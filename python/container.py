from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QFormLayout, QLabel, QLineEdit, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Docker容器创建")
        self.setGeometry(100, 100, 400, 300)

        self.container_groupbox = QGroupBox("创建容器")
        self.container_layout = QFormLayout()

        self.name_label = QLabel("容器名称:")
        self.name_edit = QLineEdit()
        self.container_layout.addRow(self.name_label, self.name_edit)

        self.image_label = QLabel("镜像名称:")
        self.image_edit = QLineEdit()
        self.container_layout.addRow(self.image_label, self.image_edit)

        self.create_button = QPushButton("创建容器")
        self.create_button.clicked.connect(self.create_container)
        self.container_layout.addRow(self.create_button)

        self.container_groupbox.setLayout(self.container_layout)

        self.setCentralWidget(self.container_groupbox)

    def create_container(self):
        container_name = self.name_edit.text()
        image_name = self.image_edit.text()

        # 在这里执行创建容器的逻辑
        print(f"创建容器：名称={container_name}，镜像={image_name}")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
