# -*- coding: utf-8 -*-

__all__ = ['Absorption_DisplayPanel']

import os
import datetime

from PySide2 import QtGui, QtCore, QtWidgets
from qudi.core.connector import Connector
from qudi.core.module import GuiBase
from qudi.gui.absorption.camera_settings_dialog import CameraSettingsDialog
from qudi.util.datastorage import TextDataStorage
import pyqtgraph as pg
import numpy as np
import logging

class DisplayPanel(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.imageview = ImageView()
        self.toolbar = ToolBar()
        
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.imageview)
        
        self.setLayout(self.layout)
        
class ToolBar(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.image_source_selector = ImageSourceComboBox()        
        self.show_roi_checkbox = QtWidgets.QCheckBox("Show ROI")
        self.show_crosshair_checkbox = QtWidgets.QCheckBox("Show Crosshair")
        self.show_normalization_checkbox = QtWidgets.QCheckBox("Show Normalization")
        self.recalculate_OD_pushbutton = QtWidgets.QPushButton("Recalculate OD")
        
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.image_source_selector)
        self.layout.addWidget(self.show_roi_checkbox)
        self.layout.addWidget(self.show_crosshair_checkbox)
        self.layout.addWidget(self.show_normalization_checkbox)
        self.layout.addWidget(self.recalculate_OD_pushbutton)
        
        self.setLayout(self.layout)

class ImageSourceComboBox(QtWidgets.QComboBox):
    def __init__(self):
        super().__init__()
        image_sources = ["Optical Density", "Number of Atoms", "Bright Image", "Dark Image"]
        for image_source in image_sources:
            self.addItem(image_source)

class Crosshair(pg.TargetItem):
    isMoving = QtCore.Signal(bool)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def mouseDragEvent(self, ev):
        if not self.movable or ev.button() != QtCore.Qt.LeftButton:
            return
        ev.accept()
        if ev.isStart():
            self.symbolOffset = self.pos() - self.mapToView(ev.buttonDownPos())
            self.moving = True

        if not self.moving:
            return
        self.setPos(self.symbolOffset + self.mapToView(ev.pos()))
        self.isMoving.emit()

        if ev.isFinish():
            self.moving = False
            self.sigPositionChangeFinished.emit(self)

