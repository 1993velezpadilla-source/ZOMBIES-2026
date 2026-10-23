#!/usr/bin/env python3
"""Prepare a minimal, temporary compatibility fixture from the user-provided archive.

Works only inside a disposable GitHub Actions runner. Does not execute Windows
binaries, rewrite game data, or upload extracted game files as artifacts.
"""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from audit_releases import PARTS, SplitReader

PREFIX = "Call of Duty 4 Modern Warfare/"
REQUIRED = (
    "localization.txt",
    *("main/iw_%02d.iwd" % i for i in range(14)),
    "main/localized_spanish_iw00.iwd",
    "zone/spanish/code_post_gfx.ff",
    "zone/spanish/common.ff",
    "zone/spanish/ui.ff",
    "zone/spanish/killhouse.ff",
    "zone/spanish/cargoship.ff",
)
ROOT = Path("_runtime_temp/original-pc-sample")
RESULT = Path("smoke-out/real-data-test")
RESULT.mkdir(parents=True, exist_ok=True)

def main():
    if len(PARTS) != 4:
        raise SystemExit("Missing pieces of the original C4-Mocs archive")
    src = SplitReader(PARTS)
    records = []
    try:
        with zipfile.ZipFile(src, "r") as outer:
            for relative in REQUIRED:
                member = outer.getinfo(PREFIX + relative)
                target = ROOT / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                sha = hashlib.sha256()
                with outer.open(member, "r") as fh, target.open("wb") as out:
                    for data in iter(lambda: fh.read(4 * 1024 * 1024), b""):
                        out.write(data)
                        sha.update(data)
                if target.stat().st_size != member.file_size:
                    raise ValueError("Size mismatch " + relative)
                records.append({"path":relative, "bytes":member.file_size,"sha256":sha.hexdigest()})
                print("Verified temporary source asset:",relative,"bytes",member.file_size,flush=True)
    finally:
        src.close()
    summary={"original_pc_files":True,"complete_game_archive":False,"files":records,
             "gameplay_not_yet_verified":True,
             "upload_extracted_binaries":False}
    (RESULT/"source-files-manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("Temporary compatibility fixture ready:",len(records),"files",
          sum(x["bytes"] for x in records),"bytes",flush=True)
if __name__=="__main__":
    main()
