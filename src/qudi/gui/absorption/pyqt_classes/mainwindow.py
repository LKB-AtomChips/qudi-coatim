# -*- coding: utf-8 -*-

__all__ = ['Absorption_pyqtMainWindow']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage
from qudi.gui.absorption.pyqt_classes import displaypanel, acquisitionpanel, atomnumberpanel, camerasettingspanel

class AbsorptionMainWindow(QtWidgets.QMainWindow):
    """ This is the generic QMainWindow subclass to be used with the qudi absorption_gui.py module.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Construct a simple GUI window with some widgets to tinker with
        self.setWindowTitle('AbsorptionGUI window')
        
        # Initialize widgets
        self.display_panel = displaypanel.DisplayPanel()
        self.atom_number_panel = atomnumberpanel.AtomNumberPanel()
        
        self.reset_button = QtWidgets.QPushButton('Reset')
        self.reset_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        self.add_ten_button = QtWidgets.QPushButton('+10')
        self.sub_ten_button = QtWidgets.QPushButton('-10')
        self.count_spinbox = QtWidgets.QSpinBox()
        self.count_spinbox.setReadOnly(True)
        self.count_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.count_spinbox.setAlignment(QtCore.Qt.AlignHCenter)
        self.count_spinbox.setRange(-2**31, 2**31-1)
        self.count_spinbox.setValue(0)
        self.label = QtWidgets.QLabel('Useless counter TER...')
        font = QtGui.QFont()
        font.setBold(True)
        self.label.setFont(font)
        # arrange widgets in layout
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.display_panel, 0, 0)
        layout.addWidget(self.atom_number_panel, 1, 0)
        layout.addWidget(self.label, 1, 0)
        layout.addWidget(self.sub_ten_button, 1, 1)
        layout.addWidget(self.count_spinbox, 2, 0)
        layout.addWidget(self.add_ten_button, 2, 1)
        layout.setColumnStretch(0, 4)
        layout.setRowStretch(0, 4)
        
        # Create dummy widget as main widget and set layout
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Opening as large as possible
        self.showMaximized() 