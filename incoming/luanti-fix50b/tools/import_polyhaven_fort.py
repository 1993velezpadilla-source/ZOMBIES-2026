#!/usr/bin/env python3
"""Import CC0 Poly Haven modular_fort_01 as actual textured Luanti node meshes.

Build-time only; fetches official Poly Haven API and checks MD5s.
Converts each glTF mesh node into a single-cell OBJ using ONE shared atlas.
No weapon, AI, barricade, or engine files are modified.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import struct
import urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

ASSET = "modular_fort_01"
API = f"https://api.polyhaven.com/files/{ASSET}"
SOURCE = "https://polyhaven.com/a/modular_fort_01"
COMPONENT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
SIZE = {5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}

def download(url, dest, md5=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req=urllib.request.Request(url, headers={"User-Agent":"XZ-Zombies-CC0-Asset-Importer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response, dest.open("wb") as out:
        while True:
            chunk=response.read(1024*1024)
            if not chunk: break
            out.write(chunk)
    if md5 and hashlib.md5(dest.read_bytes()).hexdigest().lower()!=md5.lower():
        raise RuntimeError("Source checksum mismatch: "+url)

def accessor(doc, binary, i):
    ac=doc["accessors"][i]
    if ac.get("sparse"): raise RuntimeError("Sparse glTF accessor unsupported")
    view=doc["bufferViews"][ac["bufferView"]]
    if view.get("buffer",0)!=0: raise RuntimeError("Multiple glTF buffers unsupported")
    code=COMPONENT[ac["componentType"]]
    n=COUNTS[ac["type"]]
    step=SIZE[ac["componentType"]]*n
    stride=view.get("byteStride",step)
    off=view.get("byteOffset",0)+ac.get("byteOffset",0)
    fmt="<"+code*n
    if stride<step or off+(ac["count"]-1)*stride+step>len(binary):
        raise RuntimeError("Invalid glTF accessor bounds")
    return [struct.unpack_from(fmt,binary,off+k*stride) for k in range(ac["count"])]

def transform(node):
    if "matrix" in node:
        return np.array(node["matrix"],dtype=float).reshape((4,4),order="F")
    x,y,z,w=node.get("rotation",[0,0,0,1])
    r=np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]
    ])
    out=np.eye(4)
    out[:3,:3]=r@np.diag(node.get("scale",[1,1,1]))
    out[:3,3]=node.get("translation",[0,0,0])
    return out

def material_slot(doc, material_index):
    try:
        m=doc["materials"][material_index]["pbrMetallicRoughness"]["baseColorTexture"]
        i=doc["textures"][m["index"]]["source"]
        name=doc["images"][i].get("uri","").lower()
    except (TypeError,IndexError,KeyError):
        name=""
    if "trim" in name:return (1,0)
    if "plaster" in name:return (0,1)
    return (0,0)

def build(moddir:Path, scratch:Path):
    scratch.mkdir(parents=True, exist_ok=True)
    req=urllib.request.Request(API,headers={"User-Agent":"XZ-Zombies-CC0-Asset-Importer/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:
        meta=json.load(r)
    fmt=meta["gltf"]["1k"]["gltf"]
    download(fmt["url"],scratch/"fort.gltf",fmt["md5"])
    include=fmt["include"]
    for rel,info in include.items():
        # Only original CC0 geometry and 1024px diffuse textures; no huge PBR maps.
        if rel.endswith(".bin") or "_diff_1k." in rel:
            download(info["url"],scratch/rel,info["md5"])
    doc=json.loads((scratch/"fort.gltf").read_text())
    binary=(scratch/"modular_fort_01.bin").read_bytes()
    # A single 2048x2048 PNG atlas shared by all modules, retaining
    # the original 1024x1024 plaster, stone and trim diffuse details.
    atlas=Image.new("RGB",(2048,2048),(100,95,88))
    for category,xy in [("wall",(0,0)),("trim",(1,0)),("plaster",(0,1))]:
        matches=list((scratch/"textures").glob(f"*_{category}_diff_1k.*"))
        if len(matches)!=1:raise RuntimeError("Missing CC0 texture: "+category)
        with Image.open(matches[0]) as img:
            atlas.paste(img.convert("RGB").resize((1024,1024)),(xy[0]*1024,xy[1]*1024))
    textured=moddir/"textures"
    models=moddir/"models"
    textured.mkdir(parents=True,exist_ok=True)
    models.mkdir(parents=True,exist_ok=True)
    atlas.save(textured/"xz_fort_atlas.png",optimize=True)

    nodes=doc.get("nodes",[])
    scene_index=doc.get("scene",0)
    roots=doc["scenes"][scene_index]["nodes"]
    mesh_nodes=[]
    def descend(i, parent):
        node=nodes[i]
        world=parent@transform(node)
        if "mesh" in node:mesh_nodes.append((i,node,world))
        for child in node.get("children",[]):descend(child,world)
    for i in roots:descend(i,np.eye(4))
    if not mesh_nodes:raise RuntimeError("Source glTF contains no mesh nodes")

    def make_component(i,node,world):
        mesh=doc["meshes"][node["mesh"]]
        chunks=[]
        all_positions=[]
        for primitive in mesh["primitives"]:
            if primitive.get("mode",4)!=4:continue
            positions=np.array(accessor(doc,binary,primitive["attributes"]["POSITION"]),dtype=float)
            v=np.column_stack((positions,np.ones(len(positions))))@world.T
            positions=v[:,:3]
            if not np.all(np.isfinite(positions)):raise RuntimeError("NaN vertex")
            if "TEXCOORD_0" in primitive["attributes"]:
                uv=np.array(accessor(doc,binary,primitive["attributes"]["TEXCOORD_0"]),dtype=float)
            else:
                uv=np.zeros((len(positions),2))
            indices=([int(k[0]) for k in accessor(doc,binary,primitive["indices"])]
                     if "indices" in primitive else list(range(len(positions))))
            if len(indices)%3:raise RuntimeError("Non triangle index count")
            if indices and (min(indices)<0 or max(indices)>=len(positions)):
                raise RuntimeError("Invalid index")
            slot=material_slot(doc,primitive.get("material"))
            chunks.append((positions,uv,indices,slot))
            all_positions.extend(positions)
        if not all_positions:return None
        verts=np.array(all_positions)
        minimum=np.min(verts,axis=0)
        maximum=np.max(verts,axis=0)
        extent=maximum-minimum
        if max(extent)<0.0001:return None
        # One genuine 3D object per inventory cell, no Minecraft-cube geometry.
        scale=0.96/max(extent)
        center=(maximum+minimum)*0.5
        lines=[f"# CC0 Poly Haven {SOURCE}",f"# {node.get('name','fort component')}"]
        offset=0
        num_tri=0
        for positions,uv,indices,(tx,ty) in chunks:
            pos=(positions-center)*scale
            for p in pos:
                lines.append("v %.7f %.7f %.7f"%tuple(p))
            for u,v in uv:
                # glTF UV origin is top left; OBJ V origin is bottom left.
                u=(float(u)%1.0)/2+tx*0.5
                v=1.0-((float(v)%1.0)/2+ty*0.5)
                lines.append(f"vt {u:.7f} {v:.7f}")
            for j in range(0,len(indices),3):
                a,b,c=(indices[j+k] for k in range(3))
                # A per-face normal avoids missing/black geometry on OBJ import.
                v0,v1,v2=pos[[a,b,c]]
                normal=np.cross(v1-v0,v2-v0)
                length=np.linalg.norm(normal)
                if length<1e-10:continue
                normal=normal/length
                lines.append("vn %.7f %.7f %.7f"%tuple(normal))
                n=num_tri+1
                lines.append("f "+" ".join(f"{offset+k+1}/{offset+k+1}/{n}" for k in (a,b,c)))
                num_tri+=1
            offset+=len(positions)
        if num_tri==0:return None
        return (lines,num_tri,extent)

    manifest=[]
    for i,node,world in mesh_nodes:
        if len(manifest)>=64:break
        result=make_component(i,node,world)
        if result is None:continue
        lines,tris,extent=result
        k=len(manifest)+1
        key=f"fort_{k:02d}"
        name=re.sub(r"\s+"," ",str(node.get("name","Fort module")).replace("_"," ")).strip()
        if not name or name.lower().startswith("object"):
            name="Stone Fort Module"
        name=name[:38]
        filename=f"xz_{key}.obj"
        (models/filename).write_text("\n".join(lines)+"\n")
        manifest.append((key,f"Modular Fort | {name} {k:02d}",filename,tris,[float(round(-e*scale/2,5)) for e in extent]+[float(round(e*scale/2,5)) for e in extent]))
    if not manifest:raise RuntimeError("No usable components converted")
    def lua_string(value):return json.dumps(value,ensure_ascii=True)
    rows=["-- GENERATED from CC0 Poly Haven modular_fort_01; DO NOT hand-edit","return {"]
    for key,label,filename,tris,box in manifest:
        coords=",".join(str(v) for v in box)
        rows.append(f"  {{id={lua_string(key)}, label={lua_string(label)}, mesh={lua_string(filename)}, tris={tris},box={{{coords}}}}},")
    rows.append("}")
    (moddir/"polyhaven_fort_manifest.lua").write_text("\n".join(rows)+"\n")
    report={"source":SOURCE,"license":"CC0","resolution":1024,
            "components":len(manifest),"triangles":sum(row[3] for row in manifest),
            "atlas":"xz_fort_atlas.png","models":[r[2] for r in manifest]}
    (scratch/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--mod-dir",type=Path,required=True)
    p.add_argument("--scratch",type=Path,required=True)
    a=p.parse_args()
    build(a.mod_dir,a.scratch)
