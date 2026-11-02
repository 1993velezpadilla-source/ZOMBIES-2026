#!/usr/bin/env python3
"""Assemble a PRIVATE Godot IW3 FPS laboratory on the owner's computer.

This tool does not download or redistribute COD4. It reads files that must
already have been produced locally by the IW3 extraction/animation pipeline.
All proprietary game content stays in an ignored local directory. Do not
upload the resulting project or export it publicly without authorization.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys

from iw3_gltf_animation_bridge import read_glb

GUNS=("m4","ak47","mp5")
TOOLS = {
    "iw3_fps_weapon_mount.gd": "weapon_mount.gd",
    "iw3_fps_weapon_controller.gd": "fps_controller.gd",
    "iw3_fps_playground.gd": "playground.gd",
    "iw3_fps_playground.tscn": "playground.tscn",
}
PROJECT='''config_version=5
[application]
config/name="IW3 Private FPS Lab — Not for Distribution"
run/main_scene="res://playground.tscn"
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'''

def assemble(root: Path, output: Path, tools: Path) -> dict:
    previews=root/"animated_preview"
    images=root/"godot_sandbox"/"images"
    expected=[]
    required_images=set()
    for gun in GUNS:
        for suffix in ("_animated_experimental.glb","_hands_animated_experimental.glb"):
            expected.append(gun+suffix)
    if not previews.is_dir() or not images.is_dir():
        raise ValueError("Missing local extracted / converted IW3 game data.")
    for filename in expected:
        p=previews/filename
        if not p.is_file():
            raise ValueError("Missing original locally converted weapon file: "+filename)
        data,_=read_glb(p)
        animations={a.get("name") for a in data.get("animations",[])}
        if not {"idle","ads","fire","reload"} <= animations:
            raise ValueError("Missing required 4 animations: "+filename)
        for entry in data.get("images",[]):
            uri=entry.get("uri","")
            if not uri.startswith("../images/") or not uri.endswith(".png"):
                raise ValueError("Unsafe or non-PNG image reference: "+uri)
            name=uri.rsplit("/",1)[-1]
            if not name or name.startswith(".") or ".." in name:
                raise ValueError("Invalid image reference")
            required_images.add(name)
    for name in required_images:
        if not (images/name).is_file():
            raise ValueError("Missing locally decoded source texture: "+name)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite an existing private Godot project: "+str(output))
    (output/"weapons").mkdir(parents=True,exist_ok=True)
    (output/"images").mkdir(parents=True,exist_ok=True)
    for filename in expected:
        shutil.copy2(previews/filename, output/"weapons"/filename)
    for filename in sorted(required_images):
        shutil.copy2(images/filename,output/"images"/filename)
    for source,name in TOOLS.items():
        shutil.copy2(tools/source,output/name)
    (output/"project.godot").write_text(PROJECT)
    report={"offline_private_project":str(output.resolve()),
            "original_weapon_glbs":len(expected),"png_textures":len(required_images),
            "godot_scene":"res://playground.tscn",
            "requires_user_to_supply_owned_original_assets":True,
            "android_apk_created":False,"commercial_distribution_authorized":False}
    return report

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root",type=Path,default=Path("_iw3_private"))
    parser.add_argument("--output",type=Path,default=Path("_iw3_private/fps_lab"))
    parser.add_argument("--scripts",type=Path,default=Path("tools"))
    args=parser.parse_args()
    try:
        result=assemble(args.private_root,args.output,args.scripts)
    except (ValueError,FileExistsError,FileNotFoundError,OSError) as exc:
        print("PRIVATE FPS LAB FAILED:",str(exc),file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
