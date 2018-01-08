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
        connexionAction = fileMenu.addAction('Connexion')
        connexionAction.triggered.connect(self.doConnexion)

        aboutAction = self.menuBar().addAction('About')
        aboutAction.triggered.connect(self.doAbout)


        self.show()

    def doQuit (self):
        QApplication.quit()

    def doAbout(self):
        about = QMessageBox.information(self, 'About',
        '''Dario - Version: v''' + str(VERSION),
        QMessageBox.Ok)

    def doConnexion(self):

    def doQuit(self):
        self.windows2 = None
        QWidget.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = Dario()

    sys.exit(app.exec_())

