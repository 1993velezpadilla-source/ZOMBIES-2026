#!/usr/bin/env python3
"""Stage only referenced weapon DDS textures from COD4 user's temporary IWDs.

Never stores/returns binary game textures outside the ignored runner scratch
folders. Reports names/counts only, not pixel data.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from iw3_gltf_animation_bridge import read_glb
from iw3_weapon_probe import atomic_json


def collect_required(preview_folder:Path):
    required=set()
    for file in preview_folder.glob("*_animated_experimental.glb"):
        doc,_=read_glb(file)
        for image in doc.get("images",[]):
            uri=image.get("uri","")
            if not uri: continue
            # Strictly ASCII filename; no path traversal or arbitrary IO.
            basename=Path(uri).name
            if basename.endswith(".dds") and basename == uri.rsplit("/",1)[-1] and ".." not in basename:
                required.add(basename)
    return required


def gather(previews:Path, staging:Path, target:Path, converter:Path) -> dict:
    needed=collect_required(previews)
    target.mkdir(parents=True,exist_ok=True)
    matched_dds=set()
    for zone in ("common_mp","mp_crash"):
        images=staging/"dumps"/zone/"images"
        for filename in needed:
            src=images/filename
            if src.is_file():
                shutil.copy2(src,target/filename)
                matched_dds.add(filename)
    supplied_by_iwd=set()
    notfound=needed-matched_dds
    for iwd in ("iw_02.iwd","iw_03.iwd"):
        archive=staging/"main"/iwd
        if not archive.exists():continue
        with zipfile.ZipFile(archive) as z:
            keys={x.filename.lower():x for x in z.infolist() if not x.is_dir()}
            for wanted in sorted(notfound):
                member=keys.get("images/"+wanted[:-4].lower()+".iwi")
                if not member or member.file_size>16*1024*1024:
                    continue
                iwi_path=target/(wanted[:-4]+".iwi")
                with z.open(member) as src, iwi_path.open("wb") as out:
                    shutil.copyfileobj(src,out)
                if converter.is_file():
                    proc=subprocess.run([str(converter),"--no-color",str(iwi_path)],
                                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
                    if proc.returncode==0 and (target/wanted).is_file():
                        supplied_by_iwd.add(wanted)
                iwi_path.unlink(missing_ok=True)
            notfound=needed-matched_dds-supplied_by_iwd
            if not notfound:break
    found={n for n in needed if (target/n).is_file()}
    return {"required_images":len(needed),
            "found_images":len(found),
            "converted_from_iwd":len(supplied_by_iwd),
            "existing_dds":len(matched_dds),
            "missing_images":sorted(needed-found),
            "all_dependencies_available":not (needed-found),
            "rights":"No texture files emitted as repository files or GH Actions artifacts."}


if __name__=="__main__":
    root=Path(sys.argv[1] if len(sys.argv)>1 else "_iw3_private")
    converter=Path(sys.argv[2] if len(sys.argv)>2 else "_oat/ImageConverter")
    report_path=Path(sys.argv[3] if len(sys.argv)>3 else "_iw3_reports/texture-gate.json")
    result=gather(root/"animated_preview",root,root/"godot_sandbox"/"images",converter)
    atomic_json(report_path,result)
    print(json.dumps(result))
