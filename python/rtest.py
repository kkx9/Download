import paramiko

hostname = '202.114.7.81'
username = 'yuehang'
password = 'yuehang'
#发送paramiko日志到syslogin.log文件
# paramiko.util.log_to_file('syslogin.log')

#创建一个SSH客户端client对象
ssh = paramiko.SSHClient()
#获取客户端host_keys,默认~/.ssh/known_hosts,非默认路径需指定ssh.load_system_host_keys(/xxx/xxx)
ssh.load_system_host_keys()
ssh.connect(hostname=hostname, username=username, password=password)    #创建SSH连接
stdin, stdout, stderr = ssh.exec_command('df -h')      #调用远程执行命令方法exec_command()
 #打印命令执行结果，得到Python列表形式，可以使用stdout_readlines()
print(stdout.read().decode('utf-8'))
ssh.close()
