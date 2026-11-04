#!/usr/bin/env python3
"""Extract only real video frames of an MP40 from actual Call of Duty gameplay.
No synthetic images or image-gen. Source and timestamp added on the contact sheet.
"""
from pathlib import Path
import subprocess, json, sys
from PIL import Image, ImageOps, ImageDraw, ImageFont
source=Path(sys.argv[1])
prefix=sys.argv[2]
start=float(sys.argv[3])
duration=float(sys.argv[4])
frames=int(sys.argv[5])
dest=Path("mp40_screenshots")/prefix
dest.mkdir(parents=True,exist_ok=True)
assert source.exists() and source.stat().st_size>10000, source
def get_frame(t,out):
    c=["ffmpeg","-hide_banner","-nostdin","-loglevel","error","-ss",f"{t:.3f}","-i",str(source),"-frames:v","1","-vf","scale='min(960,iw)':-2","-y",str(out)]
    subprocess.run(c,check=True,timeout=45)
    with Image.open(out) as im:
        assert im.width>100 and im.height>100
labels=[]
for i in range(frames):
    t=start+(i+0.5)*duration/frames
    output=dest/f"{i+1:02d}_{t:.3f}s.jpg"
    get_frame(t,output)
    labels.append(dict(index=i+1,timestamp_seconds=round(t,3),path=str(output)))
w=420
font=ImageFont.load_default()
thumbs=[]
for label in labels:
    im=Image.open(label["path"]).convert("RGB")
    h=round(w*im.height/im.width)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    pane=Image.new("RGB",(w,h+24),(20,22,26))
    pane.paste(im,(0,24))
    draw=ImageDraw.Draw(pane)
    draw.text((8,6),f"{prefix} | #{label['index']:02d} | {label['timestamp_seconds']:.2f}s",font=font,fill=(245,245,245))
    thumbs.append(pane)
cols=3
rows=(len(thumbs)+cols-1)//cols
cellh=max(p.height for p in thumbs)
sheet=Image.new("RGB",(w*cols,cellh*rows),(12,12,16))
for i,img in enumerate(thumbs):
    sheet.paste(img,((i%cols)*w,(i//cols)*cellh))
sheet.save(dest/"contact_sheet.jpg",quality=90)
(dest/"source_timestamps.json").write_text(json.dumps(dict(video=str(source),start=start,duration=duration,frames=labels),indent=2))
print("REAL_GAMEPLAY_FRAMES_EXTRACTED",prefix,len(labels),str(dest/"contact_sheet.jpg"))
