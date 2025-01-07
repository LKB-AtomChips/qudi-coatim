# -*- coding: utf-8 -*-

__all__ = ['GuppyDummy']

import time
import numpy as np
from qudi.interface.camera_interface import CameraInterface
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex


class GuppyDummy(CameraInterface):
    """ Dummy module for AlliedVision GuppyPro camera

    Example config for copy-paste:
o
    camera_dummy:
        module.Class: 'camera.camera_dummy.CameraDummy'
        options:
            support_live: True
            camera_name: 'Dummy camera'
            # FIXME: resolution config option causes no image
            # resolution: (1280, 720)
            exposure: 0.1
            gain: 1.0
    """


    _support_live = ConfigOption('support_live', True)
    _camera_name = ConfigOption('camera_name', 'Dummy camera')
    _resolution = ConfigOption('resolution', (1280, 720))  # High-definition !

    _live = False
    _acquiring = False
    _exposure = ConfigOption('exposure', .1)
    _gain = ConfigOption('gain', 1.)

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        pass

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.stop_acquisition()

    def get_name(self):
        """ Retrieve an identifier of the camera that the GUI can print

        @return string: name for the camera
        """
        return self._camera_name

    def get_size(self):
        """ Retrieve size of the image in pixel

        @return tuple: Size (width, height)
        """
        return self._resolution

    def support_live_acquisition(self):
        """ Return whether or not the camera can take care of live acquisition

        @return bool: True if supported, False if not
        """
        return self._support_live

    def start_live_acquisition(self):
        """ Start a continuous acquisition

        @return bool: Success ?
        """
        if self._support_live:
            self._live = True
            self._acquiring = False

    def start_single_acquisition(self):
        """ Start a single acquisition

        @return bool: Success ?
        """
        if self._live:
            return False
        else:
            self._acquiring = True
            time.sleep(float(self._exposure+10/1000))
            self._acquiring = False
            return True

    def stop_acquisition(self):
        """ Stop/abort live or single acquisition

        @return bool: Success ?
        """
        self._live = False
        self._acquiring = False

    def get_acquired_data(self):
        """ Return an array of last acquired image.

        @return numpy array: image data in format [[row],[row]...]

        Each pixel might be a float, integer or sub pixels
        """
        data = np.random.random(self._resolution)*self._exposure*self._gain
        return data.transpose()

    def set_exposure(self, exposure):
        """ Set the exposure time in seconds

        @param float time: desired new exposure time

        @return float: setted new exposure time
        """
        self._exposure = exposure
        return self._exposure

    def get_exposure(self):
        """ Get the exposure time in seconds

        @return float exposure time
        """
        return self._exposure

    def set_gain(self, gain):
        """ Set the gain

        @param float gain: desired new gain

        @return float: new exposure gain
        """
        self._gain = gain
        return self._gain

    def get_gain(self):
        """ Get the gain

        @return float: exposure gain
        """
        return self._gain

    def get_ready_state(self):
        """ Is the camera ready for an acquisition ?

        @return bool: ready ?
        """
        return not (self._live or self._acquiring)
