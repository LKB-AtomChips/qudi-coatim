# logic/display_logic.py
import numpy as np

class DisplayLogic:
    """
    Pure data logic for display: ROI math, normalization zone math, crosshair value.
    The GUI still owns pyqtgraph ROI objects; logic expects raw arrays and
    provides coordinate conversions, value extraction, etc.
    """
    def __init__(self):
        self.image = None  # numpy array

    def set_image(self, image: np.ndarray):
        if image is None:
            self.image = None
            return
        self.image = np.asarray(image)

    def roi_coords_from_roi(self, roi, imageItem):
        """
        Given a pyqtgraph ROI and the imageItem, return coords [x1, x2, y1, y2]
        matching original code's convention.
        """
        selected = roi.getArrayRegion(self.image, imageItem)
        if selected is None:
            return [0, 0, 0, 0]
        # original code excluded last row/col; keep same behaviour if shape>0
        if selected.ndim >= 2:
            dx, dy = selected.shape[:2]
            if dx > 0: dx -= 1
            if dy > 0: dy -= 1
        else:
            dx, dy = 0, 0

        x1, y1 = roi.pos()
        return [int(x1), int(x1 + dx), int(y1), int(y1 + dy)]

    def normalization_coords_from_roi(self, norm_roi, imageItem):
        selected = norm_roi.getArrayRegion(self.image, imageItem)
        if selected is None:
            return [0, 0, 0, 0]
        dx, dy = selected.shape[:2]
        x1, y1 = norm_roi.pos()
        return [int(x1), int(x1 + dx), int(y1), int(y1 + dy)]

    def get_value_at(self, x, y):
        """
        Return image value at (x,y) or None if out of bounds.
        Note: x,y are floats in GUI coordinates; convert to int indices.
        """
        if self.image is None:
            return None
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.image.shape[0] and 0 <= yi < self.image.shape[1]:
            return float(self.image[xi, yi])
        return None

    def get_roi_slice(self, roi, imageItem):
        """Return numpy slice for ROI (same format as roi.getArrayRegion)"""
        sel = roi.getArrayRegion(self.image, imageItem)
        if sel is None:
            return np.array([])
        return sel[:-1, :-1] if sel.ndim >= 2 else sel
