# logic/camera_logic.py
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import numpy as np
import time

class CameraLogic(QObject):
    """
    Simple camera stub that emits frames (numpy arrays) and simulated
    atom counts (float). Designed as a placeholder for real hardware modules.
    Signals:
      frame_ready(np.ndarray)
      atom_count(float)
      acquisition_started()
      acquisition_stopped()
    """
    frame_ready = pyqtSignal(object)
    atom_count = pyqtSignal(float)
    acquisition_started = pyqtSignal()
    acquisition_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._emit_frame)
        self.running = False
        self._frame_shape = (480, 640)  # default test shape
        self._counter = 0

    def start_acquisition(self, interval_ms=200):
        if self.running:
            return
        self.timer.start(interval_ms)
        self.running = True
        self.acquisition_started.emit()

    def stop_acquisition(self):
        if not self.running:
            return
        self.timer.stop()
        self.running = False
        self.acquisition_stopped.emit()

    def _emit_frame(self):
        # simulate an image and an "atom count"
        img = np.random.normal(loc=100, scale=20, size=self._frame_shape)
        # add a synthetic gaussian spot that grows slowly with counter
        cx, cy = self._frame_shape[0]//2, self._frame_shape[1]//2
        xs = np.arange(self._frame_shape[0]) - cx
        ys = np.arange(self._frame_shape[1]) - cy
        X, Y = np.meshgrid(xs, ys, indexing='ij')
        sigma = 10 + 0.1 * self._counter
        img += 2000 * np.exp(-(X**2 + Y**2) / (2*sigma**2))
        self._counter += 1

        # compute a proxy atom count (sum inside center ROI)
        atom_count = float(img[cx-5:cx+5, cy-5:cy+5].sum())

        self.frame_ready.emit(img)
        self.atom_count.emit(atom_count)
