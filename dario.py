import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QListView, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QLabel, QCheckBox, QPushButton
from PyQt5.QtGui import QColor, QTextCursor, QFont
from PyQt5.QtCore import Qt
import PyQt5.uic as uic

import logging as lg

from configparser import ConfigParser

import os.path
from os import listdir

VERSION = '0.1'

_PROFILE_OPTIONS = {
    'machine': {
        'ip_address': ('str', None),
        'operating_mode': ('str', None),
    },
    'motor': {
        'acceleration': ('float', 'm.s-1'),
        'deceleration': ('float', 'm.s-1'),
        'control_mode': ('int', None),

        'entq_kp': ('float', None),

        'entq_kp_vel': ('float', None),
        'entq_ki': ('float', None),
        'entq_kd': ('float', None),
        'torque_rise_time': ('float', 'ms'),
        'torque_fall_time': ('float', 'ms'),

        'application_coefficient': ('float', None),
        'application_velocity_unit': ('str', None),
        'application_position_unit': ('str', None),

        'invert': ('bool', None),

        'acceleration_time_mode': ('bool', None),

        'custom_max_velocity': ('float', None),

        'custom_max_acceleration': ('float', None),
        'custom_max_deceleration': ('float', None),
        'custom_max_position': ('float', None),
        'custom_min_position': ('float', None),
    }
}


class Dario(QMainWindow):
    UI_FILE = 'dario.ui'
    OPTIONS_FILE = 'dario_config.ini'

    def __init__(self):
        super().__init__()

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle('Dario')

        _path = os.path.dirname(os.path.realpath(__file__))

        self.options_file = os.path.join(_path, self.OPTIONS_FILE)
        self.main = uic.loadUi(os.path.join(_path, self.UI_FILE))
        self.profiles = os.listdir(os.path.join(_path, 'profiles'))

        self.setCentralWidget(self.main)

        self.create_menubar()

        self.load_options()

        self.profile_view = self.main.findChild(QListView, 'profile_list' )
        self.profile_paramaters_table = self.main.findChild(QTableWidget, 'profile_parameters')
        self.get_profile_list()
        self.create_profile_parameters_table()
        self.load_profile()

        self.log_list = self.main.findChild(QTextEdit,'log_list')
        self.cmd_line = self.main.findChild(QLineEdit, 'cmd_line')
        self.embedded_log_handler = EmbeddedLogHandler(self.log_list)
        self.embedded_log_handler.setFormatter(embedded_formatter)
        logging.addHandler(self.embedded_log_handler)
        self.embedded_log_handler.setLevel(lg.DEBUG)
        logging.setLevel(lg.DEBUG)

        self.show()

        self.cmd_line.returnPressed.connect(self._cmd_send)


    def create_menubar(self):
        file_menu = self.menuBar().addMenu('File')

        quit_action = file_menu.addAction('Quit')
        quit_action.triggered.connect(self.quit_app)


        file_menu = self.menuBar().addMenu('Tools')

        about_action = self.menuBar().addAction('About')
        about_action.triggered.connect(self.show_about_window)

    def get_profile_list(self):
        for profile in self.profiles :
            self.profile_view.addItem(profile)
            if profile == self.default_profile :
                profile_matches = self.profile_view.findItems(profile, Qt.MatchExactly)
                if len(profile_matches) == 1:
                    self.current_profile = profile_matches[0]
                self.profile_view.setCurrentItem(self.current_profile)
                self.current_profile.setFont(QFont('MS Shell Dlg 2', 8, QFont.Bold))

    def load_profile(self):
        self.profile_loaded = ConfigParser()
        _path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'profile', self._defaultProfile)
        self.profile_loaded.read(_path)

    def create_profile_parameters_table(self):
        _OPTION = ConfigParser()
        _OPTION.read_dict(_PROFILE_OPTIONS)

        self.profile_paramaters_table.setColumnCount(2)
        self.profile_paramaters_table.setHorizontalHeaderLabels(('Values', ''))

        for section in _PROFILE_OPTIONS.values():
            for option, value in section.items():
                value_type, value_unit = value
                row = self.profile_paramaters_table.rowCount()

                self.profile_paramaters_table.insertRow(row)
                self.profile_paramaters_table.setVerticalHeaderItem(row, QTableWidgetItem(option))

                widget = None
                if value_type == 'float':
                    widget = QDoubleSpinBox()
                elif value_type == 'int':
                    widget = QSpinBox()
                elif value_type == 'string':
                    widget = QLineEdit()
                elif value_type == 'bool':
                    widget = QCheckBox()

                self.profile_paramaters_table.setCellWidget(row, 0, widget)
                if value_unit and value_type in ('float', 'int', 'string'):
                    widget.setSuffix(' ' + value_unit)

                unset_button = QPushButton(widget)
                unset_button.setText('Unset')
                self.profile_paramaters_table.setCellWidget(row, 1, unset_button)

    def quit_app(self):
        # Options save method may be called here
        QApplication.quit()

    def show_about_window(self):
        about = QMessageBox.information(self, 'About',
                '''Dario - Version: v''' + str(VERSION),
                QMessageBox.Ok)

    def _cmd_send(self):
        self.cmd_line.clear()

    def load_options(self):
        with open(self.options_file, 'r') as f:
            cfg = {}
            for l in f.readlines():
                try :
                    k, v = l.split(' = ')
                    cfg[k] = v
                except Exception:
                    pass
        self.setCurrentOptions(cfg)

    def setCurrentOptions(self, cfg):
        opts = ('defaultProfile')
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
