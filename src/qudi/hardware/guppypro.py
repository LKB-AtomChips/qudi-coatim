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
from PySide2 import QtCore

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
    _support_live = ConfigOption('support_live', False)
    _resolution = ConfigOption('resolution', (656, 494))                    #(656, 494) for GuppyPro F031B
    _exposure = ConfigOption('exposure', .1)
    _gain = ConfigOption('gain', 1.)
    _minimum_exposure_time = ConfigOption('minimum_exposure_time', 72e-6)   #72 µs for GuppyPro F031B

    _buffer_count = ConfigOption('buffer-count', 5)
    
    _live = False
    _acquiring = False
    
    sigNewFrame = QtCore.Signal()
        
    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        self._camera_id = self._detection_to_id[self._camera_detection_number]
        self._request_acquisition_stop = False
        
        with Vimba.get_instance() as self.vimba:
            try:
                self.camera = self.vimba.get_camera_by_id(self._camera_id)
                logger.info(f"Detection{self._camera_detection_number} \
                    opened successfully !")
                return True

            except VimbaCameraError:
                logger.error(f"Detection {self._camera_detection_number} was not found. \
                             Please check that the camera is plugged in.")
                raise VimbaCameraError('Failed to access Camera \'{}\'. Abort.'.format(self._camera_detection_number))
        
    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.stop_acquisition()

    def get_name(self):
        """ Retrieve an identifier of the camera that the GUI can print

        @return string: name for the camera
        """
        return self._camera_detection_number

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
        """ Takes a single trigged image """
        if self._live:
            # self.frame = np.zeros(self._resolution)
            return False
        else:
            self._acquiring = True
            logger.info(f"Detection{self._camera_detection_number}: Starting acquisition")
            
            with Vimba.get_instance() as vimba:
                logger.info(f"Opening Vimba camera API")
                camera = vimba.get_camera_by_id(self._camera_id)
                with camera as cam:
                    logger.info(f"Detection{self._camera_detection_number}: Starting single frame acquisition")
                    raw_frame = cam.get_frame(timeout_ms=100000)
                    logger.info("A frame was just captured!")
                    self.frame = self._convert_frame_to_img(raw_frame)
            logger.info(f"Frame type: {type(self.frame)}")
            self._acquiring = False
            logger.info(f"Detection{self._camera_detection_number}: Ending acquisition")
            self.sigNewFrame.emit()
            return True
    
    def _convert_frame_to_img(self, frame):
        logger.info("Converting frame format")
        return np.array(frame.as_opencv_image().transpose()[0, :, :])
        
    def start_trigged_acquisition(self):
        """
        Starts acquisition of camera.
        """
        def handler(cam: Camera, frame: Frame):
            """ This function gets called every time a frame gets captured. """
            logging.info(f"Detection{self._camera_detection_number}: A frame was captured")
            frame.convert_pixel_format(PixelFormat.Mono8)
            self.frame = frame.as_opencv_image()
            # Resetting the queue frame seems to be the best practice
            cam.queue_frame(frame)
            # self.stopAcquisition.set()
            
        with Vimba.get_instance() as vimba:
            logger.info(f"Opening Vimba camera API")
            camera = vimba.get_camera_by_id(self._camera_id)
            with camera as cam:
                logging.info(f"Detection{self._camera_detection_number}: Starting acquisition")
                self._acquiring = True
                cam.TriggerSource.set("InputLines")
                cam.TriggerMode.set("On")
                cam.start_streaming(handler, buffer_count=self._buffer_count)
                while not self._request_acquisition_stop:
                    pass
                
                logging.info(f"Detection{self._camera_detection_number}: Stopping acquisition")
                cam.stop_streaming()
                self._request_acquisition_stop = False
                    
    def stop_acquisition(self):
        """ Stop/abort live or single acquisition

        @return bool: Success ?
        """
        self._request_acquisition_stop = True

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
