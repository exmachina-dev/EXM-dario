import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt5.QtWidgets import QTextEdit, QLineEdit
from PyQt5.QtGui import QColor, QTextCursor

import PyQt5.uic as uic

import logging as lg

import os.path

VERSION = '0.1'

class Dario(QMainWindow):
    UIFILE = '.\dario.ui'
    OPTIONSFILE = '.\dario_config.ini'

    def __init__(self):
        super().__init__()

        self.initUi()

    def initUi(self):
        self.setWindowTitle('Dario')

        _path = os.path.dirname(os.path.realpath(__file__))

        self.OPTIONSFILE = _path + self.OPTIONSFILE
        self.main = uic.loadUi(_path + self.UIFILE)

        self.setCentralWidget(self.main)

        self._menuBar()

        self.doOptionLoad()
        print(self._defaultProfil)

        self.log_list = self.main.findChild(QTextEdit,'log_list')
        self.cmd_line = self.main.findChild(QLineEdit, 'cmd_line')
        self.embedded_log_handler = EmbeddedLogHandler(self.log_list)
        self.embedded_log_handler.setFormatter(embedded_formatter)
        logging.addHandler(self.embedded_log_handler)
        self.embedded_log_handler.setLevel(lg.DEBUG)
        logging.setLevel(lg.DEBUG)

        self.show()

        self.cmd_line.returnPressed.connect(self._cmd_send)


    def _menuBar(self):
        fileMenu = self.menuBar().addMenu('File')

        quitAction = fileMenu.addAction('Quit')
        quitAction.triggered.connect(self.doQuit)


        fileMenu = self.menuBar().addMenu('Tools')

        aboutAction = self.menuBar().addAction('About')
        aboutAction.triggered.connect(self.doAbout)

    def doQuit (self):
        # Options save method may be called here
        QApplication.quit()

    def doAbout(self):
        about = QMessageBox.information(self, 'About',
                '''Dario - Version: v''' + str(VERSION),
                QMessageBox.Ok)

    def _cmd_send(self):
        self.cmd_line.clear()

    def doOptionLoad(self):
        with open(self.OPTIONSFILE, 'r') as f:
            cfg = {}
            for l in f.readlines():
                try :
                    k, v = l.split(' = ')
                    cfg[k] = v
                except Exception:
                    pass
        self.setCurrentOptions(cfg)

    def setCurrentOptions(self, cfg):
        opts = ('defaultProfil')
        for k, v in cfg.items():
            if k in opts:
                setattr(self, '_' + k, v)

class EmbeddedLogHandler(lg.Handler):

    def __init__(self, widget):
        self.setLevel(lg.DEBUG)

        self.widget = widget

        self.color = {
                "INFO": QColor(127, 254, 127),
                "DEBUG": QColor(254, 254, 254),
                "WARNING": QColor(254, 254, 127),
                "ERROR": QColor(254, 127,127),
                "CRITICAL": QColor(254, 0, 0),
                }
        super().__init__()

    def emit(self, record):
        msg = '<pre style="color: {}; display: inline-block;">{}</pre><br>'.format(
                self.color[record.levelname].name(), self.format(record))

        self.widget.moveCursor(QTextCursor.End)
        self.widget.insertHtml(msg)


console_logger = lg.StreamHandler()
console_formatter = lg.Formatter(
        '%(asctime)s %(name)-36s %(levelname)-8s %(message)s',
        datefmt='%Y%m%d %H:%M:%S')

embedded_formatter = lg.Formatter(
        '%(asctime)s %(name)-10s %(levelname)-8s %(message)s',
        datefmt='%H:%M:%S')

logging = lg.getLogger('dario-gui')
logging.addHandler(console_logger)
console_logger.setFormatter(console_formatter)

logging.setLevel(lg.DEBUG)

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

