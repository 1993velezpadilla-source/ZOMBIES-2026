"""Verify the actual full Luanti Android APK embeds every admitted authentic model.

This is a binary evidence gate, not an Android FPS / ADS / gameplay sign-off.
Private original models never enter public GitHub source/artifacts.
"""
from __future__ import annotations
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZipFile, BadZipFile


def confirm(apk:Path, mod:Path, manifest:dict) -> dict:
    valid=manifest.get("native_model_ids")
    if not isinstance(valid,list) or not valid:
        raise ValueError("No actual source-derived models admitted")
    if len(valid)!=len(set(valid)) or len(valid)>28:
        raise ValueError("Contradictory native source model count")
    with ZipFile(apk) as outer:
        onames=outer.namelist()
        if len(onames)!=len(set(onames)):
            raise ValueError("APK duplicate ZIP entries")
        if "assets/assets.zip" not in onames or "AndroidManifest.xml" not in onames:
            raise ValueError("Not a Luanti APK with packed assets")
        if not any(n.startswith("lib/arm64-v8a/") and n.endswith(".so") for n in onames):
            raise ValueError("Native ARM64 library missing")
        with ZipFile(BytesIO(outer.read("assets/assets.zip"))) as nested:
            names=nested.namelist()
            if len(names)!=len(set(names)):
                raise ValueError("Duplicate nested Luanti assets")
            present=[]
            for weapon in valid:
                if not weapon.isidentifier() or not weapon.isascii():
                    raise ValueError("Invalid source weapon ID")
                for kind in ("gun","hands"):
                    filename=f"arsenal_{weapon}_{kind}.glb"
                    path=f"games/voxelibre/mods/arsenal/models/{filename}"
                    original=mod/"models"/filename
                    if path not in names or not original.is_file():
                        raise ValueError(f"Missing authentic {weapon} {kind} model")
                    info=nested.getinfo(path)
                    if info.file_size != original.stat().st_size or info.file_size>32*1024*1024:
                        raise ValueError(f"Corrupt/oversized original model {filename}")
                    data=nested.read(path)
                    if hashlib.sha256(data).digest()!=hashlib.sha256(original.read_bytes()).digest():
                        raise ValueError(f"Model APK byte mismatch for {filename}")
                    if len(data)<20 or data[:4]!=b"glTF":
                        raise ValueError("Invalid first-person model GLB header")
                    version,total=struct.unpack_from("<II",data,4)
                    if version!=2 or total!=len(data):
                        raise ValueError("Invalid GLB version/byte length")
                    n,kind_magic=struct.unpack_from("<I4s",data,12)
                    if kind_magic!=b"JSON" or n>len(data)-20:
                        raise ValueError("Invalid GLB JSON")
                    doc=json.loads(data[20:20+n].decode("utf-8"))
                    clips={a["name"] for a in doc.get("animations",[])
                           if a.get("name") and a.get("channels")}
                    if not {"idle","ads","fire","reload"} <= clips:
                        raise ValueError("Original animation clip channels absent "+filename)
                    if not doc.get("skins") or not doc.get("meshes"):
                        raise ValueError("Source model has no skin or mesh "+filename)
                    present.append(path)
            base="games/voxelibre/mods/arsenal/"
            for required in ["init.lua","mod.conf","arsenal_runtime.json",
                             "textures/arsenal_flat_metal.png",
                             "textures/arsenal_flat_hands.png"]:
                if base+required not in names:
                    raise ValueError("Missing runtime mod asset: "+required)
            runtime=json.loads(nested.read(base+"arsenal_runtime.json"))
            if runtime["native_model_ids"] != valid:
                raise ValueError("Bundled manifest differs from source verified runtime")
    return {
        "apk_name":apk.name,"sha256":hashlib.sha256(apk.read_bytes()).hexdigest(),
        "source_verified_native_weapon_pairs":len(valid),
        "genuine_glb_files_bytes_checked":len(present),
        "all_animation_clip_headers_checked":True,
        "private_mod_files_present":True,
        "actual_signed_apk_bytes_checked":True,
        "apksigner_cryptographic_signature_checked":False,
        "android_installation_verified":False,
        "iron_sights_alignment_verified":False,
        "audio_fidelity_verified":False,
        "runtime_fps_verified":False,
        "commercial_redistribution_cleared":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk",required=True,type=Path)
    p.add_argument("--private-mod",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    data=confirm(args.apk,args.private_mod,json.loads(args.manifest.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    print("REAL_COD4_ARSENAL_APK_BINARY_CONTENT_GATE",
          data["source_verified_native_weapon_pairs"],"models",
          data["genuine_glb_files_bytes_checked"],"GLBs verified",
          "DEVICE PLAYTEST: NOT YET")


if __name__=="__main__":
    main()
