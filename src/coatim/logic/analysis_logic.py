# logic/analysis_logic.py
import numpy as np
from scipy.optimize import curve_fit

# Try to import your existing DataAnalysis class (keeps compatibility)
try:
    from Classes.Analysis import DataAnalysis
except Exception:
    # Minimal fallback DataAnalysis if the real one isn't present
    class DataAnalysis:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        @staticmethod
        def fit_lorentz(x, offset, amp, fwhm, center):
            # Lorentzian parameterisation where fwhm is width
            gamma = fwhm / 2.0
            return offset + amp * (gamma**2 / ((x - center)**2 + gamma**2))

class AnalysisLogic:
    """
    Logic for frequency scan plotting and fitting. Stores data points and
    performs fits using DataAnalysis.fit_lorentz (or fallback).
    """
    def __init__(self):
        self.data = []
        self.frequency_step = None
        self.current_step = 0
        self.num_steps = None

    def reset(self, frequency_step=None, num_steps=None):
        self.data = []
        self.current_step = 0
        self.frequency_step = frequency_step
        self.num_steps = num_steps

    def add_datapoint(self, atom_count):
        """Append a single measurement (number of atoms)."""
        self.data.append(float(atom_count))
        self.current_step += 1

    def x_array(self):
        if self.frequency_step is None:
            raise RuntimeError("frequency_step not set")
        # center the x axis on 0 using current_step (length of data)
        n = self.current_step
        x = np.arange(n) * self.frequency_step - (n * self.frequency_step / 2.0)
        return x

    def perform_lorentz_fit(self, p0):
        """
        Perform a Lorentzian fit; p0 should be iterable (offset, amp, fwhm, center).
        Returns (x_data, y_data, fit_data, popt) or raises exception on fit failure.
        """
        if self.current_step <= 1:
            raise RuntimeError("Not enough data points to fit")

        x_data = self.x_array()
        y_data = np.array(self.data[:self.current_step])

        analysis = DataAnalysis(x_data, y_data)

        # curve_fit expecting function signature f(x, *params)
        popt, pcov = curve_fit(analysis.fit_lorentz, x_data, y_data, p0=p0)

        fit_data = analysis.fit_lorentz(x_data, *popt)
        return x_data, y_data, fit_data, popt, pcov
