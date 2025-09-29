# -*- coding: utf-8 -*-

__all__ = ['Absorption_pyqtMainWindow']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage
from qudi.gui.absorption.panels import acquisition, atomnumber, averaging, batchprocessing, camerasettings, display

class AbsorptionMainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('AbsorptionGUI Main Window')
        
        # Initialize widgets
        self.image_panel = display.DisplayPanel()
        self.atom_number_panel = atomnumber.AtomNumberPanel()
        
        self.acquisition_panel = acquisition.AcquisitionPanel()
        self.camera_settings_panel = camerasettings.CameraSettingsPanel()
        self.averaging_panel = averaging.AveragingPanel()
        self.batch_processing_panel = batchprocessing.BatchProcessingPanel()
        
        
        # Upper layout
        self.upper_widget = QtWidgets.QWidget()
        self.upper_layout = QtWidgets.QHBoxLayout()
        self.upper_layout.addWidget(self.image_panel)
        self.upper_layout.addWidget(self.atom_number_panel)
        self.upper_widget.setLayout(self.upper_layout)
        # self.upper_layout.setColumnStretch(0, 4)
        
        # Lower layout
        self.lower_widget = QtWidgets.QWidget()
        self.lower_layout = QtWidgets.QHBoxLayout()
        self.lower_layout.addWidget(self.acquisition_panel)
        self.lower_layout.addWidget(self.camera_settings_panel)
        self.lower_layout.addWidget(self.averaging_panel)
        self.lower_layout.addWidget(self.batch_processing_panel)
        self.lower_widget.setLayout(self.lower_layout)
        
        # Create dummy widget as main widget and set layout
        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.upper_widget)
        layout.addWidget(self.lower_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Opening as large as possible
        self.showMaximized() 