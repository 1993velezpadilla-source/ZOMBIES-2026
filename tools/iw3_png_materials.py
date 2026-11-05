#!/usr/bin/env python3
"""Convert temporary IW3 OAT DDS textures to portable PNG and repoint GLB URIs.

Game binaries/textures remain inside ignored CI staging; only metadata JSON
may be uploaded. Pillow decodes DDS compression and validates image data.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

from iw3_gltf_animation_bridge import read_glb, write_glb
from iw3_weapon_probe import atomic_json

try:
    from PIL import Image
except ImportError:
    Image = None


def convert(source: Path, weapons: Path) -> dict:
    if Image is None:
        raise RuntimeError("Pillow missing: install into isolated CI deps first")
    report={"required":0,"converted":0,"conversion_failures":[],
            "rewritten_glbs":0,"glb_image_references":0,
            "missing_png":[],"verified_material_import":False}
    for glb in sorted(weapons.glob("*_animated_experimental.glb")):
        doc,buf=read_glb(glb)
        changed=False
        for image in doc.get("images",[]):
            uri=image.get("uri","")
            if not uri.startswith("../images/") or not uri.endswith(".dds"):
                continue
            name=Path(uri).name
            if "/" in name or ".." in name:
                raise ValueError("unsafe image URI")
            report["glb_image_references"]+=1
            image["uri"]="../images/"+name[:-4]+".png"
            changed=True
        if changed:
            write_glb(glb,doc,bytearray(buf))
            report["rewritten_glbs"]+=1
    needed={Path(uri.get("uri","")).name for glb in weapons.glob("*_animated_experimental.glb")
            for uri in read_glb(glb)[0].get("images",[])
            if uri.get("uri","").endswith(".png")}
    report["required"]=len(needed)
    for filename in sorted(needed):
        original=source/(filename[:-4]+".dds")
        output=source/filename
        if not original.is_file():
            report["missing_png"].append(filename)
            continue
        try:
            with Image.open(original) as src:
                src.load()
                if src.width>8192 or src.height>8192 or not src.width or not src.height:
                    raise ValueError("unexpected texture dimensions")
                src.convert("RGBA").save(output,format="PNG",optimize=False)
            with Image.open(output) as check:
                check.verify()
            report["converted"]+=1
        except (ValueError,OSError,RuntimeError) as exc:
            report["conversion_failures"].append({"name":filename,"error":str(exc)[:160]})
    report["all_png_available"]=(report["required"]==report["converted"]
                                 and not report["conversion_failures"]
                                 and not report["missing_png"])
    report["note"]="PNG validity is separate from correct original UVs, material PBR, or visible poses."
    return report


if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: iw3_png_materials.py IMAGES_DIR TEMP_GLBS OUTPUT_JSON")
    result=convert(Path(sys.argv[1]),Path(sys.argv[2]))
    atomic_json(Path(sys.argv[3]),result)
    print("IW3_PNG_MATERIAL_GATE:",json.dumps(result))
    if not result["all_png_available"]:
        raise SystemExit(1)
