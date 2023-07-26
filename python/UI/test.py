import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QPlainTextEdit
import subprocess


class ShellCommandApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.output_textedit = None
        self.execute_button = None
        self.command_input = None
        self.command_label = None
        self.setWindowTitle('Shell Command Execution')
        self.setGeometry(100, 100, 600, 400)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.command_label = QLabel("Enter shell command:")
        self.command_input = QLineEdit()
        self.execute_button = QPushButton("Execute Command")
        self.output_textedit = QPlainTextEdit()

        layout.addWidget(self.command_label)
        layout.addWidget(self.command_input)
        layout.addWidget(self.execute_button)
        layout.addWidget(self.output_textedit)

        self.setLayout(layout)

        self.execute_button.clicked.connect(self.execute_command)

    def execute_command(self):
        command = self.command_input.text()
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, universal_newlines=True)

            for line in process.stdout:
                self.output_textedit.appendPlainText(line.strip())
                QtWidgets.QApplication.processEvents()  # 实时刷新界面，保持交互性

            process.wait()
        except subprocess.CalledProcessError as e:
            self.output_textedit.appendPlainText(f"Error executing command: {e}")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    shell_command_app = ShellCommandApp()
    shell_command_app.show()
    sys.exit(app.exec_())
