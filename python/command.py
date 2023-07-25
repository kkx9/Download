from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import QProcess


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("执行命令")
        self.setGeometry(100, 100, 400, 300)

        self.button = QPushButton("执行命令", self)
        self.button.clicked.connect(self.execute_command)

    def execute_command(self):
        command = "dir"  # 替换为你要执行的命令
        process = QProcess()
        process.start(command)
        process.waitForFinished()

        print(123)
        output = process.readAllStandardOutput().data().decode()
        print(output)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
