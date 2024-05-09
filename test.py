import sys
from PySide2.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide2.QtGui import QPixmap
from PySide2.QtCore import Qt
import requests

class ImageWindow(QWidget):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.setWindowTitle("Image Viewer")
        self.setLayout(QVBoxLayout())
        self.image_label = QLabel()
        self.layout().addWidget(self.image_label)
        self.load_image()

    def load_image(self):
        try:
            response = requests.get(self.url)
            image = QPixmap()
            image.loadFromData(response.content)
            self.image_label.setPixmap(image)
        except Exception as e:
            print("Error loading image:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    url = "https://www.google.com/logos/doodles/2024/us-teacher-appreciation-week-2024-begins-6753651837110457.2-l.webp"
    image_window = ImageWindow(url)
    image_window.show()
    sys.exit(app.exec_())
