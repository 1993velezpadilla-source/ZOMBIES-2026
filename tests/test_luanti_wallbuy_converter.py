#!/usr/bin/env python3
"""Synthetic gun+hands GLB test; no copyrighted models in public CI."""
import importlib.util
import struct
from pathlib import Path

script=Path("tools/create_luanti_wallbuy_gun_only_glbs.py")
spec=importlib.util.spec_from_file_location("xz_wall_glb",script)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

binary=bytearray()
views=[]
accessors=[]
def add(rows,fmt,cols,component,type_):
    while len(binary)%4:binary.append(0)
    offset=len(binary)
    for row in rows:binary.extend(struct.pack("<"+fmt*cols,*row))
    views.append({"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset})
    accessors.append({"bufferView":len(views)-1,"componentType":component,
                      "count":len(rows),"type":type_})
    return len(accessors)-1
prims=[]
for material in (0,1):
    o=material*10.0
    pos=add([(o,0,0),(o+1,0,0),(o,1,0)],"f",3,5126,"VEC3")
    norm=add([(0,0,1)]*3,"f",3,5126,"VEC3")
    tex=add([(0,0),(1,0),(0,1)],"f",2,5126,"VEC2")
    idx=add([(0,),(1,),(2,)],"H",1,5123,"SCALAR")
    prims.append({"attributes":{"POSITION":pos,"NORMAL":norm,"TEXCOORD_0":tex},
                  "indices":idx,"material":material,"mode":4})
fixture={
    "asset":{"version":"2.0"},
    "buffers":[{"byteLength":len(binary)}],
    "bufferViews":views,"accessors":accessors,
    "meshes":[{"primitives":prims}],
    "nodes":[{"mesh":0}],"scenes":[{"nodes":[0]}],"scene":0
}
source=mod.pack_glb(fixture,bytes(binary))
out,stats=mod.convert(source,"m4")
g,_=mod.parse(out)
assert stats["triangles"]==1,stats
assert stats["vertices"]==3,stats
assert len(g["meshes"][0]["primitives"])==1
assert g["meshes"][0]["primitives"][0]["material"]==0
assert not g.get("skins") and not g.get("animations")
pos=g["accessors"][0]
assert pos["count"]==3 and abs(pos["max"][0]-pos["min"][0]-1.12)<1e-5
assert len(mod.GUNS)==28
assert len(set(mod.GUNS.values()))==28
assert all(name.startswith("cod4:") or name.startswith("ak47dev:") for name in mod.GUNS)
print("PASS: synthetic gun/hands stripping, static normalized GLB and 28 unique FIX43 weapon identifiers")
