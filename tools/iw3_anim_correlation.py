#!/usr/bin/env python3
"""Real COD4 IW3 track decode + glTF skeleton bone-name correlation gate.

Outputs diagnostics/metrics only. No XANIM, GLB or images enter repo artifacts.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import re
import struct
import sys

from iw3_xanim_v17 import load_xanim, AnimFormatError
from iw3_weapon_probe import atomic_json

GUNS = {
    "m4": re.compile(r"^viewmodel_m4(?:_|$)", re.I),
    "ak47": re.compile(r"^viewmodel_ak47(?:_|$)", re.I),
    "mp5": re.compile(r"^viewmodel_mp5(?:_|$)", re.I),
}
ACTIONS = ("idle", "ads", "fire", "reload")


def read_nodes(glb: Path) -> dict:
    with glb.open("rb") as f:
        header=f.read(20)
        if len(header)!=20:
            raise ValueError("short GLB")
        magic, ver, length, clen, ctype=struct.unpack("<4sIIII",header)
        if magic != b"glTF" or ver != 2 or length != glb.stat().st_size or clen > 32 * 1024 * 1024 or ctype!=0x4e4f534a:
            raise ValueError("invalid GLB header")
        data=json.loads(f.read(clen))
    joints = set()
    for skin in data.get("skins",[]):
        for index in skin.get("joints",[]):
            name=data["nodes"][index].get("name")
            if name:
                joints.add(name.casefold())
    return {"joints":joints, "all_nodes":len(data.get("nodes",[])),
            "skins":len(data.get("skins",[])), "animations":len(data.get("animations",[]))}


def analyze(dump: Path) -> dict:
    result={"zones":{},"decoded_count":0,"decode_errors":0,
            "decode_error_samples":[],"gun_tracks":{},
            "all_decoded_animations_in_glb": False,
            "full_godot_animation_working": False}
    by_gun={name: [] for name in GUNS}
    for zone in dump.iterdir():
        if not zone.is_dir() or not (zone / "xanim").exists():
            continue
        counts=Counter()
        for path in sorted((zone / "xanim").iterdir()):
            if not path.is_file(): continue
            try:
                anim=load_xanim(path)
                counts["decoded"]+=1
                result["decoded_count"]+=1
                if anim.delta_quat or anim.delta_trans:
                    counts["delta_tracks"]+=1
                if anim.notes:
                    counts["notetracks"]+=1
                for key,rex in GUNS.items():
                    if rex.search(path.name):
                        by_gun[key].append((zone, path, anim))
            except (AnimFormatError,ValueError,OSError,OverflowError,struct.error) as exc:
                counts["errors"]+=1
                result["decode_errors"]+=1
                if len(result["decode_error_samples"])<20:
                    result["decode_error_samples"].append({"name":path.name, "reason":str(exc)[:110]})
        result["zones"][zone.name]=dict(counts)
    for gun, animations in by_gun.items():
        examples = []
        output_guns=sorted(p for p in (dump/"common_mp"/"model_export").glob(f"viewmodel_{gun}*_lod0.glb") if p.is_file())
        if gun=="m4":
            output_guns=[p for p in output_guns if not p.name.startswith("viewmodel_m40")]
        meshes=[]
        for model in output_guns[:50]:
            try:
                nodes=read_nodes(model)
                meshes.append((model, nodes))
            except (OSError,ValueError,IndexError,KeyError,json.JSONDecodeError):
                pass
        actions=Counter()
        max_matches=0
        best=[]
        for zone, path, anim in animations:
            for action in ACTIONS:
                if re.search(r"(?:^|_)"+action+r"(?:_|$)",path.name):
                    actions[action]+=1
            names={b.name.casefold() for b in anim.bones}
            overlap=[]
            for model,node in meshes:
                match=names.intersection(node["joints"])
                if len(match)>max_matches:
                    max_matches=len(match)
                    best=[{"model":model.name,"anim":path.name,"common_bones":len(match),
                           "model_joint_count":len(node["joints"]),
                           "anim_bone_count":len(anim.bones),
                           "match_fraction":round(len(match)/max(1,len(node["joints"])),3)}]
                overlap.append(len(match))
            if len(examples)<15:
                examples.append({"name":path.name,"frames":anim.frame_count,"fps":anim.fps,
                                 "bone_tracks":len(anim.bones),
                                 "rotation_tracks":sum(b.rotations is not None for b in anim.bones),
                                 "translation_tracks":sum(b.translations is not None for b in anim.bones),
                                 "loop":anim.looping, "delta":bool(anim.delta_quat or anim.delta_trans),
                                 "best_joint_overlap":max(overlap,default=0)})
        result["gun_tracks"][gun]={"decoded":len(animations),
            "action_counts":dict(actions),"candidate_viewmodel_glbs":len(meshes),
            "max_model_bone_overlap":max_matches, "best_pair":best,
            "examples":examples}
    return result


if __name__=="__main__":
    src=Path(sys.argv[1] if len(sys.argv)>1 else "_iw3_private/dumps")
    dst=Path(sys.argv[2] if len(sys.argv)>2 else "_iw3_reports/bone-correlation.json")
    report=analyze(src)
    atomic_json(dst,report)
    print(json.dumps({
        "decoded":report["decoded_count"],"errors":report["decode_errors"],
        "error_examples":report["decode_error_samples"][:7],
        "guns":{key:{"decoded":value["decoded"],"best_overlap":value["max_model_bone_overlap"],
                     "candidates":value["candidate_viewmodel_glbs"],"best":value["best_pair"]}
                for key,value in report["gun_tracks"].items()}
    }))
