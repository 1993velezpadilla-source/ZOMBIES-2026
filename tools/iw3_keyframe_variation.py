#!/usr/bin/env python3
"""Check whether imported original IW3 action GLBs contain changing keyframe data.

Records ONLY counts and numeric difference magnitudes; not animation values.
"""
from __future__ import annotations
import json
from pathlib import Path
import math
import struct
import sys

from iw3_gltf_animation_bridge import read_glb
from iw3_weapon_probe import atomic_json


def accessor_data(doc: dict, binary: bytes, accessor_index: int) -> list[tuple]:
    accessor=doc["accessors"][accessor_index]
    if accessor["componentType"] != 5126:
        raise ValueError("expected floating-point keyframe accessor")
    comps={"SCALAR":1,"VEC3":3,"VEC4":4}[accessor["type"]]
    n=accessor["count"]
    if n < 0 or n > 100000:
        raise ValueError("suspicious accessor count")
    view=doc["bufferViews"][accessor["bufferView"]]
    offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
    stride=view.get("byteStride",4*comps)
    if stride < 4*comps or offset+(n-1)*stride+4*comps > len(binary):
        raise ValueError("invalid accessor region")
    return [struct.unpack_from("<"+("f"*comps),binary,offset+i*stride) for i in range(n)]


def analyze_glb(path: Path) -> dict:
    doc,binary=read_glb(path)
    result={}
    for anim in doc.get("animations",[]):
        channels=anim.get("channels",[])
        stats={"channels":len(channels),"keys_total":0,
               "channels_with_2_keys":0,"channels_with_different_values":0,
               "max_value_delta":0.0,"max_key_count":0,
               "distinct_sample_times":0,"bone_target_channels":len(channels)}
        samples=[]
        for channel in channels:
            samp=anim["samplers"][channel["sampler"]]
            t=accessor_data(doc,binary,samp["input"])
            v=accessor_data(doc,binary,samp["output"])
            if len(t)!=len(v):
                raise ValueError("keyframe time/value mismatch")
            n=len(v)
            stats["keys_total"]+=n
            stats["max_key_count"]=max(stats["max_key_count"],n)
            stats["channels_with_2_keys"]+=int(n>=2)
            if n>0:
                first=v[0]
                magnitude=max(math.dist(first,current) for current in v)
                if not math.isfinite(magnitude):
                    raise ValueError("nonfinite animation")
                stats["max_value_delta"]=round(max(stats["max_value_delta"],magnitude),6)
                if magnitude>0.0001:
                    stats["channels_with_different_values"]+=1
                samples.extend(x[0] for x in t)
        stats["distinct_sample_times"]=len(set(round(x,6) for x in samples))
        result[anim.get("name","?")]=stats
    return result


def run(folder: Path) -> dict:
    glbs=sorted(folder.glob("*_animated_experimental.glb"))
    output={"total_glbs":len(glbs),"glbs":{},
            "claim_of_correct_visual_motion":False}
    for file in glbs:
        output["glbs"][file.stem]=analyze_glb(file)
    output["total_nonconstant_channels"]=sum(
        a["channels_with_different_values"] for g in output["glbs"].values() for a in g.values())
    output["conclusion"]=("A glTF keyframe delta does not mean Godot applied that track to the "
                          "intended Skeleton3D. Bone pose evidence must be checked separately.")
    return output


if __name__=="__main__":
    folder=Path(sys.argv[1] if len(sys.argv)>1 else "_iw3_private/animated_preview")
    dest=Path(sys.argv[2] if len(sys.argv)>2 else "_iw3_reports/keyframe-variation.json")
    result=run(folder)
    atomic_json(dest,result)
    print("IW3_RAW_CHANNEL_VARIATION:",json.dumps({"total_glbs":result["total_glbs"],
          "total_nonconstant_channels":result["total_nonconstant_channels"],
          "by_model":{name:{action:{"keys":stats["keys_total"],
                                  "nonconstant":stats["channels_with_different_values"],
                                  "max_delta":stats["max_value_delta"]}
                            for action,stats in actions.items()}
                      for name,actions in result["glbs"].items()}}))
