#!d:\PythonProjects\AbsorptionGUI\absenv\Scripts\python.exe

import pyqtgraph as pg
from Classes.GuppyCam import *
from Classes.ui_241023_AbsorptionGUI import Ui_MainWindow # changes on the UI must be done there
from Classes.Capture import CameraWorker, VimbaLoadingWorker
from Classes.Analysis import AnalyseOD
from Classes.Display import ImageView
from Classes.AnalysisWindow import GraphicWindowFreqScan
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import numpy as np
import logging
import json # for opening/saving user parameters

logging.basicConfig(level=logging.DEBUG)

class MainWindow(QMainWindow):
    
    # Signal emitted when image gets changed
    newImage_signal = pyqtSignal()
    
    def __init__(self):
        """
        Initiates the Ui_MainWindow() class, and gets the Ui_MainWindow() instance.
        """
        self.config_filename = "config.json" # Path and filename to config file
        # self.camera_index = 0
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.showMaximized() 
        self.scan_type = None # ui of the analysis window
        
        # Initializing panels
        self.initSettings()
        self.initDisplay()
        self.initAcquisition()
        self.initFitPanel()
        
        app_icon = QIcon()
        app_icon.addFile('D:/PythonProjects/AbsorptionGUI/icons/absgui_icon.png', QSize(32,32))
        self.setWindowIcon(app_icon)
        
        # Saving config at the end
    def closeEvent(self, event):
        self.refresh_interface_settings()
        self._saveSettings()
    
    
    ############################################################################
    ####                                                                    ####
    ####                            DISPLAY                                 ####
    ####                                                                    ####
    ############################################################################
        
    def initDisplay(self):
        """
        Initializes the image displaying part of the UI.
        """
        self.display = ImageView()
        self.ui.ImageDisplayLayout.addWidget(self.display)
        
        self.fit_view = self.ui.AnalysisWidget.addViewBox()

        self._connectDisplayButtons()
        
        # Adding a toggle button for normalization
        
        self.ui.checkBox_normalize = QCheckBox(self.ui.centralwidget)
        self.ui.checkBox_normalize.setChecked(False)
        self.ui.checkBox_normalize.setText("Use Normalization")

        self.ui.DisplaySettings.addWidget(self.ui.checkBox_normalize)
        
        # Storing current images
        self.noImage = True
        self.images = {"bright": np.zeros_like(self.display.image),
                       "dark": np.zeros_like(self.display.image),
                       "OD": self.display.image,
                       "Natoms": np.zeros_like(self.display.image)}
        self.selectedImageType = "OD"
        self.analysis = None
        
        # Number of atoms label
        self.ui.NumberOfAtomsLabel.setMinimumSize(QSize(250, 0))
        self.ui.NumberOfAtomsLabel.setText(" ")
        # Connecting roi movement with change of the atom number
        self.ui.spinBox_N_step_scan.setMaximum(int(1e6))
        
        
    def _onROItogglebtn(self):
        if self.display.isROIenabled:
            self.display.roi_disable()
        else:
            self.display.roi_enable()
             
    def _onNormtogglebtn(self):
        if self.display.isNormalizationEnabled:
            self.display.normalization_disable()
        else:
            self.display.normalization_enable()
    
    def _onCrosshairtogglebtn(self):
        if self.display.isCrosshairActive:
            self.display.crosshair_disable()
        else:
            self.display.crosshair_enable()

    def _onRecalcODButton(self):
        """Gets called when the Recalculate OD button is pressed."""
        if self.analysis is not None:
            print(self.getNormalization())
            self.images["OD"] = self.analysis.calculate_OD(normalization_ROI=self.getNormalization())
            # self.images["Natoms"] = self.analysis.calculate_atom_density(self.curr_pixel_size)
            self.images["Natoms"] = self.analysis.calculate_atom_density(self.interface_settings[self.camera_index - 1]["PixelSize"])
            self.display.setImage(self.images[self.selectedImageType])
            self.retrieveAtomNumber()
            
    def _connectDisplayButtons(self):
        """Initializes connections between Display buttons and the function they call."""
        # Connecting Image selection button
        self.ui.ImageSourceCombo.currentIndexChanged.connect(self._onImageDisplaySel)
        # Connecting ROI toggle button
        self.display.roi_disable()
        self.ui.checkBox_showROI.stateChanged.connect(self._onROItogglebtn)
        # Connecting Normalization toggle button
        self.display.normalization_disable()
        self.ui.checkBox_showNorm.stateChanged.connect(self._onNormtogglebtn)
        # Connecting Crosshair toggle button
        self.display.crosshair_disable()
        self.ui.checkBox_showCross.stateChanged.connect(self._onCrosshairtogglebtn)
        # Connecting Normalize/Recalc OD button
        self.ui.pushButton_Norm.setText("Recalculate OD")
        self.ui.pushButton_Norm.setEnabled(False)
        self.ui.pushButton_Norm.clicked.connect(self._onRecalcODButton)
        self.ui.fitPushButton.clicked.connect(self.fit_image)
        self.ui.pushButton_N_at_scan.clicked.connect(self.frequency_scan)

    def _onImageDisplaySel(self, num):
        """Gets called when the Image source selection changes to index "num".

        Args:
            num (int): Image source index. 0: OD, 1: Atom number, 2: Bright image, 3: Dark image. 
        """
        num_to_im = ["OD", "Natoms", "bright", "dark"]
        selected_image = self.ui.ImageSourceCombo.currentText()
        self.selectedImageType = num_to_im[num]
        self.display.setImage(self.images[self.selectedImageType])
    
    #### Image handling  
    
    def getNormalization(self):
        """Retrieves current normalization ROI. If the "Use Normalization" button isn't checked, returns None.

        Returns:
            list: Coordinates of the normalization ROI as [x1, x2, y1, y2]. Can also be None.
        """
        if self.ui.checkBox_normalize.isChecked():
            return self.display.normalization_getcoords()
        else:
            return None
    
    def retrieveAtomNumber(self):
        """Calculates the total number of atoms in the ROI."""
        if not self.noImage:  # Checking whether an image has been made already
            self.number_of_atoms = self.analysis.calculate_atom_number(self.display.roi_getcoords())
            self.ui.NumberOfAtomsLabel.setFont(QFont('Times', 20)) 
            self.ui.NumberOfAtomsLabel.setText(self.analysis.format_atom_number(self.number_of_atoms))
        
        if self.scan_type is not None:
            if self.scan_type == "frequency scan":
                # Assurez-vous que la fenêtre d'analyse est déjà ouverte
                if self.analysis_freq_window:
                    self.analysis_freq_window.update_data(self.number_of_atoms)  # Mettre à jour la fenêtre d'analyse avec le nombre d'atomes

                
        
    def refreshImage(self, bright_image, dark_image) -> None:
        """
        Calculates the OD and Natoms images, and stores them along bright and dark in self.images.
        """
        logging.info("UI : Refreshing image")
        self.noImage = False
        self.images["bright"] = bright_image
        self.images["dark"] = dark_image
        self.analysis = AnalyseOD(bright=bright_image, dark = dark_image)
        # Computing the OD and atom number density
        self.images["OD"] = self.analysis.calculate_OD(normalization_ROI=self.getNormalization())
        self.images["Natoms"] = self.analysis.calculate_atom_density(self.interface_settings[self.camera_index - 1]["PixelSize"])
        self.display.setImage(self.images[self.selectedImageType])
        
        # Signalling that image was just changed
        self.newImage_signal.emit()
        self.retrieveAtomNumber()
    
    ############################################################################
    ####                                                                    ####
    ####                  CAMERA & INTERFACE SETTINGS                       ####
    ####                                                                    ####
    ############################################################################

    def initSettings(self):
        """ Initializes the Settings menu """
        ##################
        self._loadSettings() # Loads user interface settings
        #----------------#
        # CAMERA BUTTONS #
        # Exposure time
        self.ui.spinBox_exptime.setMinimum(0)
        self.ui.spinBox_exptime.setMaximum(100)
        self.ui.spinBox_exptime.valueChanged.connect(self._onExpTimeChange)
        self.ui.doubleSpinBox_freq_scan.setValue(5)
        self.ui.spinBox_N_at_freq_scan.setValue(35)
        self.ui.spinBox_N_step_scan.setValue(13)
        self.ui.CameraSettings.setEnabled(False)
        
        self.ui.spinBox_pixelsize.setMinimum(0)
        self.ui.spinBox_pixelsize.setMaximum(100)
        self.ui.spinBox_pixelsize.valueChanged.connect(self._onPixelSizeChange)
        # self.ui.spinBox_pixelsize.setEnabled(False)
        
    
    def _createClearSettings(self):
        self.interface_settings = []
        for index in range(1, 4):
            settings = {"ROI": [200, 400, 200, 400], "PixelSize": 8.53, "Norm": [50, 350, 50, 150]}
            self.interface_settings.append(settings)
    
    def _saveSettings(self):
        with open(self.config_filename, 'w') as f:
            json.dump(self.interface_settings, f)
            logging.info("UI : config file saved !")
    
    def _loadSettings(self):
        with open(self.config_filename, 'r') as f:
            self.interface_settings = json.load(f)
            logging.info("UI : config file loaded !")
        
    def _onPixelSizeChange(self, value):
        if (0 < value) and (100 > value):
            self.interface_settings[self.camera_index - 1]["PixelSize"] = value
            self._onRecalcODButton()
        
    def _onExpTimeChange(self, val):
        """Gets called whenever the exposure time is changed in the exposure time spinbox.
        val is new set value (in ms)
        """
        newval = val * 1e3 # newval is new set value (in µs)
        if (newval >= 72.0) and (newval < 67108934.0):
            self.camera.setExposureTime(newval) # setting the new exp time (in µs)
            logging.info("UI : Changing exposure time")

    ############################################################################
    ####                                                                    ####
    ####                            ACQUISITION                             ####
    ####                                                                    ####
    ############################################################################

    def initAcquisition(self):
        """ Initializes the Acquisition menu """
        #---------------------#
        # ACQUISITION BUTTONS #
        # Vimba loading
        self.vimbadaemon = None
        self.ui.pushButton.setObjectName("Load Cameras")
        self.ui.pushButton.clicked.connect(self.loadVimba)
        
        # Progress bar
        self.ui.VimbaLoad.setValue(0)
        # self.ui.VimbaLoad.setDisabled(True)
           
        # Camera selection
        self.ui.comboBox_camchoice.currentIndexChanged.connect(self._on_selection_change)
        self.ui.comboBox_camchoice.setEnabled(False)
        
        # Start button
        self.ui.pushButton_start_acq.clicked.connect(self.start_acquisition)
        self.ui.pushButton_start_acq.setEnabled(False)
        # Stop button
        self.ui.pushButton_stop_acq.setEnabled(False)
        self.ui.pushButton_stop_acq.clicked.connect(self.stop_acquisition)
        
        # Multiple acquisitions settings
        self.multipleAcquisitions = False 
        self._number_frame = 0
        
        # Changing max number of freq steps
        self.ui.spinBox_N_at_freq_scan.setMaximum(int(1e6))
        
        self.display.roi.sigRegionChanged.connect(self.retrieveAtomNumber)
        
               
    def _onVimbaReady(self, vd):
        """ Sequence of operations once Vimba is ready """
        # Stopping the progress bar timer
        self.loadtimer.stop()
        
        # Retrieving the daemon object and initializing settings
        self.vimbadaemon = vd
        self.camera_list = self.vimbadaemon.getCameraList()
        self.camera_index = self.camera_list[-1]
        
        # Opening camera
        self.open_camera(self.camera_index)
        
        # Moving ROI and norm to preset region
        self.display.roi_setcoords(self.interface_settings[self.camera_index - 1]["ROI"])
        self.display.normalization_setcoords(self.interface_settings[self.camera_index - 1]["Norm"])
        
        # Graphical displaying that Vimba is loaded
        self.ui.pushButton.setText("Reload Cameras")
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_start_acq.setEnabled(True)
        self.ui.CameraSettings.setEnabled(True)
        self.ui.VimbaLoad.setEnabled(False)
        self.ui.VimbaLoad.setValue(100)
        
        self.ui.pushButton_Norm.setEnabled(True)
        
        # Managing the camera selection menu
        for index in range(3): # 3 cameras indexes : 0, 1, 2
            self.ui.comboBox_camchoice.model().item(index).setEnabled(False)
        for det_number in self.camera_list: # 3 cameras numbers are possible : 1, 2, 3
            self.ui.comboBox_camchoice.model().item(det_number - 1).setEnabled(True)
        
        self.ui.comboBox_camchoice.setEnabled(True)
        self.ui.comboBox_camchoice.setCurrentIndex(self.camera_index - 1)
        
                
    def loadVimba(self):
        """
        Starts the capture module and capture parameters
        """
        # Some settings for progress bar
        loading_time = 9000    # Vimba loading time (in ms). Change if progress bar is not accurate
        refresh_time = 100      # Loading bar refresh delay (in ms)
        percent_refresh = 100 * refresh_time/loading_time
        self.cur_prog = 0
        
        if self.vimbadaemon is not None:        # Called only when reloading
            self.refresh_interface_settings()   # Pushes the ROI and normalization zones to the camera settings.
        # Function to update progress bar        
        def onTimer():
            self.cur_prog += percent_refresh
            if  self.cur_prog <= 100:
                self.ui.VimbaLoad.setValue(int(self.cur_prog))
        
        # UI response to vimba loading
        self.ui.pushButton.setDisabled(True)
        self.ui.VimbaLoad.setValue(0)
        
        # Progress bar updating timer
        self.loadtimer = QTimer()
        self.loadtimer.timeout.connect(onTimer)
        self.loadtimer.start(refresh_time)
        
        # Creating a worker to load the images, then moving it to a separate thread
        self.vbl_worker = VimbaLoadingWorker()
        self.vbl_thread = QThread()
        self.vbl_worker.moveToThread(self.vbl_thread)
        # Connecting the signals to start/stop worker and thread simultaneously
        self.vbl_thread.started.connect(self.vbl_worker.run)
        self.vbl_worker.loadingComplete.connect(self.vbl_thread.quit)
        self.vbl_worker.loadingComplete.connect(self.vbl_worker.deleteLater)
        self.vbl_thread.finished.connect(self.vbl_thread.deleteLater)
        # Connecting end of worker's task to the local method to call when Vimba is ready
        self.vbl_worker.loadingComplete.connect(self._onVimbaReady)
        
        self.vbl_thread.start(priority=0) # Let's rock !
        
    def open_camera(self, index):
        """Loads camera selected by index.

        Args:
            index (int): Camera index. Typicallly 1, 2 or 3.
        """
        # Loading current camera
        selected_camera = self.ui.comboBox_camchoice.currentText()
        self.camera_index = index
        self.camera = GuppyPro(self.vimbadaemon, self.camera_index)
        logging.info(f"UI : Camera selected : {selected_camera}")
        
        self.camera_settings = self.camera.getCameraSettings()
        self.ui.spinBox_exptime.setValue( float(self.camera_settings["ExposureTime"] * 1e-3 ))
        self.ui.spinBox_pixelsize.setValue( float(self.interface_settings[self.camera_index - 1]["PixelSize"]))
        self.worker_thread = CameraWorker(self) # Initializing current worker
        
    def _on_selection_change(self, num):
        """Gets called when the selected camera changes. ONLY to be called once Vimba is ready.
        Args:
            num (int) : Number of the camera in the menu. Typically 0, 1 or 2."""
        self.refresh_interface_settings() # Pushes the ROI and normalization zones to the camera settings.
        # Changing camera
        self.camera_index = num + 1
        self.open_camera(self.camera_index)
        # Updating ROI and normalization
        self.display.roi_setcoords(self.interface_settings[self.camera_index - 1]["ROI"])
        self.display.normalization_setcoords(self.interface_settings[self.camera_index - 1]["Norm"])
    
    def refresh_interface_settings(self):
        if not self.noImage:
            self.interface_settings[self.camera_index - 1]["ROI"] = self.display.roi_getcoords()
            self.interface_settings[self.camera_index - 1]["Norm"] = self.display.normalization_getcoords()
    
    def _acquire_images(self, N_IMAGES = 2):
        """
        To be called by the Worker thread.
        """
        image_data = self.camera.startAcquisition(N_IMAGES=N_IMAGES)
        if image_data is not None:
            self._number_frame += 1
            self.refreshImage(image_data[0], image_data[1])
        return None
     
    def start_acquisition(self) -> None:
        """
        start thread with the button start
        :return: None
        """
        # self.camera.stopAcquisition.clear()
        self.ui.pushButton_start_acq.setEnabled(False)
        self.ui.pushButton_stop_acq.setEnabled(True)
        # Disabling settings while capture
        self.ui.comboBox_camchoice.setEnabled(False)
        self.ui.CameraSettings.setEnabled(False)
        
        # Creating the capture thread
        self.worker_thread = CameraWorker(self)
        self.worker_thread.start()
        
    def stop_acquisition(self) -> None:
        self.worker_thread.requestInterruption()
        self.camera.stopAcquisition.set()
        self.worker_thread.wait(1000)
        self.worker_thread.quit()
        self.ui.pushButton_stop_acq.setEnabled(False)
        self.ui.pushButton_start_acq.setEnabled(True)
        
        # Enabling settings again
        self.ui.comboBox_camchoice.setEnabled(True)
        self.ui.CameraSettings.setEnabled(True)

    def take_picture(self) -> None:
        self.ui.pushButton_takePicture.setEnabled(False)
        self.current_images = [self.camera.takePicture()]
        self.refreshImage()
        self.ui.pushButton_takePicture.setEnabled(True)


    
    ############################################################################
    ####                                                                    ####
    ####                        FITTING PANEL                               ####
    ####                                                                    ####
    ############################################################################
    
    
    #### NOTE : as of today (30/07/2024), this part is a work in progress.
    
    def initFitPanel(self):
        """Initializes the fit panel.
        """
        self.fit_data = self.display.roi_getSlicedImg() # Retrieve image info
        
        self.ui.AnalysisWidget = pg.GraphicsLayoutWidget()
        
        self.changeFitType()
        
        self.fitPanel_connectbuttons()
        
        #self.ui.FitPanel.setEnabled(False)
        
    def fitPanel_connectbuttons(self):
        """ Connects buttons to functions for fit panel. """
        self.ui.fitTypeComboBox.currentIndexChanged.connect(self.changeFitType)
        self.display.roi.sigRegionChanged.connect(self.refreshFitPanel)
        self.newImage_signal.connect(self.refreshFitPanel)
    
    def getFitType(self):
        """Gets the type of fit that is currently required.

        Returns:
            fit_type: str, designates the fit type to be employed. Can be either "1Dx", "1Dy", "1Dxy" or "2D".
        """
        types = ["1Dx", "1Dy", "1Dxy", "2D"]
        index = self.ui.fitTypeComboBox.currentIndex()
        return types[index]
    
    def changeFitType(self):
        """Gets called when fit type needs to be changed.
        """
        self.fit_type = self.getFitType()
        self.ui.AnalysisWidget.clear()
        if self.fit_type == "1Dx" or self.fit_type == "1Dy":  # A single plot for x or y
            pass
            """self.fit_main_plot = self.ui.AnalysisWidget.addPlot(row = 1, col = 1)
            roicoords = self.display.roi_getcoords()
            self.fit_xvals = np.arange(roicoords[0], roicoords[1])
            self.fit_yvals = np.sum(self.fit_data, axis = 1)
            self.fit_main_plot.plot(self.fit_xvals, self.fit_yvals)"""
        
        if self.fit_type == "1Dxy":  # We need to have 2 plots, one for x and one for y
            pass # TBC...
        
        elif self.fit_type == "2D":  # If it is a 2D fit, we need to show the image
            pass
            """self.fit_data_img = pg.ImageItem(self.fit_data)
            self.fit_main_plot = self.ui.AnalysisWidget.addPlot(row = 1, col = 1)
            self.fit_main_plot.addItem(self.fit_data_img)"""
    
    def refreshFitPanel(self):
        """ Updates data for fit panel """
        self.fit_data = self.display.roi_getSlicedImg()
        roicoords = self.display.roi_getcoords()
        self.fit_xvals = np.arange(roicoords[0], roicoords[1])
        self.fit_yvals = np.sum(self.fit_data, axis = 1)



    def fit_image(self):
        self.fit_view.clear()
        
        if self.fit_type == "2D":
            self.fit_data, self.parameters = self.analysis.fit_cloud_profile_gaussian2D(self.display.roi_getcoords())
            self.ui.textBrowser_fit.clear()
            self.ui.textBrowser_fit.setText(
                f"A = {self.parameters[0]:.2f} \n"
                f"x_0 = {self.parameters[1]:.2f}  | y_0 = {self.parameters[2]:.2f} \n"
                f"sigma_x = {self.parameters[3]:.2f}    | sigma_y = {self.parameters[4]:.2f} [pxls] \n"
                f"sigma_x = {float(self.ui.spinBox_pixelsize.value()) * self.parameters[3]:.2f}    | sigma_y = {float(self.ui.spinBox_pixelsize.value()) * self.parameters[4]:.2f} [µm]"
            )

        # Appliquer la colormap personnalisée
        cmap = np.zeros((256, 3))  # Créer une colormap personnalisée (black, red, green, blue, white)
        cmap[:64] = [0, 0, 0]        # Black
        cmap[64:128] = [1, 0, 0]     # Red
        cmap[128:192] = [0, 1, 0]    # Green
        cmap[192:256] = [0, 0, 1]    # Blue
        cmap[192:256] = [1, 1, 1]     # White
        
        # Normaliser les données de fit
        normalized_fit_data = (self.fit_data - np.min(self.fit_data)) / (np.max(self.fit_data) - np.min(self.fit_data)) * 255
        color_mapped_fit_data = cmap[normalized_fit_data.astype(int)]

        # Créer l'item d'image avec les données ajustées
        fit_img_item = pg.ImageItem(image=color_mapped_fit_data)

        # Ajouter l'item d'image à la vue
        self.fit_view.addItem(fit_img_item)

        # Définir l'aspect ratio pour que les pixels soient carrés
        height, width = self.fit_data.shape

        # Ajuster les limites de la vue
        self.fit_view.setAspectLocked(True)  # Cela garantit que l'échelle des axes est la même
        self.fit_view.setRange(xRange=(0, width), yRange=(0, height), padding=0)

        
            

        #___________________Scan analysis part_________________#
        # the goal is, in a first time to plot the data during the scans like TOF scan in a new window 
        # second step is to add a "fit" button that will fit the data depending on which 
        # scan we use so probably a boolean var will check this.
        # the best thing would be to develop a new window dedicated to the analysis part. 
        


    #___________________Scan analysis part_________________#
    # the goal is, in a first time to plot the data during the scans like TOF scan in a new window 
    # second step is to add a "fit" button that will fit the data depending on which 
    # scan we use so probably a boolean var will check this.
    # the best thing would be to develop a new window dedicated to the analysis part. 
    
    def frequency_scan(self):
        """
        Méthode qui effectue le scan de fréquence et ouvre une fenêtre avec les résultats.
        """
        self.scan_type = "frequency scan"
        # Exemple : génération de données fictives
        frequency_steps = self.ui.doubleSpinBox_freq_scan.value()  # par exemple, 3.5 kHz entre chaque étape
        num_steps = self.ui.spinBox_N_at_freq_scan.value()  # par exemple, 31 étapes
          # Simuler des données

        # Titre du graphique
        title = "Frequency Scan"

        # Instancier la fenêtre GraphicWindow avec les arguments (titre, pas, nombre de pas, et données)
        self.analysis_freq_window = GraphicWindowFreqScan(title, frequency_steps, num_steps)
        self.analysis_freq_window.show()
    
    def rabi_scan(self):
        self.scan_type = "Rabi scan"
        time_steps = self.ui.doubleSpinBox_rabi_time_step.value()
        num_steps = self.ui.spinBox_rabi_N_step.value()
        self.analysis_rabi_window = None
    
    def TOF_scan(self):
        self.scan_type = "TOF scan" 