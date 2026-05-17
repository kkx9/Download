# Kubelet 停止上报心跳后发生了什么

当一个节点的 Kubelet 因为宕机、网络中断或进程崩溃而停止上报心跳，Kubernetes 会经历一条完整的故障检测与自愈链路。本文按时间顺序逐阶段拆解这一过程。

---

## 第一阶段：心跳机制与超时检测（0 ~ 40s）

Kubelet 正常运行时，会持续更新 `kube-node-lease` 命名空间下与节点同名的 `Lease` 对象的 `RenewTime` 字段，作为心跳信号。

`NodeLifecycleController` 每隔 `nodeMonitorPeriod`（默认 5s）执行一次 `monitorNodeHealth`，读取每个节点的 Lease：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:956
observedLease, _ := nc.leaseLister.Leases(v1.NamespaceNodeLease).Get(node.Name)
if observedLease != nil && (savedLease == nil ||
    savedLease.Spec.RenewTime.Before(observedLease.Spec.RenewTime)) {
    nodeHealth.lease = observedLease
    nodeHealth.probeTimestamp = nc.now()  // Lease 有更新，刷新探测时间戳
}
```

只要 Kubelet 停止续约，`probeTimestamp` 就不再更新。当超过 `nodeMonitorGracePeriod`（默认 **40s**）后，触发故障判定：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:962
if nc.now().After(nodeHealth.probeTimestamp.Add(gracePeriod)) {
    // 进入故障处理逻辑
}
```

---

## 第二阶段：节点状态标记为 Unknown

超时确认后，控制器将节点的 `Ready`、`MemoryPressure`、`DiskPressure`、`PIDPressure` 等所有关键条件全部置为 `Unknown`：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:1020
if currentCondition.Status != v1.ConditionUnknown {
    currentCondition.Status  = v1.ConditionUnknown
    currentCondition.Reason  = "NodeStatusUnknown"
    currentCondition.Message = "Kubelet stopped posting node status."
    currentCondition.LastTransitionTime = nowTimestamp
}
```

随后通过 `UpdateStatus` 将变更写入 API Server，使整个集群感知到该节点已不可信：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:1032
if _, err := nc.kubeClient.CoreV1().Nodes().UpdateStatus(ctx, node, metav1.UpdateOptions{}); err != nil {
    ...
}
```

---

## 第三阶段：为节点打上 NoExecute 污点

节点状态更新后，`processTaintBaseEviction` 立即根据 `Ready` 条件的新值决定打哪种污点：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:810
case v1.ConditionUnknown:
    // 若节点已有 not-ready 污点，立即换成 unreachable
    if taintutils.TaintExists(node.Spec.Taints, NotReadyTaintTemplate) {
        taintToAdd := *UnreachableTaintTemplate
        controllerutil.SwapNodeControllerTaint(ctx, nc.kubeClient,
            []*v1.Taint{&taintToAdd}, []*v1.Taint{NotReadyTaintTemplate}, node)
    } else if nc.markNodeForTainting(node, v1.ConditionUnknown) {
        // 加入待打污点队列
    }
