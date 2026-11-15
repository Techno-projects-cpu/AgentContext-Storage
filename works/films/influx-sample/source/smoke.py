import numpy as np, time
from engine import *
s = Scene(1080, 1920, ss=1)
mat = dict(color=(0.62,0.66,0.74), metal=0.9, rough=0.24)
s.add(bevel_box(2.2,0.5,3.4, bevel=0.12), mat)
s.add(cylinder(0.45,1.6,24), dict(color=(0.4,0.45,0.55),metal=0.95,rough=0.18))
s.add(wing_plate(span=2.6), dict(color=(0.5,0.55,0.63),metal=0.92,rough=0.30))
s.add(grid_plane(n=8, spacing=0.9, z=1.4), dict(color=(0.10,0.22,0.95),metal=0.2,rough=0.9))
s.set_camera((3.4,2.0,5.2),(0,0,0), fov=40)
t0=time.time(); img=s.render(); print("render s", round(time.time()-t0,2))
img.save('/tmp/smoke.png'); print(img.size)
