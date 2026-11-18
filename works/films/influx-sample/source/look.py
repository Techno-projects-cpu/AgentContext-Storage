import numpy as np, time
from engine import *
import model as M
s=Scene(1080,1920,ss=1, bg=(0.006,0.008,0.014), bg_top=(0.03,0.045,0.075))
for V,F,mat in M.build_sr71():
    s.add((V,F),mat)
s.set_camera((6.4,3.4,8.2),(0,0.1,0.2),fov=30)
t0=time.time(); im=s.render(); print('s',round(time.time()-t0,2))
im.save('/tmp/plane3.png')