```

最终节点会被打上 `node.kubernetes.io/unreachable:NoExecute` 污点。`NoExecute` 效果意味着：**不能容忍该污点的 Pod 必须被驱逐**。

---

## 第四阶段：TaintEvictionController 调度 Pod 驱逐

`TaintEvictionController` 监听节点污点变化，对节点上每个 Pod 计算其容忍能力：

```go
// pkg/controller/tainteviction/taint_eviction.go:463
allTolerated, usedTolerations := v1helper.GetMatchingTolerations(logger, taints, tolerations)
if !allTolerated {
    // Pod 完全无法容忍，立即加入驱逐队列（triggerTime = now）
    tc.taintEvictionQueue.AddWork(ctx, NewWorkArgs(...), now, now)
    return
}
minTolerationTime := getMinTolerationTime(usedTolerations)
// 有容忍时间（默认 300s），延迟驱逐
triggerTime := startTime.Add(minTolerationTime)
tc.taintEvictionQueue.AddWork(ctx, NewWorkArgs(...), startTime, triggerTime)
```

> **关键设计**：延迟驱逐给了 Kubelet 一个恢复窗口。若节点在 300s 内恢复，污点被移除，驱逐任务会被取消，Pod 不受影响。

---

## 第五阶段：执行删除，Pod 命运分叉

计时器到期后，`deletePodHandler` 被触发：

```go
// pkg/controller/tainteviction/taint_eviction.go:129
func addConditionAndDeletePod(ctx context.Context, c clientset.Interface, name, ns string) error {
    pod, _ := c.CoreV1().Pods(ns).Get(ctx, name, metav1.GetOptions{})
    // 1. 先打上 DisruptionTarget 条件，供监控审计
    apipod.UpdatePodCondition(newStatus, &v1.PodCondition{
        Type:    v1.DisruptionTarget,
        Status:  v1.ConditionTrue,
        Reason:  "DeletionByTaintManager",
        Message: "Taint manager: deleting due to NoExecute taint",
    })
    utilpod.PatchPodStatus(...)
    // 2. 执行物理删除
    return c.CoreV1().Pods(ns).Delete(ctx, name, metav1.DeleteOptions{})
}
```

Pod 被删除后，命运取决于其是否有上层控制器：

| Pod 类型 | 删除后结果 |
|---|---|
| **Deployment / ReplicaSet 管理的 Pod** | 控制器感知副本数不足，在健康节点上重建新 Pod |
| **裸 Pod（无控制器）** | API 对象永久消失，不会在任何节点重建 |
| **静态 Pod（Static Pod）** | Kubelet 恢复后读取本地 Manifest，重建 Mirror Pod，自动恢复 |

---

## 第六阶段：集群级保护——防止误驱逐

如果大量节点同时失联（如控制面网络分区），盲目驱逐会造成雪崩。`handleDisruption` 通过区域健康度来动态调节驱逐速率：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:1344
switch {
case readyNodes == 0 && notReadyNodes > 0:
    return notReadyNodes, stateFullDisruption   // 全区域失效
case notReadyNodes > 2 &&
    float32(notReadyNodes)/float32(notReadyNodes+readyNodes) >= nc.unhealthyZoneThreshold:
    return notReadyNodes, statePartialDisruption // 超过 33% 节点失效
default:
    return notReadyNodes, stateNormal
}
```

当**所有区域全部进入 FullDisruption** 时，系统判断这是控制面自身的网络问题，会立即停止一切驱逐并移除所有污点：

```go
// pkg/controller/nodelifecycle/node_lifecycle_controller.go:1090
if allAreFullyDisrupted {
    logger.Info("Controller detected that all Nodes are not-Ready. Entering master disruption mode")
    for i := range nodes {
        nc.markNodeAsReachable(ctx, nodes[i]) // 移除所有污点
    }
    for k := range nc.zoneStates {
        nc.zoneNoExecuteTainter[k].SwapLimiter(0) // 驱逐速率归零
    }
}
```

---

## 完整时间线

```
T+0s    Kubelet 停止续约 Lease
T+5s    NodeLifecycleController 第一次检测到 Lease 未更新
T+40s   超过 nodeMonitorGracePeriod，节点标记为 Ready=Unknown
T+40s   节点被打上 node.kubernetes.io/unreachable:NoExecute 污点
T+40s   TaintEvictionController 为节点上所有 Pod 计算驱逐时间
T+340s  默认 tolerationSeconds(300s) 到期，Pod 被删除
T+340s  有控制器的 Pod 在健康节点重建；裸 Pod 永久消失
```

