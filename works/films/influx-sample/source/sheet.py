import numpy as np, time
from engine import *
import model as M
from frame import orbit_cam
parts = M.build_sr71()
out=[]
for i,(az,el) in enumerate([(35,14),(90,6),(135,22),(20,32),(70,-4),(180,10)]):
    s=Scene(540,960,ss=1, bg=(0.006,0.008,0.014), bg_top=(0.03,0.045,0.075))
    for V,F,mat in parts: s.add((V,F),mat)
    eye,c = orbit_cam(parts, az=az, el=el, fill=0.86, fov=30)
    s.set_camera(eye,c,fov=30)
    t0=time.time(); im=s.render(); print(i, round(time.time()-t0,2))
    out.append(im)
W,H=540,960
sheet=Image.new('RGB',(W*3,H*2))
for i,im in enumerate(out): sheet.paste(im,((i%3)*W,(i//3)*H))
sheet.save('/tmp/angles.png'); print('saved')
