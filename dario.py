import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsObject
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer

import PyQt5.uic as uic

import time
import os.path

class TestConfig(QMainWindow):
    UIFILE = '.\dario.ui'

    def __init__(self):
        super().__init__()

        self.initUi()

    def initUi(self):
        self.setWindowTitle('Test Config Tool')

        _path = os.path.dirname(os.path.realpath(__file__))
        self.main = uic.loadUi(_path + self.UIFILE)

        self.setCentralWidget(self.main)
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = TestConfig()

    sys.exit(app.exec_())

