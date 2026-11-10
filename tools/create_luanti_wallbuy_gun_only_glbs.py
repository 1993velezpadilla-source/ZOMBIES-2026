#!/usr/bin/env python3
"""Make normalized, static gun-only World Wall Buy GLBs from a private Luanti asset ZIP.

Run ONLY on the owner's private staged APK assets. No COD4 model bytes or
atlases are committed to GitHub. Outputs 28 unique GLBs plus wall_models.json
for mods/xz_classic_props to consume at runtime.
"""
import argparse
import json
import math
import struct
import zipfile
from pathlib import Path

SOURCE_MOD="games/voxelibre/mods/ak47dev/"
COD4=(
    "ak74u barrett colt45 deserteagle deserteaglegold dragunov g36c g3 "
    "m1014 m14 m16 m21 m40a3 m4 m60e4 mp44 mp5 p90 remington700 "
    "rpd rpg saw skorpion usp uzi winchester1200"
).split()
GUNS={**{"cod4:"+id:"a_"+id+"_none_none_std.glb" for id in COD4},
      "ak47dev:ak47":"ak47hd.glb","ak47dev:m9":"m9hd.glb"}
SIZES={5121:(1,"B"),5123:(2,"H"),5125:(4,"I"),5126:(4,"f")}
COMPS={"SCALAR":1,"VEC2":2,"VEC3":3}
def parse(raw):
    if len(raw)<28 or raw[:4]!=b"glTF":raise ValueError("GLB header missing")
    _,ver,total=struct.unpack_from("<4sII",raw)
    if ver!=2 or total!=len(raw):raise ValueError("GLB length incorrect")
    n,kind=struct.unpack_from("<I4s",raw,12)
    if kind!=b"JSON":raise ValueError("GLB JSON missing")
    doc=json.loads(raw[20:20+n])
    binlen,kind=struct.unpack_from("<I4s",raw,20+n)
    if kind!=b"BIN\x00":raise ValueError("GLB BIN missing")
    buf=raw[28+n:28+n+binlen]
    if len(buf)!=binlen:raise ValueError("GLB BIN truncated")
    return doc,buf
def values(doc,buf,i):
    a=doc["accessors"][i]
    v=doc["bufferViews"][a["bufferView"]]
    width,fmt=SIZES[a["componentType"]]
    components=COMPS[a["type"]]
    size=width*components
    step=v.get("byteStride",size)
    start=v.get("byteOffset",0)+a.get("byteOffset",0)
    if start+(a["count"]-1)*step+size>len(buf):raise ValueError("accessor bounds")
    format="<"+fmt*components
    return [struct.unpack_from(format,buf,start+k*step) for k in range(a["count"])]
def pack_glb(doc,data):
    txt=json.dumps(doc,separators=(",",":"),ensure_ascii=True).encode()
    txt+=b" "*((-len(txt))%4)
    data+=b"\x00"*((-len(data))%4)
    total=12+8+len(txt)+8+len(data)
    return b"glTF"+struct.pack("<II",2,total)+struct.pack("<I4s",len(txt),b"JSON")+txt+struct.pack("<I4s",len(data),b"BIN\x00")+data
def target_size(id):
    if id in ("m9","colt45","usp","deserteagle","deserteaglegold","skorpion"):return .65
    if id in ("barrett","dragunov","m40a3","m21","remington700","rpg"):return 1.40
    if id in ("saw","rpd","m60e4"):return 1.30
    return 1.12