### Citations

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L810-819)
```go
	case v1.ConditionUnknown:
		// We want to update the taint straight away if Node is already tainted with the NotReadyTaintTemplate
		if taintutils.TaintExists(node.Spec.Taints, NotReadyTaintTemplate) {
			taintToAdd := *UnreachableTaintTemplate
			if !controllerutil.SwapNodeControllerTaint(ctx, nc.kubeClient, []*v1.Taint{&taintToAdd}, []*v1.Taint{NotReadyTaintTemplate}, node) {
				logger.Error(nil, "Failed to instantly swap NotReadyTaint to UnreachableTaint. Will try again in the next cycle")
			}
		} else if nc.markNodeForTainting(node, v1.ConditionUnknown) {
			logger.V(2).Info("Node is unresponsive. Adding it to the Taint queue", "node", klog.KObj(node), "timeStamp", decisionTimestamp)
		}
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L956-960)
```go
	observedLease, _ := nc.leaseLister.Leases(v1.NamespaceNodeLease).Get(node.Name)
	if observedLease != nil && (savedLease == nil || savedLease.Spec.RenewTime.Before(observedLease.Spec.RenewTime)) {
		nodeHealth.lease = observedLease
		nodeHealth.probeTimestamp = nc.now()
	}
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L962-962)
```go
	if nc.now().After(nodeHealth.probeTimestamp.Add(gracePeriod)) {
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L1020-1025)
```go
				if currentCondition.Status != v1.ConditionUnknown {
					currentCondition.Status = v1.ConditionUnknown
					currentCondition.Reason = "NodeStatusUnknown"
					currentCondition.Message = "Kubelet stopped posting node status."
					currentCondition.LastTransitionTime = nowTimestamp
				}
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L1032-1035)
```go
			if _, err := nc.kubeClient.CoreV1().Nodes().UpdateStatus(ctx, node, metav1.UpdateOptions{}); err != nil {
				logger.Error(err, "Error updating node", "node", klog.KObj(node))
				return gracePeriod, observedReadyCondition, currentReadyCondition, err
			}
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L1090-1104)
```go
		if allAreFullyDisrupted {
			logger.Info("Controller detected that all Nodes are not-Ready. Entering master disruption mode")
			for i := range nodes {
				_, err := nc.markNodeAsReachable(ctx, nodes[i])
				if err != nil {
					logger.Error(nil, "Failed to remove taints from Node", "node", klog.KObj(nodes[i]))
				}
			}
			// We stop all evictions.
			for k := range nc.zoneStates {
				nc.zoneNoExecuteTainter[k].SwapLimiter(0)
			}
			for k := range nc.zoneStates {
				nc.zoneStates[k] = stateFullDisruption
			}
```

**File:** pkg/controller/nodelifecycle/node_lifecycle_controller.go (L1344-1351)
```go
	switch {
	case readyNodes == 0 && notReadyNodes > 0:
		return notReadyNodes, stateFullDisruption
	case notReadyNodes > 2 && float32(notReadyNodes)/float32(notReadyNodes+readyNodes) >= nc.unhealthyZoneThreshold:
		return notReadyNodes, statePartialDisruption
	default:
		return notReadyNodes, stateNormal
	}
```

**File:** pkg/controller/tainteviction/taint_eviction.go (L129-147)
```go
func addConditionAndDeletePod(ctx context.Context, c clientset.Interface, name, ns string) (err error) {
	pod, err := c.CoreV1().Pods(ns).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return err
	}
	newStatus := pod.Status.DeepCopy()
	updated := apipod.UpdatePodCondition(newStatus, &v1.PodCondition{
		Type:               v1.DisruptionTarget,
		ObservedGeneration: apipod.CalculatePodConditionObservedGeneration(&pod.Status, pod.Generation, v1.DisruptionTarget),
		Status:             v1.ConditionTrue,
		Reason:             "DeletionByTaintManager",
		Message:            "Taint manager: deleting due to NoExecute taint",
	})
	if updated {
		if _, _, _, err := utilpod.PatchPodStatus(ctx, c, pod.Namespace, pod.Name, pod.UID, pod.Status, *newStatus); err != nil {
			return err
		}
	}
	return c.CoreV1().Pods(ns).Delete(ctx, name, metav1.DeleteOptions{})
```

**File:** pkg/controller/tainteviction/taint_eviction.go (L463-489)
```go
	allTolerated, usedTolerations := v1helper.GetMatchingTolerations(logger, taints, tolerations)
	if !allTolerated {
		logger.V(2).Info("Not all taints are tolerated after update for pod on node", "pod", podNamespacedName.String(), "node", klog.KRef("", nodeName))
		// We're canceling scheduled work (if any), as we're going to delete the Pod right away.
		tc.cancelWorkWithEvent(logger, podNamespacedName)
		tc.taintEvictionQueue.AddWork(ctx, NewWorkArgs(podNamespacedName.Name, podNamespacedName.Namespace), now, now)
		return
	}
	minTolerationTime := getMinTolerationTime(usedTolerations)
	// getMinTolerationTime returns negative value to denote infinite toleration.
	if minTolerationTime < 0 {
		logger.V(4).Info("Current tolerations for pod tolerate forever, cancelling any scheduled deletion", "pod", podNamespacedName.String())
		tc.cancelWorkWithEvent(logger, podNamespacedName)
		return
	}

	startTime := now
	triggerTime := startTime.Add(minTolerationTime)
	scheduledEviction := tc.taintEvictionQueue.GetWorkerUnsafe(podNamespacedName.String())
	if scheduledEviction != nil {
		startTime = scheduledEviction.CreatedAt
		if startTime.Add(minTolerationTime).Before(triggerTime) {
			return
		}
		tc.cancelWorkWithEvent(logger, podNamespacedName)
	}
	tc.taintEvictionQueue.AddWork(ctx, NewWorkArgs(podNamespacedName.Name, podNamespacedName.Namespace), startTime, triggerTime)
```
