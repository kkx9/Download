# MADE builder

docker run --rm --privileged  -e DOCKER_CROSSPLATFORMS -e BUILD_APT_MIRROR -e BUILDFLAGS -e KEEPBUNDLE -e DOCKER_BUILD_ARGS -e DOCKER_BUILD_GOGC -e DOCKER_BUILD_OPTS -e DOCKER_BUILD_PKGS -e DOCKER_BUILDKIT -e DOCKER_BASH_COMPLETION_PATH -e DOCKER_CLI_PATH -e DOCKER_DEBUG -e DOCKER_EXPERIMENTAL -e DOCKER_GITCOMMIT -e DOCKER_GRAPHDRIVER -e DOCKER_LDFLAGS -e DOCKER_PORT -e DOCKER_REMAP_ROOT -e DOCKER_ROOTLESS -e DOCKER_STORAGE_OPTS -e DOCKER_TEST_HOST -e DOCKER_USERLANDPROXY -e DOCKERD_ARGS -e DELVE_PORT -e GITHUB_ACTIONS -e TEST_FORCE_VALIDATE -e TEST_INTEGRATION_DIR -e TEST_INTEGRATION_USE_SNAPSHOTTER -e TEST_SKIP_INTEGRATION -e TEST_SKIP_INTEGRATION_CLI -e TESTCOVERAGE -e TESTDEBUG -e TESTDIRS -e TESTFLAGS -e TESTFLAGS_INTEGRATION -e TESTFLAGS_INTEGRATION_CLI -e TEST_FILTER -e TIMEOUT -e VALIDATE_REPO -e VALIDATE_BRANCH -e VALIDATE_ORIGIN_BRANCH -e VERSION -e PLATFORM -e DEFAULT_PRODUCT_LICENSE -e PRODUCT -e PACKAGER_NAME -v "/home/yuehang/moby/.:/go/src/github.com/docker/docker/." -v "/home/yuehang/moby/.git:/go/src/github.com/docker/docker/.git" -v docker-dev-cache:/root/.cache -v docker-mod-cache:/go/pkg/mod/  -v /home/yuehang/tracee_test:/tracee -v /home/yuehang/test:/home/unprivilegeduser/test  -v /home/yuehang/repos/image_diff/MADE_diff/diff:/var/lib/docker/aufs/diff -t -i "docker-dev" bash


vim /etc/docker/daemon.json
{
  "features": {
    "dependency-builder": true
  }
}

hack/make.sh binary install-binary run
