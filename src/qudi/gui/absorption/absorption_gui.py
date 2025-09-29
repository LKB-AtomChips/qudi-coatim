# -*- coding: utf-8 -*-

__all__ = ['AbsorptionMainWindow']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage
from qudi.gui.absorption import mainwindow
        
class AbsorptionGui(GuiBase):
    """ Main gui class for absorption imaging.
    Example config for copy-paste: (TO BE MODIFIED)

    camera_gui:
        module.Class: 'camera.cameragui.CameraGui'
        connect:
            absorption_logic:
            camera_logic:
    """

    _camera_logic = Connector(name='camera_logic', interface='GuppyLogic')
    _absorption_logic = Connector(name='absorption_logic', interface='AbsorptionLogic')

    sigStartStopVideoToggled = QtCore.Signal(bool)
    sigCaptureFrameTriggered = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mw = None
        self._settings_dialog = None

    def on_activate(self):
        """ Initializes all needed UI files and establishes the connectors.
        """
        logic = self._absorption_logic()

        # Create main window
        self._mw = mainwindow.AbsorptionMainWindow()
        # Create settings dialog
        self._settings_dialog = CameraSettingsDialog(self._mw)
        # Connect the action of the settings dialog with this module
        self._settings_dialog.accepted.connect(self._update_settings)
        self._settings_dialog.rejected.connect(self._keep_former_settings)
        self._settings_dialog.button_box.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(
            self._update_settings
        )

        # Fill in data from logic
        logic_busy = logic.module_state() == 'locked'
        # self._mw.action_start_video.setChecked(logic_busy)
        # self._mw.action_capture_frame.setChecked(logic_busy)
        # self._update_frame(logic.last_frame)
        self._keep_former_settings()

        # # connect main window actions
        # self._mw.action_start_video.triggered[bool].connect(self._start_video_clicked)
        # self._mw.action_capture_frame.triggered.connect(self._capture_frame_clicked)
        # self._mw.action_show_settings.triggered.connect(lambda: self._settings_dialog.exec_())
        # self._mw.action_save_frame.triggered.connect(self._save_frame)
        # connect update signals from logic
        # logic.sigFrameChanged.connect(self._update_frame)
        # logic.sigAcquisitionFinished.connect(self._acquisition_finished)
        # connect GUI signals to logic slots
        # self.sigStartStopVideoToggled.connect(logic.toggle_video)
        # self.sigCaptureFrameTriggered.connect(logic.capture_frame)
        self.show()

    def on_deactivate(self):
        """ De-initialisation performed during deactivation of the module.
        """
        logic = self._absorption_logic()
        # disconnect all signals
        self.sigCaptureFrameTriggered.disconnect()
        self.sigStartStopVideoToggled.disconnect()
        # logic.sigAcquisitionFinished.disconnect(self._acquisition_finished)
        # logic.sigFrameChanged.disconnect(self._update_frame)
        # self._mw.action_save_frame.triggered.disconnect()
        # self._mw.action_show_settings.triggered.disconnect()
        # self._mw.action_capture_frame.triggered.disconnect()
        # self._mw.action_start_video.triggered.disconnect()
        self._mw.close()

    def show(self):
        """Make window visible and put it above all other windows.
        """
        self._mw.show()
        self._mw.raise_()
        self._mw.activateWindow()

    def _update_settings(self):
        """ Write new settings from the gui to the file. """
        logic = self._absorption_logic()
        # logic.set_exposure(self._settings_dialog.exposure_spinbox.value())
        # logic.set_gain(self._settings_dialog.gain_spinbox.value())

    def _keep_former_settings(self):
        """ Keep the old settings and restores them in the gui. """
        logic = self._absorption_logic()
        # self._settings_dialog.exposure_spinbox.setValue(logic.get_exposure())
        # self._settings_dialog.gain_spinbox.setValue(logic.get_gain())

    def _capture_frame_clicked(self):
        # self._mw.action_start_video.setDisabled(True)
        # self._mw.action_capture_frame.setDisabled(True)
        # self._mw.action_show_settings.setDisabled(True)
        self.sigCaptureFrameTriggered.emit()

    def _acquisition_finished(self):
        # self._mw.action_start_video.setChecked(False)
        # self._mw.action_start_video.setEnabled(True)
        # self._mw.action_capture_frame.setChecked(False)
        # self._mw.action_capture_frame.setEnabled(True)
        # self._mw.action_show_settings.setEnabled(True)
        pass

    def _start_video_clicked(self, checked):
        # if checked:
        #     self._mw.action_show_settings.setDisabled(True)
        #     self._mw.action_capture_frame.setDisabled(True)
        #     self._mw.action_start_video.setText('Stop Video')
        # else:
        #     self._mw.action_start_video.setText('Start Video')
        # self.sigStartStopVideoToggled.emit(checked)
        pass

    def _update_frame(self, frame_data):
        """
        """
        pass
        # self._mw.image_widget.set_image(frame_data)

    def _save_frame(self):
        logic = self._absorption_logic()
        ds = TextDataStorage(root_dir=self.module_default_data_dir)
        timestamp = datetime.datetime.now()
        # tag = logic.create_tag(timestamp)

        parameters = {}
        # parameters['gain'] = logic.get_gain()
        # parameters['exposure'] = logic.get_exposure()

        # data = logic.last_frame
        # if data is not None:
        #     file_path, _, _ = ds.save_data(data, metadata=parameters, nametag=tag,
        #                                timestamp=timestamp, column_headers='Image (columns is X, rows is Y)')
        #     figure = logic.draw_2d_image(data, cbar_range=None)
        #     ds.save_thumbnail(figure, file_path=file_path.rsplit('.', 1)[0])
        # else:
        #     self.log.error('No Data acquired. Nothing to save.')
        # return
