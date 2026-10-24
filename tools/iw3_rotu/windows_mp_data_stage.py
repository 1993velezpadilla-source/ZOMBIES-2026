#!/usr/bin/env python3
"""Stage a narrow, disposable COD4 multiplayer data subset for a server boot probe.

Requires already-provided game files in an existing local split ZIP. Does NOT
publish, change, redistribute, or execute original Windows game executables.
Only KisakCOD source-built server may be launched by the separate CI step.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_releases import SplitReader, SOURCE_ZIP_BYTES

PREFIX = "Call of Duty 4 Modern Warfare/"
REQUIRED = (
    "localization.txt",
    "main/iw_00.iwd",
    "main/iw_01.iwd",
    "main/iw_02.iwd",
    "main/iw_03.iwd",
    "main/iw_04.iwd",
    "main/localized_spanish_iw00.iwd",
    "zone/spanish/code_post_gfx_mp.ff",
    "zone/spanish/localized_code_post_gfx_mp.ff",
    "zone/spanish/localized_common_mp.ff",
    "zone/spanish/common_mp.ff",
    "zone/spanish/ui_mp.ff",
    "zone/spanish/mp_crash.ff",
    "zone/spanish/mp_crash_load.ff",
)
# Explicit extension whitelist. Never stage source .exe, .dll, .bat or config.
ALLOWED = {".txt", ".iwd", ".ff"}


def stage_from_zip(parts: list[Path], destination: Path, required=REQUIRED) -> dict:
    if not parts:
        raise ValueError("Missing ZIP parts")
    if any(p.is_symlink() for p in parts):
        raise ValueError("Symlink archive pieces are disallowed")
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    reader = SplitReader(parts)
    try:
        with zipfile.ZipFile(reader) as z:
            names = set(z.namelist())
            missing = [p for p in required if PREFIX + p not in names]
            if missing:
                raise ValueError("Missing required original MP files: " + ", ".join(missing))
            for rel in required:
                relative = Path(rel)
                if relative.is_absolute() or ".." in relative.parts or relative.suffix.lower() not in ALLOWED:
                    raise ValueError("Refusing unsafe or executable path " + rel)
                info = z.getinfo(PREFIX + rel)
                if info.flag_bits & 1:
                    raise ValueError("Unexpected encrypted data " + rel)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with z.open(info, "r") as src, target.open("wb") as output:
                    while True:
                        block = src.read(1024 * 1024)
                        if not block:
                            break
                        digest.update(block)
                        output.write(block)
                if target.stat().st_size != info.file_size:
                    raise ValueError("File length mismatch: " + rel)
                rows.append({"path": rel, "bytes": info.file_size, "sha256": digest.hexdigest()})
                print("STAGED_MP_DATA", rel, info.file_size, flush=True)
    finally:
        reader.close()
    return {
        "mode": "restricted offline multiplayer server boot diagnostic",
        "source_archive_whole_installation": False,
        "selected_files": rows,
        "selected_total_bytes": sum(row["bytes"] for row in rows),
        "mp_level": "mp_crash",
        "raw_game_assets_in_artifact": False,
        "gameplay_verified": False,
        "zombies_verified": False,
        "limitations": "Only a narrow subset is staged. A failed map load may be due to incomplete original content.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    parts = sorted(args.parts_dir.glob("C4-Mocs.zip.part-*"))
    if len(parts) != 4 or [x.name for x in parts] != [f"C4-Mocs.zip.part-{i:03d}" for i in range(4)]:
        raise SystemExit("Expected exactly four canonical archive parts")
    if sum(x.stat().st_size for x in parts) != SOURCE_ZIP_BYTES:
        raise SystemExit("Archive length mismatch")
    report = stage_from_zip(parts, args.dest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("STAGING_RESULT",json.dumps({"count":len(report["selected_files"]),"bytes":report["selected_total_bytes"]}),flush=True)


if __name__ == "__main__":
    main()
