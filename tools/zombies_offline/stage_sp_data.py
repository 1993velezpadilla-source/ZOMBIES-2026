#!/usr/bin/env python3
"""Stage minimum provided COD4 SP data only inside a disposable test directory.

The data input is the *existing owner-provided* archive stored in four
release parts. The script never stages original executables/DLLs and never
uploads or publishes COD4 assets. The output is a metadata-only report.
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
# Source archive inventory verifies these files; SP killhouse is the original
# tutorial mission. These data are solely an INPUT for the ephemeral smoke test,
# never a legal replacement for authoring our own room and weapon content.
REQUIRED_SP = (
    "localization.txt",
    *tuple(f"main/iw_{i:02}.iwd" for i in range(14)),
    "main/localized_spanish_iw00.iwd",
    "zone/spanish/code_post_gfx.ff",
    "zone/spanish/common.ff",
    "zone/spanish/ui.ff",
    "zone/spanish/killhouse.ff",
)
ALLOWED = {".txt", ".iwd", ".ff"}


def stage_from_reader(archive, destination: Path, required=REQUIRED_SP) -> dict:
    """Archive object needs only seek/read. Supports tiny in-memory test ZIPs."""
    destination.mkdir(parents=True, exist_ok=True)
    selected = []
    seen = set()
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        missing = [name for name in required if PREFIX + name not in names]
        if missing:
            raise ValueError("Missing required SP data: " + ", ".join(missing))
        for name in required:
            relative = Path(name)
            if (
                relative.is_absolute() or ".." in relative.parts
                or "\\" in name or relative.suffix.lower() not in ALLOWED
                or name in seen
            ):
                raise ValueError("Unsafe/duplicate archive path: " + name)
            seen.add(name)
            info = zf.getinfo(PREFIX + name)
            if info.flag_bits & 1 or info.is_dir():
                raise ValueError("Encrypted or directory entry not supported: " + name)
            output_path = destination / relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with zf.open(info, "r") as src, output_path.open("wb") as dst:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    digest.update(chunk)
                    dst.write(chunk)
            if output_path.stat().st_size != info.file_size:
                raise ValueError("Extracted length mismatch: " + name)
            selected.append({"path": name, "bytes": info.file_size,
                             "sha256": digest.hexdigest()})
    return {
        "purpose": "ephemeral offline single-player level-load diagnostic",
        "game": "ZOMBIES-2026 source-built KisakCOD-sp with input user archive",
        "test_level": "killhouse",
        "original_cod4_executables_copied": False,
        "gameplay_verified": False,
        "first_zombie_verified": False,
        "file_count": len(selected),
        "total_bytes": sum(row["bytes"] for row in selected),
        "files": selected,
        "game_data_in_artifacts": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--parts-dir", type=Path, required=True)
    cli.add_argument("--dest", type=Path, required=True)
    cli.add_argument("--report", type=Path, required=True)
    args = cli.parse_args()
    parts = sorted(args.parts_dir.glob("C4-Mocs.zip.part-*"))
    expected = [f"C4-Mocs.zip.part-{i:03}" for i in range(4)]
    if [x.name for x in parts] != expected:
        raise SystemExit("Expected exactly four canonical owner-supplied ZIP parts")
    if any(x.is_symlink() for x in parts):
        raise SystemExit("Symlink archive input refused")
    if sum(x.stat().st_size for x in parts) != SOURCE_ZIP_BYTES:
        raise SystemExit("Original archive byte length mismatch")
    reader = SplitReader(parts)
    try:
        result = stage_from_reader(reader, args.dest)
    finally:
        reader.close()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Z2026_OFFLINE_SP_STAGE " + json.dumps({
        "level": result["test_level"], "count": result["file_count"],
        "bytes": result["total_bytes"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
