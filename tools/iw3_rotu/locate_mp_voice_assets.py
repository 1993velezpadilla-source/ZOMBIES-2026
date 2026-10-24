#!/usr/bin/env python3
"""Locate named UI/image resources inside the provided COD4 split ZIP's IWDs.

Filename metadata only: does not publish textures, sounds, GSC, or other assets.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_releases import SplitReader, SOURCE_ZIP_BYTES

NEEDLES=("loadscreen_mp_crash_snow", "loadscreen_mp_crash", "mp_crash_snow")
def locate(parts: list[Path], needles: tuple[str,...]=NEEDLES) -> dict:
    if not parts: raise ValueError("No split ZIP parts provided")
    matches=[]
    iwd_count=0
    reader=SplitReader(parts)
    try:
        with zipfile.ZipFile(reader) as outer:
            for ent in outer.infolist():
                if ent.is_dir() or not ent.filename.lower().endswith(".iwd"):continue
                iwd_count+=1
                with tempfile.TemporaryFile() as temp:
                    with outer.open(ent) as stream:
                        shutil.copyfileobj(stream,temp,length=8*1024*1024)
                    temp.seek(0)
                    with zipfile.ZipFile(temp) as inner:
                        for item in inner.infolist():
                            normalized=item.filename.replace("\\","/").lower()
                            if any(token in normalized for token in needles):
                                matches.append({"archive":ent.filename,"filename":item.filename,
                                    "uncompressed_bytes":item.file_size})
                print("IWD_METADATA_SEARCHED",iwd_count,ent.filename,flush=True)
    finally:
        reader.close()
    return {"scope":"Read-only IWD entry metadata search", "query_terms":needles,
        "containers_checked":iwd_count,"matches":matches,
        "raw_copyrighted_bytes_saved":False,
        "contains_original_game_assets":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parts-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    parts=sorted(args.parts_dir.glob("C4-Mocs.zip.part-*"))
    if len(parts)!=4 or sum(x.stat().st_size for x in parts)!=SOURCE_ZIP_BYTES:
        raise SystemExit("Original split ZIP pieces absent or length mismatch")
    result=locate(parts)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("ASSET_LOCATION_RESULT",json.dumps(result,ensure_ascii=False),flush=True)
if __name__=="__main__":
    main()
