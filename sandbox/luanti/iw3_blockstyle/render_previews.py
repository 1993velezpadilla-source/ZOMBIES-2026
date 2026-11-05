#!/usr/bin/env python3
"""Render actual converted cuboid GLB as static, clearly labelled debug PNGs.

Screenshots are raster previews only, NOT original meshes, source texture
images, animation keyframes or a claim that gameplay ADS/reload already works.
Requires Pillow. Supports the exact GLB output of voxelize.py.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from voxelize import read_accessor, read_glb

W,H=1280,800
BG=(19,23,31)
MAX_FACES=65000

def font(size,bold=False):
    candidates=(
      "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        try:return ImageFont.truetype(candidate,size)
        except OSError:pass
    return ImageFont.load_default()

def mesh_faces(file:Path):
    doc,raw=read_glb(file)
    bounds=[]
    faces=[]
    for mesh in doc["meshes"]:
        for prim in mesh.get("primitives",[]):
            pos=read_accessor(doc,raw,prim["attributes"]["POSITION"])
            if "indices" in prim:
                ix=[a[0] for a in read_accessor(doc,raw,prim["indices"])]
            else:
                ix=list(range(len(pos)))
            color=doc["materials"][prim.get("material",0)].get(
                "pbrMetallicRoughness",{}).get("baseColorFactor",[.38,.40,.44,1])
            colors=read_accessor(doc,raw,prim["attributes"]["COLOR_0"]) if "COLOR_0" in prim["attributes"] else None
            bounds.extend(pos)
            if len(ix)%3:raise ValueError("non-triangle index count")
            for k in range(0,len(ix),3):
                ids=ix[k:k+3]
                if colors is not None:
                    tint=[sum(colors[i][v] for i in ids)/3 for v in range(3)]
                    rgb=tuple(max(20,min(245,int(color[v]*tint[v]*255))) for v in range(3))
                else:
                    rgb=tuple(max(28,min(220,int(v*255))) for v in color[:3])
                faces.append(([pos[i] for i in ids],rgb))
    if not faces or len(faces)>MAX_FACES:raise ValueError("unrenderable model")
    return faces,bounds

def make_view(faces,bounds,label,view,yaw,elev,output):
    lo=[min(p[i] for p in bounds) for i in range(3)]
    hi=[max(p[i] for p in bounds) for i in range(3)]
    span=[hi[i]-lo[i] for i in range(3)]
    major=max(range(3),key=lambda i:span[i])
    other=[i for i in range(3) if i!=major]
    vertical=2 if 2!=major else (1 if 1!=major else 0)
    side=next(i for i in other if i!=vertical)
    mid=[(hi[i]+lo[i])/2 for i in range(3)]
    a=math.radians(yaw);e=math.radians(elev)
    ca,sa,ce,se=math.cos(a),math.sin(a),math.cos(e),math.sin(e)
    def transform(p):
        x=p[major]-mid[major]
        y=p[side]-mid[side]
        z=p[vertical]-mid[vertical]
        # Orthographic camera with positive depth closer to viewer.
        screenx=ca*x+sa*y
        screeny=se*sa*x-se*ca*y+ce*z
        depth=-ce*sa*x+ce*ca*y+se*z
        return (screenx,screeny,depth)
    corners=[[x,y,z] for x in (lo[0],hi[0])
                       for y in (lo[1],hi[1])
                       for z in (lo[2],hi[2])]
    points=[transform(p) for p in corners]
    max_x=max(v[0] for v in points);min_x=min(v[0] for v in points)
    max_y=max(v[1] for v in points);min_y=min(v[1] for v in points)
    scale=min(1090/max(1e-5,max_x-min_x),580/max(1e-5,max_y-min_y))
    target_x=W/2;target_y=H/2+20
    col=(min_x+max_x)/2;row=(min_y+max_y)/2
    screen=lambda p:(target_x+(p[0]-col)*scale,target_y-(p[1]-row)*scale)
    prepared=[]
    for vertices,rgb in faces:
        tri=[transform(p) for p in vertices]
        a1=[tri[1][i]-tri[0][i] for i in range(3)]
        a2=[tri[2][i]-tri[0][i] for i in range(3)]
        cross=(a1[1]*a2[2]-a1[2]*a2[1],
               a1[2]*a2[0]-a1[0]*a2[2],
               a1[0]*a2[1]-a1[1]*a2[0])
        length=math.sqrt(sum(x*x for x in cross))
        if length<1e-14:continue
        normal=tuple(x/length for x in cross)
        # Slight facet lighting with broad ambient component.
        light=.76+.22*abs(sum(normal[i]*u for i,u in enumerate((-.38,.53,.76))))
        color=tuple(min(244,max(25,int(v*light))) for v in rgb)
        prepared.append((sum(t[2] for t in tri)/3,[screen(t) for t in tri],color))
    # Painter algorithm on compact opaque cube faces. Far triangles first.
    prepared.sort(key=lambda t:t[0])
    im=Image.new("RGB",(W,H),BG)
    draw=ImageDraw.Draw(im)
    # Studio blueprint backdrop (no fabricated screenshots / background scenery).
    for x in range(0,W,40):
        draw.line((x,0,x,H),fill=(28,32,42),width=1)
    for y in range(0,H,40):
        draw.line((0,y,W,y),fill=(28,32,42),width=1)
    for _,verts,c in prepared:
        draw.polygon(verts,fill=c)
    draw.rectangle((0,0,W,90),fill=(15,17,23))
    draw.text((32,19),"AK-47  /  COD4 CONVERTED GEOMETRY",font=font(28,True),fill=(239,241,246))
    draw.text((34,58),label,font=font(16),fill=(173,189,202))
    draw.rectangle((0,H-55,W,H),fill=(14,16,22))
    draw.text((33,H-40),
      "REAL GEOMETRY • STATIC DEBUG PREVIEW • ANIMATIONS/ADS NOT VISUALLY VERIFIED",
      font=font(14,True),fill=(231,197,127))
    im.save(output,optimize=True)
    return {"file":str(output),"triangles":len(prepared),
            "axis_assumption":f"long={major} vertical={vertical} side={side}"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--hands",type=Path)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    faces,bounds=mesh_faces(args.input)
    print(make_view(faces,bounds,"ISOMETRIC / BLOCKSTYLE · RAW MODEL REST POSE",
        "iso",28,25,args.output/"ak47_cod4_blockstyle_3quarter.png"))
    print(make_view(faces,bounds,"PROFILE / BLOCKSTYLE · RAW MODEL REST POSE",
        "profile",0,5,args.output/"ak47_cod4_blockstyle_profile.png"))
    print(make_view(faces,bounds,"TOP-DOWN INSPECTION · NOT ADS",
        "top",3,82,args.output/"ak47_cod4_blockstyle_top.png"))
    if args.hands and args.hands.is_file():
        f,b=mesh_faces(args.hands)
        print(make_view(f,b,"ORIGINAL COD4 VIEWHANDS CONVERTED TO BLOCKS",
           "hands",30,25,args.output/"ak47_cod4_blockstyle_hands.png"))

if __name__=="__main__":
    main()
