import sys
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import paramiko


def connect_remote():
    remote_command_app = RemoteCommandApp()
    remote_command_app.show()


class RemoteConnectionApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('远程连接界面')
        self.setGeometry(100, 100, 400, 200)

        self.remote_host = None

        self.remote_button = QtWidgets.QToolButton(self)
        self.remote_button.clicked.connect(connect_remote)
        self.remote_button.setIcon(QtGui.QIcon('button_image.png'))
        self.remote_button.setIconSize(QtCore.QSize(100, 100))
        self.remote_button.setText("connect")
        self.remote_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout = QtWidgets.QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.remote_button)
        layout.addStretch()
        self.setLayout(layout)


def entry_container():
    remote_command_app = ContainerCommandApp()
    remote_command_app.show()


class RemoteCommandApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.channel = None
        self.connect_remote()

        self.setWindowTitle('远程执行命令界面')
        self.setGeometry(100, 100, 400, 300)

        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QToolButton(self)
        button.clicked.connect(self.upgrade_to_root)
        button.setIcon(QtGui.QIcon('user_root.png'))
        button.setIconSize(QtCore.QSize(100, 100))
        button.setText('Root')
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button)

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(
            lambda _, cmd='docker run -it -p 2222:22 --privileged ubuntu:20.04': self.execute_command(cmd))
        button0.setIcon(QtGui.QIcon('Create a container.png'))
        button0.setIconSize(QtCore.QSize(200, 200))
        button0.setText('Create a container')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(entry_container)
        button1.setIcon(QtGui.QIcon('Entry container.png'))
        button1.setIconSize(QtCore.QSize(200, 200))
        button1.setText('Entry container')
        button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1)

        button2 = QtWidgets.QToolButton(self)
        button2.clicked.connect(
            lambda _, cmd='docker ps': self.execute_command(cmd))
        button2.setIcon(QtGui.QIcon('list.png'))
        button2.setIconSize(QtCore.QSize(200, 200))
        button2.setText('List')
        button2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button2)

        button3 = QtWidgets.QToolButton(self)
        button3.clicked.connect(
            lambda _, cmd='cd tmp && touch': self.execute_command(cmd))
        button3.setIcon(QtGui.QIcon('file.png'))
        button3.setIconSize(QtCore.QSize(200, 200))
        button3.setText('Create file')
        button3.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button3)

        self.setLayout(layout)

    def connect_remote(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.WarningPolicy())

            remote_host = '202.114.7.81'
            username = 'yuehang'
            password = 'yuehang'

            self.client.connect(hostname=remote_host, username=username, password=password)

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
            QtWidgets.QMessageBox.critical(self, '远程连接错误', '认证失败，请检查用户名和密码。')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '远程连接错误', f"无法连接到远程主机: {e}")

    def upgrade_to_root(self):
        while self.channel.recv_ready():
            self.channel.recv(65535).decode()

        root_password = 'yuehang'
        self.channel.send(f"su\n")
        while not self.channel.recv_ready():
            continue
        self.channel.recv(65535).decode()
        # if 'Password:' in output:
        self.channel.send(f"{root_password}\n")
        output = ""
        while not self.channel.recv_ready():
            continue
        while self.channel.recv_ready():
            output += self.channel.recv(65535).decode()
        if 'Authentication failure' in output:
            QtWidgets.QMessageBox.critical(self, '错误', '切换到root用户失败。请检查Root密码是否正确。')
            return
        else:
            QtWidgets.QMessageBox.information(self, '成功', '成功切换到root用户。')

    def execute_command(self, command):
        while self.channel.recv_ready():
            self.channel.recv(65535).decode()
        self.channel.send(f"{command}\n")
        time.sleep(3)
        output = ""
        while not self.channel.recv_ready():
            continue
        while self.channel.recv_ready():
            output += self.channel.recv(65535).decode()
        if output:
            print(f"Output from remote host: {output}")


    def closeEvent(self, event):
        if self.client is not None:
            self.client.close()
            self.client = None


class ContainerCommandApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Container')
        self.setGeometry(100, 100, 400, 300)

        layout = QtWidgets.QVBoxLayout()

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(lambda _, cmd='pwd': self.execute_command(cmd))
        button0.setIcon(QtGui.QIcon('Create a container.png'))
        button0.setIconSize(QtCore.QSize(100, 100))
        button0.setText('pwd')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0)

        # button1 = QtWidgets.QToolButton(self)
        # button1.clicked.connect(self.upgrade_to_root())
        # button1.setIcon(QtGui.QIcon('upgrade_to_root.png'))
        # button1.setIconSize(QtCore.QSize(100, 100))
        # button1.setText('upgrade to root')
        # button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        # layout.addWidget(button1)

        self.setLayout(layout)

        self.jump_client = None
        self.container = None
        self.ssh_client = None

    def connect_to_jump_host(self):
        host = '202.114.7.81'
        username = 'yuehang'
        password = 'yuehang'

        self.jump_client = paramiko.SSHClient()
        self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.jump_client.connect(host, username=username, password=password)

    def entry_container(self):
        self.connect_to_jump_host()
        try:
            if self.jump_client:
                transport = self.jump_client.get_transport()
                container_addr = ('127.0.0.1', 2222)  # 替换为目标主机的地址和端口
                local_addr = ('localhost', 0)
                self.container = transport.open_channel("direct-tcpip", container_addr, local_addr)

                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect('localhost', username='testuser', password='testuser', sock=self.container)
        except paramiko.AuthenticationException:
            QtWidgets.QMessageBox.critical(self, '远程连接错误', '认证失败，请检查用户名和密码。')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '远程连接错误', f"无法连接到远程主机: {e}")

    def upgrade_to_root(self):
        stdin, stdout, stderr = self.ssh_client.exec_command("sudo su -")
        stdin.write('root' + "\n")
        stdin.flush()
        return stdout.channel.recv_exit_status() == 0

    def execute_command(self, command, flag=False):
        self.entry_container()
        if flag:
            self.upgrade_to_root()
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode().strip()
        if output:
            print(f"Output from remote host: {output}")
        elif error:
            print(f"Error from remote host: {error}")

        self.ssh_client.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    remote_connection_app = RemoteConnectionApp()
    remote_connection_app.show()
    sys.exit(app.exec_())
