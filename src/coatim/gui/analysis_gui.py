# gui/analysis_gui.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDoubleSpinBox
import pyqtgraph as pg
from PyQt5.QtCore import pyqtSignal, Qt

class AnalysisGui(QWidget):
    """
    Thin GUI that delegates fit logic to an external AnalysisLogic instance.
    Exposes:
      - set_logic(analysis_logic)
      - add_datapoint(atom_count)
      - set_scan_params(frequency_step, num_steps)
    """
    request_fit = pyqtSignal(tuple)  # p0 tuple (offset, amp, width, center)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analysis - Frequency Scan")
        self.resize(800, 600)

        layout = QVBoxLayout()
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', "Nombre d'atomes")
        self.plot_widget.setLabel('bottom', "Fréquence [kHz]")
        layout.addWidget(self.plot_widget)

        ctrl = QHBoxLayout()
        self.offset = QDoubleSpinBox(); self.offset.setRange(-1e9, 1e9); self.offset.setValue(0.0)
        self.amp = QDoubleSpinBox(); self.amp.setRange(-1e12, 1e12); self.amp.setValue(1e6)
        self.width = QDoubleSpinBox(); self.width.setRange(0.0, 1e9); self.width.setValue(40.0)
        self.center = QDoubleSpinBox(); self.center.setRange(-1e9, 1e9); self.center.setValue(0.0)

        ctrl.addWidget(QLabel("Offset:")); ctrl.addWidget(self.offset)
        ctrl.addWidget(QLabel("Amplitude:")); ctrl.addWidget(self.amp)
        ctrl.addWidget(QLabel("FWHM:")); ctrl.addWidget(self.width)
        ctrl.addWidget(QLabel("Center:")); ctrl.addWidget(self.center)

        self.fit_button = QPushButton("Perform fit")
        self.clear_button = QPushButton("Clear")
        ctrl.addWidget(self.fit_button)
        ctrl.addWidget(self.clear_button)
        layout.addLayout(ctrl)

        self.width_label = QLabel("FWHM after fit: N/A")
        layout.addWidget(self.width_label)

        self.setLayout(layout)

        # internal storage
        self.data = []
        self.frequency_step = 1.0  # default
        self.current_step = 0

        # External logic to be set via set_logic
        self.logic = None

        # connections
        self.fit_button.clicked.connect(self.on_fit_clicked)
        self.clear_button.clicked.connect(self.on_clear_clicked)

        # plot items
        self.data_plot = None
        self.fit_plot = None

    def set_logic(self, logic):
        self.logic = logic

    def set_scan_params(self, frequency_step, num_steps=None):
        self.frequency_step = frequency_step
        if self.logic:
            self.logic.reset(frequency_step, num_steps)

    def add_datapoint(self, atom_count):
        if self.logic is None:
            # still keep internal list so plotting works
            self.data.append(float(atom_count))
            self.current_step += 1
        else:
            self.logic.add_datapoint(atom_count)
            self.current_step = self.logic.current_step

        self._update_plot()

    def _x_array(self):
        n = self.current_step
        return (pg.np.arange(n) * self.frequency_step) - (n * self.frequency_step / 2.0)

    def _update_plot(self):
        x = self._x_array()
        if self.logic is None:
            y = pg.np.array(self.data)
        else:
            y = pg.np.array(self.logic.data[:self.current_step])

        self.plot_widget.clear()
        if len(x) > 0:
            self.plot_widget.plot(x, y, pen='b', symbol='o')

    def on_fit_clicked(self):
        p0 = (self.offset.value(), self.amp.value(), self.width.value(), self.center.value())
        if self.logic is None:
            return
        try:
            x, y, fit_data, popt, pcov = self.logic.perform_lorentz_fit(p0)
            # replot
            self.plot_widget.clear()
            self.plot_widget.plot(x, y, pen='b', symbol='o')
            self.plot_widget.plot(x, fit_data, pen='r')
            self.width_label.setText(f"FWHM after fit: {popt[2]:.3f}")
        except Exception as e:
            self.width_label.setText(f"Fit error: {e}")

    def on_clear_clicked(self):
        if self.logic:
            self.logic.reset(self.frequency_step)
        self.data = []
        self.current_step = 0
        self.plot_widget.clear()
        self.width_label.setText("FWHM after fit: N/A")
