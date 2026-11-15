import time, numpy as np
from engine import Scene
import model as M
from frame import orbit_cam
parts=M.build_sr71(seam_light=True)
for ss in (1,2):
    s=Scene(1080,1920,ss=ss)
    for V,F,mat in parts: s.add((V,F),mat)
    eye,c=orbit_cam(parts,az=40,el=18,fill=0.9,fov=32)
    s.set_camera(eye,c,fov=32)
    t0=time.time(); im=s.render(); dt=time.time()-t0
    print(f"ss={ss} {im.size} {dt:.2f}s/frame -> 720 frames = {dt*720/60:.1f} min")