class ImageView(pg.GraphicsLayoutWidget):
    """The ImageView displays the image and the tools to manipulate it.
    It is instantiated to a default image that can be changed using the setImage method.
    """
    def __init__(self):
        super().__init__()

        # Initializing the default image
        self.default_size_on_startup = (640, 480)
        self.image = np.zeros(self.default_size_on_startup)

        # Parameters of the main window
        backgroundcolor = (25,25,25)
        self.setBackground(backgroundcolor)
        # Parameters of side plots
        max_height_side_plots = 80  # Max width of the side plots
        self.pen = pg.mkPen(color=(255, 255, 0), width = 2) # pen of the side plots

        # Creating the image
        self.imageItem = pg.ImageItem(self.image)
        # self.imageItem.setColorMap(pg.colormap.getFromMatplotlib("viridis"))
        # self.imageItem.setColorMap("viridis")

        # Initializing the image display area
        self.imageDisplay = self.addPlot(row = 1, col = 1)
        self.imageDisplay.addItem(self.imageItem) # Putting the image in the frame
        self.imageItem.setColorMap("viridis")
        self.imageDisplay.setAspectLocked(lock = True, ratio = 1) # Locking aspect ratio

        # Initializing the ROI on the image display area
        self._initROI()

        # Initializing the normalization on the image display area
        self._initNormalization()

        # Initializing the label
        self.label = pg.TextItem()
        self.label.setTextWidth(max_height_side_plots)
        self.textZone = self.addViewBox(col = 0, row =0)
        self.textZone.setMaximumWidth(max_height_side_plots)
        self.textZone.setMaximumHeight(max_height_side_plots)
        self.textZone.addItem(self.label)

        # Constructing right plot for displaying vertical ROI data
        self.vplot = self.addPlot(row = 1, col = 0)
        self.vplot.setMaximumWidth(max_height_side_plots)
        self.vplot.getViewBox().invertX(True)
        self._initHistogram() # initializes the histogram
        
        # Constructing lower plot for displaying horizontal ROI data
        self.hplot = self.addPlot(row = 0, col = 1)
        self.hplot.setMaximumHeight(max_height_side_plots)
        self.roi.sigRegionChanged.connect(self._onROIchange)


        # Initializing the crosshair
        self._init_crosshair()
        
        # Updating the side plots
        self._onROIchange()

    #######
    # GENERAL PUBLIC METHODS
    def setImage(self, newimage):
        """Change the displayed image to the newimage passed as an argument."""
        self.image = newimage
        self.imageItem.setImage(newimage, autoLevels=False)
        self._onROIchange()

    #######
    # ROI MANAGEMENT
    def _initROI(self):
        # Initializes the ROI
        self.isROIenabled = True
        roipen = (255, 255, 50)
        roihandlepen = (255, 255, 0)
        roihandleoverpen = (255, 255, 255)
        self.roibounds = QtCore.QRectF(QtCore.QPointF(0,0), QtCore.QPointF(self.image.shape[0], self.image.shape[1]))

        self.roi = pg.ROI([200, 200], [100, 100], pen = roipen, handlePen=roihandlepen,
                          handleHoverPen=roihandleoverpen, maxBounds=self.roibounds)
        self.roi.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.roi.addScaleHandle([0, 0.5], [0.5, 0.5])

		# adding roi to the plot area
        self.imageDisplay.addItem(self.roi)
        
        # Initializing plot crosshairs for updating (they will be painted when initializing crosshairs)
        self.hplot_vline = None

		# setting z value to roi
		# making sure ROI is drawn above image
        self.roi.setZValue(10)
    
    def _onROIchange(self):
        """Updates the horizontal and vertical plots anytime the ROI is changed."""
        selected = self.roi_getSlicedImg()      # Retrieving selected pixels
        [x1, x2, y1, y2] = self.roi_getcoords() 
        selected_x = np.arange(x1, x2)          # Creating x axis
        selected_y = np.arange(y1, y2)          # Creating y axis
 
        # Changing the plotted values
        self.hplot.clear()
        self.vplot.clear()
        self.hplot.plot(selected_x, selected.mean(axis = 1), pen = self.pen)
        self.vplot.plot(selected.mean(axis = 0), selected_y, pen = self.pen)

        if self.hplot_vline is not None:
            # Painting again the crosshairs (they get erased because of clear !)
            self.hplot.addItem(self.hplot_vline, ignoreBounds = True)
            self.vplot.addItem(self.vplot_hline, ignoreBounds = True)
            self.hplot_vline.setPos(self.hplot_vline.getPos())
            self.vplot_hline.setPos(self.vplot_hline.getPos())

    def roi_getcoords(self) -> tuple:
        """ Returns the coordinates of the ROI as a list
        [x1, x2, y1, y2] coordinates of the two points defining the ROI rectangle"""
        selected = self.roi_getSlicedImg()
        x1, y1 = self.roi.pos()     # Position (in px) of bottom left of ROI
        size = np.shape(selected)   # Size (in px) of ROI
        dx, dy = size[0], size[1]
        return [int(x1), int(x1 + dx), int(y1), int(y1 + dy)]
    
    def roi_setcoords(self, coords: list):
        """Sets the coordinates of the ROI to the coords list inputted.

        Args:
            coords (list): Desired position of the ROI. Format [x1, x2, y1, y2].
        """
        [x1, x2, y1, y2] = coords
        self.roi.setPos(x1, y1)
        self.roi.setSize((x2 - x1, y2 - y1))
        
    def roi_getSlicedImg(self):
        """ Returns the portion of the image that is selected by the ROI. """
        return self.roi.getArrayRegion(self.image, self.imageItem)[:-1, :-1] # retrieving selected pixel values
        # excluding last row and column bc they show up as dark on the screen.

    def roi_enable(self):
        """ Displays the ROI if it is not already visible """
        if not self.isROIenabled:
            self.isROIenabled = True
            self.roi.setVisible(True)
            # self.imageDisplay.addItem(self.roi)

    def roi_disable(self):
        """ Hides the ROI from view if it is visible"""
        if self.isROIenabled:
            self.isROIenabled = False
            # self.imageDisplay.removeItem(self.roi)
            self.roi.setVisible(False)

    #######
    # NORMALIZATION ZONE HANDLING
    def _initNormalization(self):
        # Initializes the ROI
        self.isNormalizationEnabled = True
        norm_pen = pg.mkPen((80, 80, 255))
        norm_hoverpen = pg.mkPen(200, 200, 255)
        norm_handle_pen = pg.mkPen((150, 150, 255))
        norm_handleHover_pen = pg.mkPen(220, 150, 255)
        self.norm = pg.ROI([10, 20], [100, 50], handlePen = norm_handle_pen, handleHoverPen=norm_handleHover_pen,
                           pen = norm_pen, hoverPen=norm_hoverpen, maxBounds=self.roibounds)
        self.norm.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.norm.addScaleHandle([0, 0.5], [0.5, 0.5])

		# adding roi to the plot area
        self.imageDisplay.addItem(self.norm)

		# setting z value to roi
		# making sure ROI is drawn above image
        self.norm.setZValue(5)

    def normalization_enable(self):
        if not self.isNormalizationEnabled:
            self.isNormalizationEnabled = True
            self.norm.setVisible(True)
            # self.imageDisplay.addItem(self.norm)

    def normalization_disable(self):
        if self.isNormalizationEnabled:
            self.isNormalizationEnabled = False
            self.norm.setVisible(False)
            # self.imageDisplay.removeItem(self.norm)

    def normalization_getcoords(self) -> tuple:
        """ Returns the coordinates of the normalization zone as a list
        [x1, x2, y1, y2] coordinates of the two points defining the ROI rectangle"""
        selected = self.norm.getArrayRegion(self.image, self.imageItem) # retrieving selected pixel values
        x1, y1 = self.norm.pos()     # Position (in px) of bottom left of norm zone
        size = np.shape(selected)   # Size (in px) of norm zone
        dx, dy = size[0], size[1]
        return [int(x1), int(x1 + dx), int(y1), int(y1 + dy)]

    def normalization_setcoords(self, coords: list):
        """Sets the coordinates of the normalization region to the coords list inputted.

        Args:
            coords (list): Desired position of the normalization. Format [x1, x2, y1, y2].
        """
        [x1, x2, y1, y2] = coords
        self.norm.setPos(x1, y1)
        self.norm.setSize((x2 - x1, y2 - y1))
        
    #######
    # HISTOGRAM
    def _initHistogram(self):
        # Initializes the histogram
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.imageItem)
        self.addItem(self.hist, row = 0, col = 2, rowspan = 2)
        self.hist.vb.setMouseEnabled(y=False)
        

    #######
    # CROSSHAIRS
    def _init_crosshair(self):
        # Crosshair params
        zval = 10    
        self.crosshairpen = pg.mkPen(color='r')
        crosshairsize = 20

        # Creating the crosshair
        self.isCrosshairActive = True
        self.crosshair = Crosshair(pen = self.crosshairpen, size = crosshairsize, pos=(300, 200), symbol = "o")
        self.imageDisplay.addItem(self.crosshair)
        self.crosshair.setZValue(zval)

        self.crosshair.isMoving.connect(self._onCrosshairMove)

        # Crosshair extension on image plot
        self.crosshair_ext_v = pg.InfiniteLine(angle=90, movable=False, pen=self.crosshairpen)
        self.crosshair_ext_h = pg.InfiniteLine(angle=0,  movable=False, pen=self.crosshairpen)
        self.imageDisplay.addItem(self.crosshair_ext_v, ignoreBounds=True)
        self.imageDisplay.addItem(self.crosshair_ext_h, ignoreBounds=True)
        self.crosshair_ext_h.setZValue(zval)
        self.crosshair_ext_v.setZValue(zval)
        
        # Painting the crosshair over the vertical plot
        self.vplot_hline = pg.InfiniteLine(angle=0,  movable=False, pen=self.crosshairpen)
        self.vplot.addItem(self.vplot_hline, ignoreBounds=True)

        # Painting the crosshair over the horizontal plot
        self.hplot_vline = pg.InfiniteLine(angle=90, movable=False, pen=self.crosshairpen)
        self.hplot.addItem(self.hplot_vline, ignoreBounds=True)

        self.cur_value = 0
        self._onCrosshairMove()
        
    def _onCrosshairMove(self):
        x, y = self.crosshair.pos()

        # Moving the crosshair in the plots
        self.hplot_vline.setPos(x)
        self.vplot_hline.setPos(y)
        # Moving the extensions in the image display
        self.crosshair_ext_v.setPos(x)
        self.crosshair_ext_h.setPos(y)

        # Updating the value displayed
        if 0 <= x < self.image.shape[0] and 0 <= y < self.image.shape[1]:
            self.cur_value = self.image[int(x), int(y)]
            self.label.setText(f"({x:.1f}, {y:.1f}) \n val = {self.cur_value:.2f}")
    
    def crosshair_disable(self):
        """ Removes the crosshair from view """
        if self.isCrosshairActive:
            self.isCrosshairActive = False
            self.crosshair.setVisible(False)
            self.crosshair_ext_h.setVisible(False)
            self.crosshair_ext_v.setVisible(False)
            self.hplot_vline.setVisible(False)
            self.vplot_hline.setVisible(False)

    def crosshair_enable(self):
        """ Displays the crosshair """
        if not self.isCrosshairActive:
            self.isCrosshairActive = True
            self.crosshair.setVisible(True)
            self.crosshair_ext_h.setVisible(True)
            self.crosshair_ext_v.setVisible(True)
            self.hplot_vline.setVisible(True)
            self.vplot_hline.setVisible(True)