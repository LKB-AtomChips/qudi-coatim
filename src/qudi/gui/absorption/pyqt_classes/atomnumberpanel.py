# -*- coding: utf-8 -*-

__all__ = ['Absorption_pyqtAcquisitionPanel']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage

class AtomNumberPanel(QtWidgets.QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.setTitle("Atom Number")
        self.setCheckable(True)