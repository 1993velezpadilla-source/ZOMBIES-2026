#!/usr/bin/env python3
"""Create a real Luanti native wield mesh from the ORIGINAL 47 AK component boxes.

Unlike an animated entity, a mesh-drawtype node is drawn by Luanti's first-
person WieldMeshSceneNode; no player-bone attachment is required. One material
and single texture atlas avoid glTF slot and shader compatibility surprises.

Editable/animated GLB from V3 is retained alongside the reliable visible OBJ.
"""
import ast
import struct
import sys
import zlib
from pathlib import Path

THIS=Path(__file__).resolve().parent
ORIGINAL=THIS.parent/"v3/build_ak47_assets.py"

def extract_parts():
    tree=ast.parse(ORIGINAL.read_text(encoding="utf8"))
    result=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=="box":
            result.append(tuple(ast.literal_eval(a) for a in n.value.args))
    assert len(result)==47, f"Expected original 47 parts; got {len(result)}"
    return result

def pngchunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)

def make_atlas(out):
    palette = [
        ("metal",(92,98,102)),
        ("black",(35,38,42)),
        ("wood",(146,80,42)),
        ("skin",(180,131,103)),
    ]
    raw=bytearray()
    for y in range(16):
        raw.append(0)
        for mat,col in palette:
            for x in range(16):
                shade=((x*19+y*13+(x*y)%7)%19)-9
                if mat=="wood":
                    shade+= (8 if x%4==0 else 0)-(4 if y%7==1 else 0)
                raw+=bytes(max(0,min(255,c+shade)) for c in col)+b"\xff"
    header=struct.pack(">IIBBBBB",64,16,8,6,0,0,0)
    out.write_bytes(b"\x89PNG\r\n\x1a\n" +
        pngchunk(b"IHDR",header)+
        pngchunk(b"IDAT",zlib.compress(raw,9))+
        pngchunk(b"IEND",b""))

FACES=[
    ((0,3,2,1),(0,0,-1)),((4,5,6,7),(0,0,1)),
    ((0,4,7,3),(-1,0,0)),((1,2,6,5),(1,0,0)),
    ((3,7,6,2),(0,1,0)),((0,1,5,4),(0,-1,0)),
]
MATS={"metal":0,"black":1,"wood":2,"skin":3}
def make_obj(out,parts):
    # OBJ: 1.0 model units = 1 game node (unlike entity glTF: 10 units = 1).
    vlines=["# Original AK-47 prototype by Voxel Sandbox","o AK47Wield",
        "# The visible 3D rifle: separate 47 cuboid elements, one atlas.",
        "# Luanti uses 1 OBJ unit = 1 map node for static nodes.",
        "mtllib ak47dev_static.mtl", "usemtl ak47dev_atlas"]
    normals=[(0,0,-1),(0,0,1),(-1,0,0),(1,0,0),(0,1,0),(0,-1,0)]
    vlines.extend("vn %d %d %d"%q for q in normals)
    vertex=0
    texcoord=0
    for name,mat,bone,x1,y1,z1,x2,y2,z2 in parts:
        # Move the rigid rifle a little down and right relative to its node
        # origin, so it doesn't obscure the camera in first-person wielding.
        # The fitted ADS viewmodel is still separate in the animated GLB.
        scale=0.085
        dx,dy,dz=0,-.05,-.18
        verts=[
            (x1,y1,z1),(x2,y1,z1),(x2,y2,z1),(x1,y2,z1),
            (x1,y1,z2),(x2,y1,z2),(x2,y2,z2),(x1,y2,z2)]
        verts=[(x*scale+dx,y*scale+dy,z*scale+dz) for x,y,z in verts]
        vlines.append("g "+name)
        vlines.extend("v %.6f %.6f %.6f"%v for v in verts)
        idx=MATS[mat]
        # Tile per material in atlas: metal 0..0.25, black .25.. .50 etc.
        uv=[((idx+.04)/4,.94),((idx+.96)/4,.94),
            ((idx+.96)/4,.06),((idx+.04)/4,.06)]
        for face,(corners,_) in enumerate(FACES):
            for u,v in uv:
                vlines.append("vt %.6f %.6f"%(u,v))
            a,b,c,d=[vertex+i+1 for i in corners]
            t=texcoord+1
            n=face+1
            vlines.append("f %d/%d/%d %d/%d/%d %d/%d/%d"%
                          (a,t,n,b,t+1,n,c,t+2,n))
            vlines.append("f %d/%d/%d %d/%d/%d %d/%d/%d"%
                          (a,t,n,c,t+2,n,d,t+3,n))
            texcoord+=4
        vertex+=8
    out.write_text("\n".join(vlines)+"\n",encoding="ascii")
    out.with_suffix(".mtl").write_text(
        "newmtl ak47dev_atlas\nKd 1.0 1.0 1.0\nmap_Kd ak47dev_atlas.png\n",
        encoding="ascii")
    print(f"V3.1 native first-person OBJ: {len(parts)} independent parts, "
          f"{vertex} vertices, {2*6*len(parts)} triangles; "
          f"OBJ size {out.stat().st_size:,} bytes")

def main():
    if len(sys.argv)!=2:raise SystemExit("build_wield_mesh.py MOD_PATH")
    dest=Path(sys.argv[1])
    (dest/"models").mkdir(parents=True,exist_ok=True)
    (dest/"textures").mkdir(parents=True,exist_ok=True)
    parts=extract_parts()
    make_obj(dest/"models/ak47dev_static.obj",parts)
    make_atlas(dest/"textures/ak47dev_atlas.png")
    assert (dest/"models/ak47dev_static.obj").stat().st_size>10000
    assert (dest/"textures/ak47dev_atlas.png").read_bytes().startswith(b"\x89PNG")
if __name__=="__main__":main()
