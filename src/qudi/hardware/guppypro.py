# -*- coding: utf-8 -*-

__all__ = ['GuppyPro']

import time
import numpy as np
from qudi.interface.camera_interface import CameraInterface
from qudi.core.connector import Connector
from qudi.core.statusvariable import StatusVar
from qudi.core.configoption import ConfigOption
from qudi.util.mutex import Mutex
import logging
from vimba import *

logging.basicConfig(filename='logfile.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GuppyPro(CameraInterface):
    """ 
    Allied Vision GuppyPro
    """

    # Cameras dictionary
    # Dictionary of the correspondence between cameras and camera Detection number
    _id_to_detection = {"DEV_0xA4701120ABD31": 1,
                            "DEV_0xA4701120A77DD": 2, "DEV_0xA4701120ABD33": 3}
    # Same as above but keys are detection numbers
    _detection_to_id = {
        num: identity for identity, num in _id_to_detection.items()}

    # OPTIONS
    _camera_detection_number = ConfigOption('camera_detection_number', 2)
    _support_live = ConfigOption('support_live', True)
    _resolution = ConfigOption('resolution', (1280, 720))  # High-definition !

    _live = False
    _acquiring = False
    _exposure = ConfigOption('exposure', .1)
    _gain = ConfigOption('gain', 1.)
    
    
    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        camera_id = self._detection_to_id[self._camera_detection_number]
        with Vimba.get_instance() as self.vimba:
            try:
                self.camera = self.vimba.get_camera_by_id(camera_id)
                logger.info(f"Detection{self._camera_detection_number} \
                    opened successfully !")                
                return True

            except VimbaCameraError:
                logger.error(f"Detection {self._camera_detection_number} was not found. \
                             Please check that the camera is plugged in.")
                return False
                # raise VimbaCameraError('Failed to access Camera \'{}\'. Abort.'.format(camera_id))
                
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
        """ Does not work yet 
        @FIX ME later maybe """
        if self._live:
            self.frame = np.zeros(self._resolution)
            return False
        else:
            self._acquiring = True
            logger.info(f"Detection{self._camera_detection_number}: Starting acquisition")
                
            with self.camera as cam:
                cam.TriggerSource.set("Software")
                self.frame = cam.get_frame(timeout_ms=3000)
            self.frame.convert_pixel_format(PixelFormat.Mono8)
                
            self._acquiring = False
            return True
        
    def start_trigged_acquisition(self):
        pass
        
        # def handler_single(cam: Camera, frame: Frame):
        #     logging.info("GuppyCam    : Handling frame")
        #     frame.convert_pixel_format(PixelFormat.Mono8)
        #     self.last_frame = frame.as_opencv_image()
        #     # Resetting the queue frame seems to be the best practice
        #     cam.queue_frame(frame)
        #     self.stopAcquisition.set()
        

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
        data = self.frame
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
