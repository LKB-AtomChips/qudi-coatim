# -*- coding: utf-8 -*-

__all__ = ['Absorption_AcquisitionPanel']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage

class AcquisitionPanel(QtWidgets.QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        
        self.setTitle("Acquisition Panel")
        
        self.setCheckable(False)
        
        self.start_acquisition_button = QtWidgets.QPushButton("Start Acquisition")
        self.stop_acquisition_button = QtWidgets.QPushButton("Stop Acquisition")
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.start_acquisition_button)
        layout.addWidget(self.stop_acquisition_button)
        
        self.setLayout(layout)