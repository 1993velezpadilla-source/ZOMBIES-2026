#!/usr/bin/env python3
"""Private 3-weapon animated GLB build gate, metadata only.

For each rifle, find best first-person model/4 matching XANIM animations and
build a scratch GLB with channels. This is STRUCTURAL PROOF, not rendered poses.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
from iw3_gltf_animation_bridge import attach, read_glb
from iw3_xanim_v17 import load_xanim
from iw3_weapon_probe import atomic_json

GUNS={"m4":re.compile(r"^viewmodel_m4(?:_|$)"),
      "ak47":re.compile(r"^viewmodel_ak47(?:_|$)"),
      "mp5":re.compile(r"^viewmodel_mp5(?:_|$)")}
ACTIONS={"idle":re.compile(r"(?:^|_)idle(?:_|$)"),
         "ads":re.compile(r"(?:^|_)ads(?:_|$)"),
         "fire":re.compile(r"(?:^|_)fire(?:_|$)"),
         "reload":re.compile(r"(?:^|_)reload(?:_|$)")}


def run(root:Path, destination:Path):
    source=root/"common_mp"
    all_glbs=[p for p in (source/"model_export").glob("*.glb") if re.search(r"_lod0\.glb$",p.name)]
    all_anims=[p for p in (source/"xanim").iterdir() if p.is_file()]
    report={"guns":{}, "ready_for_gameplay":False, "pose_validated":False}
    for gun,pat in GUNS.items():
        models=[p for p in all_glbs if pat.match(p.stem)]
        anims=[p for p in all_anims if pat.match(p.name)]
        picked={}
        for action,rx in ACTIONS.items():
            possibles=[a for a in anims if rx.search(a.name)]
            if not possibles:
                continue
            # Prefer vanilla animations over scoped/silencer variants.
            possibles.sort(key=lambda p:(len(p.name),p.name))
            picked[action]=possibles[0]
        models.sort(key=lambda m:(len(m.name),m.name))
        rec={"source_models":len(models), "source_anims":len(anims),
             "found_actions":sorted(picked),"selected_model":models[0].name if models else None}
        if len(picked)==4 and models:
            try:
                selected=models[0]
                target=destination/f"{gun}_animated_experimental.glb"
                result=attach(selected,picked,target)
                rec["gltf"]=result
                doc,_=read_glb(target)
                rec["glb_import_ready_structure"]=len(doc.get("animations",[]))>=4 and all(
                    len(a["channels"])>0 for a in doc["animations"])
                rec["output_size_bytes"]=target.stat().st_size
                rec["base_image_uris"]=len(doc.get("images",[]))
            except (ValueError, OSError, KeyError) as err:
                rec["error"]=str(err)[:300]
        report["guns"][gun]=rec
    report["structural_proof_count"]=sum(x.get("glb_import_ready_structure",False)
                                          for x in report["guns"].values())
    return report


if __name__=="__main__":
    src=Path(sys.argv[1] if len(sys.argv)>1 else "_iw3_private/dumps")
    out=Path(sys.argv[2] if len(sys.argv)>2 else "_iw3_private/animated_preview")
    dest=Path(sys.argv[3] if len(sys.argv)>3 else "_iw3_reports/animated-glb-gate.json")
    r=run(src,out)
    atomic_json(dest,r)
    print(json.dumps({"structural_proof_count":r["structural_proof_count"],
                      "guns":{g:{"actions":o["found_actions"],"model":o["selected_model"],
                                 "ready":o.get("glb_import_ready_structure",False),
                                 "channels":{k:v["channels"] for k,v in o.get("gltf",{}).get("tracks",{}).items()},
                                 "error":o.get("error")}
                              for g,o in r["guns"].items()}}))
