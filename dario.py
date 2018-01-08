import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QMdiSubWindow, QWidget
from PyQt5.QtWidgets import QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsObject
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer

import PyQt5.uic as uic

import time
import os.path

VERSION = '0.1'

class Dario(QMainWindow):
    UIFILE = '.\dario.ui'

    def __init__(self):
        super().__init__()

        self.initUi()

    def initUi(self):
        self.setWindowTitle('Dario')

        _path = os.path.dirname(os.path.realpath(__file__))
        self.main = uic.loadUi(_path + self.UIFILE)

        self.setCentralWidget(self.main)

        fileMenu = self.menuBar().addMenu('File')

        quitAction = fileMenu.addAction('Quit')
        quitAction.triggered.connect(self.doQuit)

        fileMenu = self.menuBar().addMenu('Tools')

        aboutAction = self.menuBar().addAction('About')
        aboutAction.triggered.connect(self.doAbout)

        self.show()

    def doQuit (self):
        # Options save method may be called here
        QApplication.quit()

    def doAbout(self):
        about = QMessageBox.information(self, 'About',
        '''Dario - Version: v''' + str(VERSION),
        QMessageBox.Ok)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(base_path)
    fstyle = os.path.join(base_path, './style.qss')
    with open(fstyle, 'r') as f:
        style = f.readlines()
    app.setStyleSheet(' '.join(style))

    w = Dario()

    sys.exit(app.exec_())

