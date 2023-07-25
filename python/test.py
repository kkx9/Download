import sys
import paramiko
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QFileDialog


class Window2(QMainWindow):
    def __init__(self, ssh_client):
        super().__init__()
        self.setWindowTitle("Window 2")

        self.ssh_client = ssh_client

        # 创建用于显示文件的文本编辑框
        self.text_edit = QTextEdit(self)
        self.setCentralWidget(self.text_edit)

    def update_files_list(self):
        # 获取指定目录下的文件列表并显示在窗口2中的文本编辑框
        stdin, stdout, stderr = self.ssh_client.exec_command("ls /home/yuehang/tmp")
        files = stdout.read().decode().strip().split("\n")
        self.text_edit.setPlainText("\n".join(files))

    def create_new_file(self, file_name, file_content):
        # 在远程主机中创建新文件
        command = f"echo '{file_content}' > /home/yuehang/tmp/{file_name}"
        self.ssh_client.exec_command(command)
        self.update_files_list()


class Window1(QMainWindow):
    def __init__(self, ssh_client):
        super().__init__()
        self.setWindowTitle("Window 1")

        self.ssh_client = ssh_client

        # 创建显示文件按钮
        self.show_file_button = QPushButton("Show Files", self)
        self.show_file_button.clicked.connect(self.show_files_dialog)

        # 创建创建文件按钮
        self.create_file_button = QPushButton("Create File", self)
        self.create_file_button.clicked.connect(self.create_new_file)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.show_file_button)
        layout.addWidget(self.create_file_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.window2 = Window2(ssh_client)

    def show_files_dialog(self):
        # # 显示指定目录的文件对话框
        # file_dialog = QFileDialog(self)
        # file_dialog.setFileMode(QFileDialog.Directory)
        # directory = file_dialog.getExistingDirectory(self, "Select Directory")
        # if directory:
        #     # 在窗口2显示指定目录的文件
        self.window2.update_files_list()
        self.window2.show()

    def create_new_file(self):
        # 创建新文件的操作，这里假设用户输入了文件名和内容
        file_name, file_content = self.get_new_file_info()

        # 在窗口2同步更新创建的文件
        self.window2.create_new_file(file_name, file_content)

    def get_new_file_info(self):
        # 假设这里有一个对话框或输入框来获取新文件的信息
        file_name = "new_file.txt"
        file_content = "This is the content of the new file."
        return file_name, file_content

    def closeEvent(self, event):
        # 关闭窗口1时断开SSH连接
        self.ssh_client.close()


class Window0(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Window 0")

        # 创建连接到远程主机按钮
        self.connect_button = QPushButton("Connect to Remote Host", self)
        self.connect_button.clicked.connect(self.connect_to_remote_host)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.connect_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.ssh_client = None

    def connect_to_remote_host(self):
        # 使用SSH连接到远程主机
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("202.114.7.81", username="yuehang", password="yuehang")

        # 创建窗口1，并传递SSH客户端对象
        window1 = Window1(ssh)
        window1.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建窗口0
    window0 = Window0()
    window0.show()

    # 创建窗口2


    sys.exit(app.exec_())
