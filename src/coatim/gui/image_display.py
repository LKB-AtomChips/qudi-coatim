# gui/image_display_gui.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
import pyqtgraph as pg
import numpy as np

# Reuse original ImageView code but thin wrapper to connect with DisplayLogic
# Import your original implementation? We will embed a slightly adapted version.

class ImageViewWidget(pg.GraphicsLayoutWidget):
    frame_clicked = pyqtSignal()
    def __init__(self, initial_image=None):
        super().__init__()
        self.image = initial_image if initial_image is not None else np.zeros((480,640))
        self.setBackground((25,25,25))

        # image item
        self.imageItem = pg.ImageItem(self.image)
        self.imageDisplay = self.addPlot(row=1, col=1)
        self.imageDisplay.addItem(self.imageItem)
        self.imageDisplay.setAspectLocked(True)

        # small side-plots and histogram (kept minimal)
        self.vplot = self.addPlot(row=1, col=0)
        self.vplot.getViewBox().invertX(True)
        self.hplot = self.addPlot(row=0, col=1)
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.imageItem)
        self.addItem(self.hist, row=0, col=2, rowspan=2)

        # ROI and normalization ROIs
        self.roi = pg.ROI([50,50], [100,100], pen=(255,255,50))
        self.imageDisplay.addItem(self.roi)
        self.norm_roi = pg.ROI([10,20], [40,40], pen=(80,80,255))
        self.imageDisplay.addItem(self.norm_roi)

        # crosshair
        self.crosshair = pg.InfiniteLine(angle=90, movable=False, pen='r')
        self.imageDisplay.addItem(self.crosshair)
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False, pen='r')
        self.imageDisplay.addItem(self.crosshair_h)

        self.roi.sigRegionChanged.connect(self._on_roi_change)
        self.norm_roi.sigRegionChanged.connect(self._on_roi_change)

        self._on_roi_change()

    def set_image(self, image):
        self.image = np.asarray(image)
        self.imageItem.setImage(self.image, autoLevels=False)
        self._on_roi_change()

    def _on_roi_change(self):
        # update side plots from ROI
        sel = self.roi.getArrayRegion(self.image, self.imageItem)
        if sel is None or sel.size == 0:
            return
        # keep shape behaviour similar to original
        if sel.ndim >= 2:
            sx = np.arange(sel.shape[0])
            sy = np.arange(sel.shape[1])
            self.hplot.clear(); self.vplot.clear()
            self.hplot.plot(sx, sel.mean(axis=1), pen=(255,255,0))
            self.vplot.plot(sel.mean(axis=0), sy, pen=(255,255,0))

    def get_roi_coords(self):
        x1, y1 = self.roi.pos()
        sel = self.roi.getArrayRegion(self.image, self.imageItem)
        if sel is None:
            return [0,0,0,0]
        dx, dy = sel.shape[:2]
        return [int(x1), int(x1+dx-1), int(y1), int(y1+dy-1)]

    def get_norm_coords(self):
        x1, y1 = self.norm_roi.pos()
        sel = self.norm_roi.getArrayRegion(self.image, self.imageItem)
        if sel is None:
            return [0,0,0,0]
        dx, dy = sel.shape[:2]
        return [int(x1), int(x1+dx-1), int(y1), int(y1+dy-1)]

class ImageDisplayGui(QWidget):
    """
    Thin wrapper: connects ImageViewWidget with DisplayLogic instance.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Display")
        layout = QVBoxLayout()
        self.label = QLabel("Image Display")
        layout.addWidget(self.label)
        self.image_widget = ImageViewWidget()
        layout.addWidget(self.image_widget)
        self.setLayout(layout)

        self.logic = None

    def set_logic(self, logic):
        self.logic = logic

    def set_image(self, image):
        if self.logic:
            self.logic.set_image(image)
        self.image_widget.set_image(image)

    def get_roi_coords(self):
        return self.image_widget.get_roi_coords()

    def get_norm_coords(self):
        return self.image_widget.get_norm_coords()
