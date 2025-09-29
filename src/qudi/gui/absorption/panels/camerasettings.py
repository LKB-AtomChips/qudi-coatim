# -*- coding: utf-8 -*-

__all__ = ['Absorption_CameraSettingsPanel']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage

class CameraSettingsPanel(QtWidgets.QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.setTitle("Camera Settings")
        
        layout = QtWidgets.QGridLayout()
        
        exposure_time_label = QtWidgets.QLabel("Exposure time [ms]")
        self.exposure_time_doublespinbox = QtWidgets.QDoubleSpinBox()
        self.exposure_time_doublespinbox.setMinimum(0)
        self.exposure_time_doublespinbox.setMaximum(100)
        layout.addWidget(exposure_time_label, 0, 0)
        layout.addWidget(self.exposure_time_doublespinbox, 0, 1)        
        
        trigger_type_label = QtWidgets.QLabel("Trigger Type:")
        layout.addWidget(trigger_type_label, 1, 0)
        self.trigger_time_combobox = QtWidgets.QComboBox()
        self.trigger_time_combobox.addItem("InputLines")
        self.trigger_time_combobox.addItem("Software")
        layout.addWidget(self.trigger_time_combobox, 1, 1)
        
        pixel_size_label = QtWidgets.QLabel("Pixel size [µm]")
        layout.addWidget(pixel_size_label, 2, 0)
        self.pixel_size_combobox = QtWidgets.QDoubleSpinBox()
        self.pixel_size_combobox.setMinimum(0)
        self.pixel_size_combobox.setMaximum(100)
        layout.addWidget(self.pixel_size_combobox, 2, 1)
        
        gain_label = QtWidgets.QLabel("Gain [dB]")
        layout.addWidget(gain_label, 3, 0)
        self.gain_combobox = QtWidgets.QDoubleSpinBox()
        self.gain_combobox.setMinimum(0)
        self.gain_combobox.setMaximum(24)
        layout.addWidget(self.gain_combobox, 3, 1)
        
        self.ignore_timeout_checkbox = QtWidgets.QCheckBox("Ignore Timeout ?")
        layout.addWidget(self.ignore_timeout_checkbox, 4, 0)
        
        self.trigger_checkbox = QtWidgets.QCheckBox("Trigger On")
        layout.addWidget(self.trigger_checkbox, 5, 0)
        
        self.setLayout(layout)