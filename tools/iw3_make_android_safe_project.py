#!/usr/bin/env python3
"""Create a self-contained, legal-to-share Godot Android FPS APK source project.

Only handmade procedural placeholder geometry and GDScript are bundled.
No XMODEL/XANIM/IWI/DDS/GLB/COD4 graphics, samples or textures are included.
Does NOT make an APK; GitHub Actions later exports debug APK.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import shutil
import sys

SCRIPTS = {
    "iw3_fps_playground.gd": "playground.gd",
    "iw3_fps_weapon_mount.gd": "weapon_mount.gd",
    "iw3_fps_weapon_controller.gd": "fps_controller.gd",
    "iw3_fps_android_safe.gd": "android_safe.gd",
    "iw3_fps_android_safe.tscn": "android_safe.tscn",
}
PROJECT = """config_version=5

[application]
config/name="ZOMBIES FPS LAB - SAFE"
run/main_scene="res://android_safe.tscn"
config/description="Original FPS test chamber with geometric placeholder weapons. No COD4 assets."

[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/handheld/orientation=0
window/stretch/mode="canvas_items"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/vram_compression/import_etc2_astc=true

[input_devices]
pointing/emulate_mouse_from_touch=true
"""
EXPORT = """[preset.0]

name="Android"
platform="Android"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/ZOMBIES_FPS_LAB_SAFE_ARM64.apk"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

gradle_build/use_gradle_build=false
architectures/armeabi-v7a=false
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
package/unique_name="org.xziellabs.zombiesfpssafe"
package/name="ZOMBIES FPS LAB SAFE"
package/signed=true
version/code=1
version/name="0.1.0-test"
screen/immersive_mode=true
permissions/internet=false
"""

FORBIDDEN_SUFFIXES={".glb",".iwi",".iwd",".ff",".dds",".xanim",".apk"}
FORBIDDEN_NAMES={"viewmodel_m4_mp_lod0.glb","viewmodel_mp5_mp_lod0.glb","viewmodel_ak47_mp_lod0.glb"}


def create(scripts:Path, target:Path)->dict:
    if not scripts.is_dir():
        raise ValueError("Cannot find scripts directory")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Will not overwrite existing build directory: "+str(target))
    for src in SCRIPTS:
        if not (scripts/src).is_file():
            raise FileNotFoundError("Missing safe Godot source: "+src)
    target.mkdir(parents=True,exist_ok=True)
    for src,dst in SCRIPTS.items():
        shutil.copy2(scripts/src,target/dst)
    (target/"project.godot").write_text(PROJECT)
    (target/"export_presets.cfg").write_text(EXPORT)
    (target/"build").mkdir(exist_ok=True)
    shipped=[str(p.relative_to(target)) for p in target.rglob("*") if p.is_file()]
    if any(Path(name).suffix.lower() in FORBIDDEN_SUFFIXES or Path(name).name in FORBIDDEN_NAMES for name in shipped):
        raise ValueError("Forbidden source assets in public-safe project")
    return {"files":sorted(shipped),
            "source_files":len(shipped),
            "original_game_assets":0,
            "procedural_art_only":True,
            "exports_to_android_ARM64_only":True,
            "tested_on_android_device":False,
            "apk_exists":False,
            "project_root":str(target)}


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scripts",type=Path,default=Path("tools"))
    p.add_argument("--output",type=Path,default=Path("_safe_android_fps"))
    args=p.parse_args()
    try:
        info=create(args.scripts,args.output)
    except (FileExistsError,FileNotFoundError,ValueError,OSError) as exc:
        print("SAFE_ANDROID_PROJECT_ERROR:",str(exc),file=sys.stderr)
        return 1
    print("SAFE_ANDROID_PROJECT:",json.dumps(info))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
