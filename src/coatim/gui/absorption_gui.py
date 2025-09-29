# gui/absorption_gui.py
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5 import QtCore
import sys

# Import the original generated UI class
try:
    from AbsorptionGUI_v1 import Ui_MainWindow
except Exception:
    from PyQt5.QtWidgets import QLabel, QVBoxLayout
    class Ui_MainWindow:
        def setupUi(self, MainWindow):
            MainWindow.setWindowTitle("Absorption GUI (fallback)")
            central = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Fallback UI - Absorption GUI not available"))
            central.setLayout(layout)
            MainWindow.setCentralWidget(central)

# Import our new image display GUI
from gui.image_display_gui import ImageDisplayGui


class AbsorptionMainWindow(QMainWindow):
    """
    Main window for absorption imaging.
    Integrates ImageDisplayGui inside the layout defined in AbsorptionGUI_v1.ui
    """
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create and insert image display widget into the placeholder layout
        self.image_display = ImageDisplayGui()
        try:
            self.ui.ImageDisplayLayout.addWidget(self.image_display)
        except Exception:
            print("⚠️ Could not find ImageDisplayLayout in UI, adding as central widget instead")
            self.setCentralWidget(self.image_display)

        # Connectors to logic modules
        self.display_logic = None
        self.camera_logic = None
        self.analysis_logic = None

        # Hook up buttons (if they exist in UI)
        try:
            self.ui.pushButton_start_acq.clicked.connect(self.start_acquisition)
            self.ui.pushButton_stop_acq.clicked.connect(self.stop_acquisition)
            self.ui.pushButton.clicked.connect(self.load_cameras)  # "Load Cameras"
            self.ui.pushButton_Norm.clicked.connect(self.normalize_images)
        except Exception:
            pass

    def set_display_logic(self, display_logic):
        self.display_logic = display_logic
        self.image_display.set_logic(display_logic)

    def set_camera_logic(self, camera_logic):
        self.camera_logic = camera_logic
        if camera_logic is not None:
            camera_logic.frame_ready.connect(self.on_frame_ready)
            camera_logic.atom_count.connect(self.on_atom_count)

    def set_analysis_logic(self, analysis_logic):
        self.analysis_logic = analysis_logic

    # ---- Camera control ----
    def start_acquisition(self):
        if self.camera_logic:
            self.camera_logic.start_acquisition()
        else:
            print("No camera logic connected")

    def stop_acquisition(self):
        if self.camera_logic:
            self.camera_logic.stop_acquisition()
        else:
            print("No camera logic connected")

    def load_cameras(self):
        print("Load Cameras pressed - implement real hardware loading here")

    # ---- Updates ----
    def on_frame_ready(self, frame):
        self.image_display.set_image(frame)

    def on_atom_count(self, count):
        try:
            self.ui.NumberOfAtomsLabel.setText(f"{count:.3g}")
        except Exception:
            print(f"Atom count: {count:.3g}")

    def normalize_images(self):
        if self.display_logic is None:
            print("No display logic available")
            return
        coords = self.image_display.get_norm_coords()
        print("Normalization coords:", coords)
