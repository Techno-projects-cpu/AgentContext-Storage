"""One frame per shot, in a grid, for camera/typography review."""
import sys, time
import numpy as np
from PIL import Image
from shots import SHOTS
import render as R

W,H=432,768
which=[int(x) for x in sys.argv[1].split(',')] if len(sys.argv)>1 else list(range(len(SHOTS)))
frac=float(sys.argv[2]) if len(sys.argv)>2 else 0.55
ims=[]
for i in which:
    s=SHOTS[i]; t=s['start']+(s['end']-s['start'])*frac
    t0=time.time()
    im=R.render_frame(s,t,W,H,1)
    ims.append(im); print(i, s['name'], round(time.time()-t0,2),'s')
cols=3; rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(W*cols,H*rows),(0,0,0))
for k,im in enumerate(ims): sheet.paste(im,((k%cols)*W,(k//cols)*H))
sheet.save('/tmp/contact.png'); print('saved', sheet.size)
