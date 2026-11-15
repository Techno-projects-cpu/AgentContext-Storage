"""Sample frames from a video into one strip, to judge motion and continuity."""
import subprocess, sys
from PIL import Image
src=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 8
dur=float(subprocess.check_output(['/home/user/.local/bin/ffprobe','-v','error','-show_entries',
    'format=duration','-of','csv=p=0',src]).decode().strip())
W,H=270,480
ims=[]
for i in range(n):
    t=dur*(i+0.5)/n
    subprocess.check_output(['/home/user/.local/bin/ffmpeg','-y','-hide_banner','-loglevel','error',
      '-ss',f'{t:.3f}','-i',src,'-frames:v','1','/tmp/_f.png'])
    ims.append(Image.open('/tmp/_f.png').resize((W,H),Image.LANCZOS))
cols=n if n<=8 else 4
rows=(n+cols-1)//cols
sheet=Image.new('RGB',(W*cols,H*rows),(0,0,0))
for k,im in enumerate(ims): sheet.paste(im,((k%cols)*W,(k//cols)*H))
sheet.save('/tmp/strip.png'); print('dur',dur,'->','/tmp/strip.png')
