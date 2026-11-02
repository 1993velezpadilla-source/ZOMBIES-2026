#!/usr/bin/env python3
"""EXPERIMENTAL real IW3 XANIM -> animated GLB proof for Godot/Blender inspection.

Converts matched *bone-name* XANIM tracks into glTF animation channels without
retargeting/rest-pose correction. Animation semantics/coordinate frames remain
UNVERIFIED; do not claim these as playable reload/ADS before rendered comparison.

The transformed GLBs are written ONLY into ignored ephemeral/private folders.
No proprietary models, textures, movements or keyframe values in public artifacts.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import struct
import sys

from iw3_xanim_v17 import load_xanim, AnimFormatError
from iw3_weapon_probe import atomic_json

def align4(b: bytes) -> bytes:
    return b + b"\x00"*((-len(b))%4)


def read_glb(path: Path):
    blob=path.read_bytes()
    if len(blob)<20 or len(blob)>128*1024*1024:
        raise ValueError("GLB invalid length")
    magic,ver,size=struct.unpack_from("<4sII",blob)
    if (magic,ver,size)!=(b"glTF",2,len(blob)):
        raise ValueError("GLB header mismatch")
    off=12
    chunks=[]
    while off<len(blob):
        clen,ctype=struct.unpack_from("<II",blob,off)
        off+=8
        if clen%4 or off+clen>len(blob):
            raise ValueError("invalid GLB chunk boundary")
        chunks.append((ctype,blob[off:off+clen]))
        off+=clen
    if not chunks or chunks[0][0]!=0x4E4F534A:
        raise ValueError("GLB missing JSON")
    data=json.loads(chunks[0][1].decode("utf-8"))
    bins=[c for t,c in chunks if t==0x004E4942]
    if len(bins)>1:
        raise ValueError("multiple binary chunks unsupported")
    return data,bins[0] if bins else b""


def add_animation(data: dict, binary: bytearray, anim, *, label: str):
    skin_joints=set()
    for skin in data.get("skins",[]):
        skin_joints.update(skin.get("joints",[]))
    if not skin_joints:
        raise ValueError("cannot animate GLB without skin joints")
    if len(data.get("buffers",[]))!=1:
        raise ValueError("expected single internal GLB buffer")
    names={data["nodes"][i].get("name","").casefold():i for i in skin_joints}
    gltf_anim={"name":label,"samplers":[],"channels":[]}
    hits=Counter()
    duration=anim.frame_count/anim.fps
    accessors=data.setdefault("accessors",[])
    views=data.setdefault("bufferViews",[])

    def append_accessor(values: list[tuple], *, atype: str):
        if not values:
            raise ValueError("empty animation samples")
        vector_size=len(values[0])
        if any(len(v)!=vector_size for v in values):
            raise ValueError("inconsistent vector dimensions")
        offset=len(binary)
        flattened=[float(x) for row in values for x in row]
        raw=struct.pack("<"+str(len(flattened))+"f", *flattened)
        binary.extend(align4(raw))
        view_id=len(views)
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(raw)})
        acc_id=len(accessors)
        rec={"bufferView":view_id,"componentType":5126,"count":len(values),"type":atype}
        if atype=="SCALAR":
            rec["min"]=[min(flattened)]
            rec["max"]=[max(flattened)]
        accessors.append(rec)
        return acc_id

    for bone in anim.bones:
        node=names.get(bone.name.casefold())
        if node is None:
            continue
        hits["matched_bones"]+=1
        for prop, track, typ in (("rotation",bone.rotations,"VEC4"),
                                 ("translation",bone.translations,"VEC3")):
            if track is None:
                continue
            if len(track.indices)!=len(track.values):
                raise ValueError("unequal keyframe sizes")
            if any(i < 0 or i > anim.frame_count + 1 for i in track.indices):
                raise ValueError("time index out of frame range")
            if any(a>=b for a,b in zip(track.indices,track.indices[1:])):
                raise ValueError("non-increasing frame indices")
            times=[(max(0,i)/anim.fps,) for i in track.indices]
            times_acc=append_accessor(times,atype="SCALAR")
            value_acc=append_accessor(track.values,atype=typ)
            index=len(gltf_anim["samplers"])
            gltf_anim["samplers"].append({
                "input":times_acc,"output":value_acc,"interpolation":"LINEAR"})
            gltf_anim["channels"].append({
                "sampler":index,"target":{"node":node,"path":prop}})
            hits[prop+"_channels"]+=1
    if gltf_anim["channels"]:
        data.setdefault("animations",[]).append(gltf_anim)
    hits["channels"]=len(gltf_anim["channels"])
    hits["bone_tracks_in_xanim"]=len(anim.bones)
    hits["anim_duration_seconds"]=round(duration,4)
    return dict(hits)


def write_glb(path: Path, doc: dict, binary: bytearray):
    if len(doc.get("buffers",[]))!=1:
        raise ValueError("expected one glb buffer")
    doc["buffers"][0]["byteLength"]=len(binary)
    encoded=align4(json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode("utf-8"))
    # JSON padding must be spaces, not NULs.
    encoded=encoded.rstrip(b"\x00")+b" "*((-len(encoded.rstrip(b"\x00")))%4)
    b=align4(bytes(binary))
    total=12+8+len(encoded)+8+len(b)
    if total>200*1024*1024:
        raise ValueError("animated GLB exceeds safety budget")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("wb") as f:
        f.write(struct.pack("<4sII",b"glTF",2,total))
        f.write(struct.pack("<II",len(encoded),0x4E4F534A));f.write(encoded)
        f.write(struct.pack("<II",len(b),0x004E4942));f.write(b)


def attach(model_path: Path, tracks: dict[str,Path], target: Path):
    doc, raw=read_glb(model_path)
    buf=bytearray(raw)
    original=len(doc.get("animations",[]))
    rec={}
    for name,p in sorted(tracks.items()):
        track=load_xanim(p)
        rec[name]=add_animation(doc,buf,track,label=name)
    write_glb(target,doc,buf)
    check_doc,_=read_glb(target)
    names=[a.get("name") for a in check_doc.get("animations",[])]
    if not all(name in names for name in tracks):
        raise ValueError("animation missing from written GLB")
    if any(meta["channels"]==0 for meta in rec.values()):
        raise ValueError("no matching animation channels")
    return {"base_model":model_path.name,"animation_names":names[original:],
            "tracks":rec,"glb_animated":True,
            "animations_validated_in_godot":False,
            "animation_pose_verified":False,
            "retargeting_warning":"Raw XANIM joints matched by name; local-vs-global and rest-pose not calibrated."}


if __name__=="__main__":
    if len(sys.argv)<5 or (len(sys.argv)-3)%2:
        raise SystemExit("usage: iw3_gltf_animation_bridge.py BASE.glb DEST.glb LABEL XANIM [LABEL XANIM...]")
    base,dest=map(Path,sys.argv[1:3])
    routes={sys.argv[i]:Path(sys.argv[i+1]) for i in range(3,len(sys.argv),2)}
    info=attach(base,routes,dest)
    print(json.dumps({"created":True,"tracks":info["tracks"],
                      "animated_godot":False,"pose_verified":False}))
