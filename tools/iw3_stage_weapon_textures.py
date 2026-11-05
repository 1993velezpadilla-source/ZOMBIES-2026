#!/usr/bin/env python3
"""Stage only referenced weapon DDS textures from COD4 user's temporary IWDs.

Never stores/returns binary game textures outside the ignored runner scratch
folders. Reports names/counts only, not pixel data.
"""
from __future__ import annotations
import json
import difflib
import tempfile
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from iw3_gltf_animation_bridge import read_glb
from iw3_weapon_probe import atomic_json
from audit_releases import SplitReader, SOURCE_ZIP_BYTES


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
    # Source IWDs are spread across the complete original COD4 ZIP. Lookup
    # exact filenames in the already published index to avoid opening all
    # 22 IWD archives, but preserve strict source name provenance.
    suggestions={}
    index_file=Path("docs/audit/c4-iwd-file-inventory.json")
    parts=sorted(Path("_release_assets/c4").glob("C4-Mocs.zip.part-*"))
    indexed={}
    if index_file.is_file():
        for row in json.loads(index_file.read_text()):
            location=row["path"]
            if location.lower().startswith("images/") and location.lower().endswith(".iwi"):
                indexed.setdefault(Path(location).stem.lower(),[]).append((row["container"],location))
    if len(parts)==4 and sum(p.stat().st_size for p in parts)==SOURCE_ZIP_BYTES:
        matches={}
        for wanted in sorted(needed-matched_dds-supplied_by_iwd):
            stem=Path(wanted).stem.lower()
            candidates=[stem,"mtl_"+stem]
            # Plain _c texture may use IW3's more descriptive _col suffix.
            if stem.endswith("_c"):
                candidates += [stem[:-2]+"_col","mtl_"+stem[:-2]+"_col"]
            hits=[loc for candidate in candidates for loc in indexed.get(candidate,[])]
            if hits:
                matches[wanted]=hits[0]
            else:
                near=difflib.get_close_matches(stem,indexed.keys(),n=3,cutoff=0.55)
                suggestions[wanted]=near
        group={}
        for wanted,(container,inner) in matches.items():
            group.setdefault(container,[]).append((wanted,inner))
        reader=SplitReader(parts)
        try:
            with zipfile.ZipFile(reader) as outer:
                for container, requests in group.items():
                    info=outer.getinfo(container)
                    with tempfile.TemporaryFile() as f:
                        with outer.open(info) as stream:
                            shutil.copyfileobj(stream,f,length=4*1024*1024)
                        f.seek(0)
                        with zipfile.ZipFile(f) as nested:
                            for wanted,inner in requests:
                                member=nested.getinfo(inner)
                                if member.file_size>16*1024*1024:
                                    continue
                                iwi_file=target/(wanted[:-4]+".iwi")
                                with nested.open(member) as source, iwi_file.open("wb") as dest:
                                    shutil.copyfileobj(source,dest)
                                if converter.is_file():
                                    proc=subprocess.run([str(converter),"--no-color",str(iwi_file)],
                                                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                                        timeout=30,check=False)
                                    if proc.returncode==0 and (target/wanted).is_file():
                                        supplied_by_iwd.add(wanted)
                                iwi_file.unlink(missing_ok=True)
        finally:
            reader.close()
    found={n for n in needed if (target/n).is_file()}
    return {"required_images":len(needed),
            "found_images":len(found),
            "converted_from_iwd":len(supplied_by_iwd),
            "existing_dds":len(matched_dds),
            "missing_images":sorted(needed-found),
            "image_index_suggestions":{k:v for k,v in suggestions.items() if k in needed-found},
            "all_dependencies_available":not (needed-found),
            "rights":"No texture files emitted as repository files or GH Actions artifacts."}


if __name__=="__main__":
    root=Path(sys.argv[1] if len(sys.argv)>1 else "_iw3_private")
    converter=Path(sys.argv[2] if len(sys.argv)>2 else "_oat/ImageConverter")
    report_path=Path(sys.argv[3] if len(sys.argv)>3 else "_iw3_reports/texture-gate.json")
    result=gather(root/"animated_preview",root,root/"godot_sandbox"/"images",converter)
    atomic_json(report_path,result)
    print(json.dumps(result))