def convert(raw,id):
    g,buf=parse(raw)
    prims=[]
    for p in g["meshes"][0]["primitives"]:
        # Source material 0 = GUN, material 1 = HANDS.
        if p.get("material")!=0:continue
        if p.get("mode",4)!=4:raise ValueError("not a triangle mesh")
        attr=p["attributes"]
        if not all(k in attr for k in ("POSITION","NORMAL","TEXCOORD_0")):
            raise ValueError("gun missing position/normal/UV")
        pos=values(g,buf,attr["POSITION"])
        norm=values(g,buf,attr["NORMAL"])
        uv=values(g,buf,attr["TEXCOORD_0"])
        ids=values(g,buf,p["indices"])
        if not (len(pos)==len(norm)==len(uv)):raise ValueError("attribute mismatch")
        if not all(0<=row[0]<len(pos) for row in ids):raise ValueError("index bounds")
        prims.append((pos,norm,uv,ids))
    if not prims:raise ValueError("no gun material geometry")
    allpos=[v for a,_,_,_ in prims for v in a]
    lo=[min(a[i] for a in allpos) for i in range(3)]
    hi=[max(a[i] for a in allpos) for i in range(3)]
    extent=max(hi[i]-lo[i] for i in range(3))
    if extent<=0:raise ValueError("degenerate weapon")
    scale=target_size(id)/extent
    center=[(lo[i]+hi[i])*.5 for i in range(3)]
    v,n,t,idx=[],[],[],[]
    for pos,norm,uv,indices in prims:
        offset=len(v)
        v.extend(tuple((x[i]-center[i])*scale for i in range(3)) for x in pos)
        n.extend(norm)
        t.extend(uv)
        idx.extend((offset+row[0],) for row in indices)
    if len(v)>65535:raise ValueError("too many vertices for mobile 16-bit index")
    binary=bytearray()
    views=[];accessors=[]
    def put(rows,fmt,dim,component,kind,target):
        while len(binary)%4:binary.append(0)
        offset=len(binary)
        for row in rows:binary.extend(struct.pack("<"+fmt*dim,*row))
        views.append(dict(buffer=0,byteOffset=offset,
                          byteLength=len(binary)-offset,target=target))
        a=dict(bufferView=len(views)-1,componentType=component,
               count=len(rows),type=kind)
        if kind=="VEC3":
            a["min"]=[min(row[i] for row in rows) for i in range(3)]
            a["max"]=[max(row[i] for row in rows) for i in range(3)]
        accessors.append(a)
        return len(accessors)-1
    pi=put(v,"f",3,5126,"VEC3",34962)
    ni=put(n,"f",3,5126,"VEC3",34962)
    ti=put(t,"f",2,5126,"VEC2",34962)
    ii=put(idx,"H",1,5123,"SCALAR",34963)
    doc={
      "asset":{"version":"2.0","generator":"XZIEL safe gun-only wall miniature"},
      "scene":0,"scenes":[{"nodes":[0]}],
      "nodes":[{"name":id+"_world_gun","mesh":0}],
      "meshes":[{"name":id+"_gun_without_hands",
                 "primitives":[{"attributes":{"POSITION":pi,"NORMAL":ni,
                   "TEXCOORD_0":ti},"indices":ii,"material":0,"mode":4}]}],
      "materials":[{"name":"gun_atlas","doubleSided":True,
                    "pbrMetallicRoughness":{"metallicFactor":.25,"roughnessFactor":.68}}],
      "buffers":[{"byteLength":len(binary)}],
      "bufferViews":views,"accessors":accessors}
    return pack_glb(doc,bytes(binary)),{"triangles":len(idx)//3,"vertices":len(v)}
def create(archive,dest):
    mod=SOURCE_MOD
    entries=set(archive.namelist())
    models={}
    records=[]
    for item,source in GUNS.items():
        id=item.split(":")[1]
        texture=("a_"+id+"_shared.png") if item.startswith("cod4:") else (
            "ak47hd_rifle.png" if id=="ak47" else "m9hd_rifle.png")
        if mod+"models/"+source not in entries:raise FileNotFoundError(source)
        if mod+"textures/"+texture not in entries:raise FileNotFoundError(texture)
        raw=archive.read(mod+"models/"+source)
        baked,stat=convert(raw,id)
        mesh="xz_wall_"+id+".glb"
        (dest/"models").mkdir(parents=True,exist_ok=True)
        (dest/"models"/mesh).write_bytes(baked)
        models[item]={"mesh":mesh,"texture":texture}
        records.append({"item":item,"source":source,"mesh":mesh,
                        "original_bytes":len(raw),"new_bytes":len(baked),**stat})
    if len(models)!=28 or len(set(x["mesh"] for x in models.values()))!=28:
        raise ValueError("Expected 28 different models")
    (dest/"wall_models.json").write_text(
        json.dumps({"schema_version":1,"models":models},sort_keys=True)+"\n")
    (dest/"wall_model_audit.json").write_text(json.dumps(records,indent=2)+"\n")
    return records
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--assets",required=True,help="PRIVATE uncompressed inner Luanti ZIP")
    p.add_argument("--out",required=True,help="private xz_classic_props mod staging")
    args=p.parse_args()
    out=Path(args.out)
    with zipfile.ZipFile(args.assets) as z:
        report=create(z,out)
    print("FIX43_GUN_ONLY_WALLBUY_GLBS",len(report),
          "TOTAL_BYTES",sum(x["new_bytes"] for x in report))
if __name__=="__main__":main()
