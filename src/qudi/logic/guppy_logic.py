# -*- coding: utf-8 -*-

"""
A module for controlling a camera.

Copyright (c) 2021, the qudi developers. See the AUTHORS.md file at the top-level directory of this
distribution and on <https://github.com/Ulm-IQO/qudi-iqo-modules/>

This file is part of qudi.

Qudi is free software: you can redistribute it and/or modify it under the terms of
the GNU Lesser General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

Qudi is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with qudi.
If not, see <https://www.gnu.org/licenses/>.
"""

import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from PySide2 import QtCore
from qudi.core.connector import Connector
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import RecursiveMutex
from qudi.core.module import LogicBase


class GuppyLogic(LogicBase):
    """ Logic class for controlling a GuppyPro camera.

    @ TO CHANGE:::
    Example config for copy-paste:

    camera_logic:
        module.Class: 'camera_logic.CameraLogic'
        connect:
            camera: camera_dummy
        options:
            minimum_exposure_time: 0.05
    """

    # declare connectors
    _camera = Connector(name='camera', interface='CameraInterface')
    # declare config options
    _minimum_exposure_time = ConfigOption(name='minimum_exposure_time',
                                          default=76e-3,
                                          missing='warn')

    # signals
    sigFrameChanged = QtCore.Signal(object)
    sigAcquisitionFinished = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__timer = None
        self._thread_lock = RecursiveMutex()
        self._exposure = -1
        self._gain = -1
        self._last_frame = None

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        camera = self._camera()
        self._exposure = camera.get_exposure()
        self._gain = camera.get_gain()

        self.__timer = QtCore.QTimer()
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__acquire_video_frame)

    def on_deactivate(self):
        """ Perform required deactivation. """
        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer = None

    @property
    def last_frame(self):
        return self._last_frame

    def set_exposure(self, time):
        """ Set exposure time of camera """
        with self._thread_lock:
            if self.module_state() == 'idle':
                camera = self._camera()
                camera.set_exposure(time)
                self._exposure = camera.get_exposure()
            else:
                self.log.error('Unable to set exposure time. Acquisition still in progress.')

    def get_exposure(self):
        """ Get exposure of hardware """
        with self._thread_lock:
            self._exposure = self._camera().get_exposure()
            return self._exposure

    def set_gain(self, gain):
        with self._thread_lock:
            if self.module_state() == 'idle':
                camera = self._camera()
                camera.set_gain(gain)
                self._gain = camera.get_gain()
            else:
                self.log.error('Unable to set gain. Acquisition still in progress.')

    def get_gain(self):
        with self._thread_lock:
            self._gain = self._camera().get_gain()
            return self._gain

    def capture_frame(self):
        """
        """
        with self._thread_lock:
            if self.module_state() == 'idle':
                def on_acquisition_end():
                    if self.module_state() == 'locked':
                        self.module_state.unlock()
                        self.timer.stop()
                        camera.sigNewFrame.disconnect()
                        self.log.info("Handling new frame")
                        self._last_frame = camera.get_acquired_data()
                        self.sigFrameChanged.emit(self._last_frame)
                        self.log.info(f"{self._last_frame}")
                        self.sigAcquisitionFinished.emit()
                def on_timeout():
                    camera.sigNewFrame.disconnect()
                    self.log.error("Acquisition timed out!")
                    self.module_state.unlock()
                    self.sigAcquisitionFinished.emit()
                self.module_state.lock()
                camera = self._camera()
                camera.sigNewFrame.connect(on_acquisition_end)
                self.timer = QtCore.QTimer()
                self.timer.timeout.connect(on_timeout)
                self.timer.setSingleShot(True)
                self.timer.start(10000)
                camera.start_single_acquisition()
            else:
                self.log.error('Unable to capture single frame. Acquisition still in progress.')

    def toggle_video(self, start):
        if start:
            self._start_video()
        else:
            self._stop_video()

    def _start_video(self):
        """ Start the data recording loop.
        """
        with self._thread_lock:
            if self.module_state() == 'idle':
                self.module_state.lock()
                exposure = max(self._exposure, self._minimum_exposure_time)
                camera = self._camera()
                # if camera.support_live_acquisition():
                #     camera.start_live_acquisition()
                # else:
                camera.start_trigged_acquisition()
                # self.__timer.start(1000 * exposure)
            else:
                self.log.error('Unable to start video acquisition. Acquisition still in progress.')

    def _stop_video(self):
        """ Stop the data recording loop.
        """
        with self._thread_lock:
            if self.module_state() == 'locked':
                self.__timer.stop()
                self._camera().stop_acquisition()
                self.module_state.unlock()
                self.sigAcquisitionFinished.emit()

    def __acquire_video_frame(self):
        """ Execute step in the data recording loop: save one of each control and process values
        """
        with self._thread_lock:
            camera = self._camera()
            self._last_frame = camera.get_acquired_data()
            self.sigFrameChanged.emit(self._last_frame)
            if self.module_state() == 'locked':
                exposure = max(self._exposure, self._minimum_exposure_time)
                self.__timer.start(1000 * exposure)
                if not camera.support_live_acquisition():
                    camera.start_single_acquisition()  # the hardware has to check it's not busy

    def create_tag(self, time_stamp):
        return f"{time_stamp}_captured_frame"

    def draw_2d_image(self, data, cbar_range=None):
        # Create image plot
        fig, ax = plt.subplots()
        cfimage = ax.imshow(data,
                            cmap='inferno',  # FIXME: reference the right place in qudi
                            origin='lower',
                            interpolation='none')

        if cbar_range is None:
            cbar_range = (np.nanmin(data), np.nanmax(data))
        cbar = plt.colorbar(cfimage, shrink=0.8)
        cbar.ax.tick_params(which=u'both', length=0)
        return fig
