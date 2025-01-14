# %%
from vimba import *

# %%
with Vimba.get_instance() as vb:
    liste = vb.get_all_cameras()
    print(liste)
# %%
liste[0]
# %%
with liste[0] as cam:
    cam.ExposureTime.set(1)
# %%
with Vimba.get_instance() as vb:
    liste = vb.get_all_cameras()
    print(liste)
    liste[0]
    with liste[0] as cam:
        frame = cam.get_frame()
# %%
import matplotlib.pyplot as plt

# %%
plt.imshow(frame.as_opencv_image())
# %%
frame_converted = frame.as_opencv_image()

# %%
