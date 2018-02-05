import sys
from functools import partial

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget
from PyQt5.QtWidgets import QTextEdit, QLineEdit, QListView, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox, QLabel, QCheckBox, QPushButton
from PyQt5.QtGui import QColor, QTextCursor, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QTimer

import PyQt5.uic as uic

from pythonosc import dispatcher, osc_server, udp_client, osc_message_builder
import logging as lg

from configparser import ConfigParser

import threading

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

    device_list_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        _path = os.path.dirname(os.path.realpath(__file__))

        self.options_file = os.path.join(_path, self.OPTIONS_FILE)
        self.profiles_path = os.path.join(_path, 'profiles')
        self.ui_file = os.path.join(_path, self.UI_FILE)

        self.load_options()

        self.osc_dispatcher = dispatcher.Dispatcher()
        self.osc_dispatcher.map("/*",print)
        self.osc_dispatcher.map("/config/profile/list/reply", self.create_profiles_list)
        self.osc_dispatcher.map("/config/profile/list/ok", self.profiles_list_view)

        self.osc_dispatcher.map("/config/profile/list_options/reply",self.create_profile_options)
        broadcast_ip = self.options.get('osc', 'broadcast_ip',
                                        fallback='10.255.255.255')
        reply_port = int(self.options.get('osc', 'reply_port', fallback='6969'))
        self.osc_clients = dict()
        self.osc_clients['broadcast'] = udp_client.SimpleUDPClient(
                broadcast_ip, reply_port)

        logging.info('Sending on {}:{}'.format(broadcast_ip,reply_port))

        self.device_list = dict()


        ip = self.options.get('osc', 'ip', fallback='')
        port = int(self.options.get('osc', 'port', fallback=6969))

        self.osc_server = osc_server.ThreadingOSCUDPServer((ip, port), self.osc_dispatcher)

        logging.info('Listening on {}'.format(self.osc_server.server_address))
        self.server_thread =threading.Thread(target = self.osc_server.serve_forever)
        self.server_thread.start()

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle('Dario')

        self.main = uic.loadUi(self.ui_file)
        self.setCentralWidget(self.main)

        self.create_menubar()

        self.profile_view = self.main.findChild(QListView, 'profile_list' )
        self.profile_paramaters_table = self.main.findChild(QTableWidget, 'profile_parameters')

        self.log_list = self.main.findChild(QTextEdit,'log_list')
        self.cmd_line = self.main.findChild(QLineEdit, 'cmd_line')
        self.embedded_log_handler = EmbeddedLogHandler(self.log_list)
        self.embedded_log_handler.setFormatter(embedded_formatter)
        logging.addHandler(self.embedded_log_handler)
        self.embedded_log_handler.setLevel(lg.DEBUG)
        logging.setLevel(lg.DEBUG)

        self.device_table = self.main.findChild(QTableWidget, 'deviceTable')
        self.device_table.setColumnCount(3)
        self.device_table.setHorizontalHeaderLabels(('IP', 'S/N', ''))

        # Connect signals and slots
        scan_button = self.main.findChild(QPushButton, 'scanButton')
        scan_button.clicked.connect(self.scan_devices)

        self.device_list_changed.connect(self.update_device_table)

        self.osc_dispatcher.map('/announce', self.add_to_device_list)

        self.profiles_list = []
        self.get_profile_list()
        self.get_profile_loaded()
        self.get_profile_option()
        self.load_profile()

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
        self.osc_clients['broadcast'].send_message("/config/profile/list", ())

    def get_profile_loaded(self):
        self.osc_clients['broadcast'].send_message("/config/get", ('machine:profile'))

    def get_profile_option(self):
        self.osc_clients['broadcast'].send_message("/config/profile/list_options", ())

    def create_profiles_list(self, args, value):
        self.profiles_list.append(value)

    def profiles_list_view(self, args, value):
        for profile in self.profiles_list:
            self.profile_view.addItem(profile)

        '''
        files = os.listdir(self.profiles_path)
        def is_conf(path):
            return str(path).endswith('.conf')
        self.profiles = [p[:-5] for p in filter(is_conf, files)]

        for profile in self.profiles :
            self.profile_view.addItem(profile)
            if profile == self.options['configuration']['default_profile']:
                profile_matches = self.profile_view.findItems(profile, Qt.MatchExactly)
                if len(profile_matches) == 1:
                    self.current_profile = profile_matches[0]
                self.profile_view.setCurrentItem(self.current_profile)
                self.current_profile.setFont(QFont('MS Shell Dlg 2', 8, QFont.Bold))
        '''
    def load_profile(self):
        self.profile_loaded = ConfigParser()
        _file = self.options['configuration']['default_profile'] + '.conf'
        _path = os.path.join(self.profiles_path, _file)
        self.profile_loaded.read(_path)

    def create_profile_parameters_table(self):
        _OPTION = ConfigParser()
        _OPTION.read_dict(_PROFILE_OPTIONS)

        self.profile_paramaters_table.setColumnCount(2)
        self.profile_paramaters_table.setHorizontalHeaderLabels(('Values', ''))
        profile_widget_list = {}
        for section, options in _PROFILE_OPTIONS.items():
            for option, value in options.items():
                value_type, value_unit = value
                row = self.profile_paramaters_table.rowCount()
                self.profile_paramaters_table.insertRow(row)
                self.profile_paramaters_table.setVerticalHeaderItem(row, QTableWidgetItem(option))
                widget = None
                if value_type == 'float':
                    widget = QDoubleSpinBox()
                elif value_type == 'int':
                    widget = QSpinBox()
                elif value_type == 'str':
                    widget = QLineEdit()
                elif value_type == 'bool':
                    widget = QCheckBox()

                self.profile_paramaters_table.setCellWidget(row, 0, widget)


                if value_unit and value_type in ('float', 'int', 'string'):
                    widget.setSuffix(' ' + value_unit)

                profile_widget_list[section + ':' + option] = widget

                unset_button = QPushButton(widget)
                unset_button.setText('Unset')
                self.profile_paramaters_table.setCellWidget(row, 1, unset_button)

    def quit_app(self):
        # Options save method may be called here
        QApplication.quit()

    def show_about_window(self):
        about = QMessageBox.information(self, 'About',
                'Dario - Version: <b>v{}</b>'.format(VERSION),
                QMessageBox.Ok)

    def _cmd_send(self):
        self.cmd_line.clear()

    def load_options(self):
        self.options = ConfigParser()
        self.options.read(self.options_file)

    # GUI methods

    def update_device_table(self):
        self.device_table.clear()

        for sn, d in self.device_list.items():
            r = self.device_table.rowCount()
            dev_addr = '{0[ip]}/{0[mask]}:{0[port]}'.format(d)

            sn_label = QLabel(sn)
            dev_label = QLabel(dev_addr)
            connect_button = QPushButton('Connect')
            connect_button.clicked.connect(partial(self.connect_to_device, d))

            self.device_table.insertRow(r)
            self.device_table.setCellWidget(r, 0, sn_label)
            self.device_table.setCellWidget(r, 1, dev_label)
            self.device_table.setCellWidget(r, 1, connect_button)

    # Connection methods

    def add_to_device_list(addr, args):
        '''
        Add OSC device to list

        Except reply like /announce 4417ARCP0001 10.84.212.169/8:6969
        '''
        try:
            sn, net_addr = args
            cidr_ip, port = net_addr.split(':')
            ip, mask = net_addr.split('/')
        except IndexError:
            logging.error('Misformatted announce message: {}'.format(' '.join(args)))
            return

        if self.device_list.has_key(sn):
            logging.warn('Replacing {!s} by {}'.format(self.device_list[sn], cidr_port))

        dev = {
                'ip': ip,
                'port': int(port),
                'mask': int(mask),
                }
        self.device_list[sn] = dev
        osc_client = udp_client.SimpleUDPClient( ip, port)
        self.osc_client[ip] = osc_client

        self.devices_changed.emit()

    # OSC communication

    def scan_devices(self):
        self.osc_clients['broadcast'].send_message('/identify', ())
        logging.info('send : /identify')

    def connect_to_device(self, ip):
        pass

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
