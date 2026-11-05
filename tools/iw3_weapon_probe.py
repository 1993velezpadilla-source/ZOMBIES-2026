#!/usr/bin/env python3
"""Bounded IW3 weapon extraction probe. Never publishes or commits game assets.

prepare: selectively stage user-supplied COD4 fastfiles/IWDs from the split ZIP.
probe: use OpenAssetTools Unlinker to inspect/extract, then report metadata ONLY.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

from audit_releases import SplitReader, SOURCE_ZIP_BYTES

ZIP_ROOT = "Call of Duty 4 Modern Warfare/"
ZONES = ("common_mp", "mp_crash", "common")
IWD_FILES = ("iw_02.iwd", "iw_03.iwd")
# Actual IW3 type names from OpenAssetTools src/Common/Game/IW3/GameIW3.cpp.
IW3_ASSET_TYPES = ("xmodel", "xanim", "weapon", "image", "material")
KEYWORDS = {
    "M4": re.compile(r"(?<![a-z0-9])(?:m4|m4a1|m4_carbine)(?![a-z0-9])", re.I),
    "AK-47": re.compile(r"(?:ak47|ak_47|ak-47)", re.I),
    "MP5": re.compile(r"(?<![a-z0-9])mp5(?:sd)?(?![a-z0-9])", re.I),
    "viewhands": re.compile(r"viewhand|view_hand|hand_(?:right|left)|hands_", re.I),
}
MAX_GLB_JSON = 32 * 1024 * 1024


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def zip_members_for(zones: list[str], iwds: bool) -> list[str]:
    members = [f"zone/spanish/{zone}.ff" for zone in zones]
    if iwds:
        members += [f"main/{name}" for name in IWD_FILES]
    return members


def stage_archive(parts_dir: Path, output: Path, zones: list[str], iwds: bool) -> dict:
    parts = sorted(parts_dir.glob("C4-Mocs.zip.part-*"))
    if len(parts) != 4 or sum(p.stat().st_size for p in parts) != SOURCE_ZIP_BYTES:
        raise ValueError("Missing/incorrect split COD4 release ZIP parts")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    reader = SplitReader(parts)
    try:
        with zipfile.ZipFile(reader) as archive:
            for relative in zip_members_for(zones, iwds):
                # Fixed allow-list; never extract arbitrary archive paths.
                member = archive.getinfo(ZIP_ROOT + relative)
                if member.is_dir() or member.file_size > 300 * 1024 * 1024:
                    raise ValueError("Unexpected member size or type: " + relative)
                dest = output / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                total = 0
                with archive.open(member) as src, dest.open("wb") as dst:
                    while chunk := src.read(4 * 1024 * 1024):
                        dst.write(chunk)
                        digest.update(chunk)
                        total += len(chunk)
                if total != member.file_size:
                    raise IOError("Incomplete staged member: " + relative)
                results.append({"file": relative, "size": total, "sha256": digest.hexdigest()})
    finally:
        reader.close()
    return {"staged": results, "total_bytes": sum(x["size"] for x in results)}


def glb_metadata(path: Path) -> dict:
    with path.open("rb") as inp:
        head = inp.read(20)
        if len(head) != 20:
            raise ValueError("GLB header truncated")
        magic, version, length, chunk_len, chunk_type = struct.unpack("<4sIIII", head)
        if magic != b"glTF" or version != 2 or length != path.stat().st_size:
            raise ValueError("Invalid GLB v2 header/length")
        if chunk_type != 0x4E4F534A or chunk_len > MAX_GLB_JSON or chunk_len % 4:
            raise ValueError("Invalid GLB JSON chunk")
        payload = json.loads(inp.read(chunk_len).decode("utf-8").rstrip(" \t\r\n\x00"))
    return {key: len(payload.get(key, [])) for key in
            ("meshes", "skins", "animations", "nodes", "materials", "textures", "images")}


def scan_output(root: Path) -> dict:
    counts = Counter()
    guns: dict[str, list[str]] = {name: [] for name in KEYWORDS}
    glbs = []
    errors = []
    files = sorted(p for p in root.rglob("*") if p.is_file()) if root.exists() else []
    for p in files:
        rel = p.relative_to(root).as_posix()
        counts[p.suffix.lower() or "[none]"] += 1
        for name, regex in KEYWORDS.items():
            if regex.search(rel) and len(guns[name]) < 40:
                guns[name].append(rel)
        if p.suffix.lower() == ".glb":
            try:
                meta = glb_metadata(p)
                if len(glbs) < 250:
                    glbs.append({"file": rel, **meta})
            except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
                errors.append({"file": rel, "error": str(exc)[:120]})
    return {
        "file_count": len(files),
        "extensions": dict(sorted(counts.items())),
        "weapon_filename_matches": guns,
        "glb_total": counts[".glb"],
        "glb_inspected": len(glbs),
        "glb_models": glbs,
        "invalid_glb": errors[:25],
        "glb_with_skins": sum(x["skins"] > 0 for x in glbs),
        "glb_with_animations": sum(x["animations"] > 0 for x in glbs),
        "note": "A GLB mesh does not prove an animated, correctly positioned FPS gun.",
    }


def safe_exec(cmd: list[str], timeout: int) -> dict:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout,
                              check=False)
        log = proc.stdout + "\n" + proc.stderr
        return {"returncode": proc.returncode, "log_characters": len(log),
                "weapon_log_matches": {name: len(regex.findall(log))
                                       for name, regex in KEYWORDS.items()},
                "error_tail": log[-1700:] if proc.returncode else ""}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "error": f"Timed out after {timeout}s"}


def probe(unlinker: Path, root: Path, dump_root: Path, zones: list[str],
          report_file: Path) -> dict:
    if not unLinker_exists(unlinker):
        raise FileNotFoundError("Unlinker binary missing or not executable: " + str(unlinker))
    search_path = str(root / "main") + ";" + str(root / "zone" / "spanish")
    report = {"tool": "OpenAssetTools Unlinker", "game": "IW3/COD4",
              "search_path_configured": True, "zones": {}, "scope": "local metadata only",
              "rights": "No extracted game assets may be committed or published."}
    failed = False
    for zone in zones:
        fastfile = root / "zone" / "spanish" / f"{zone}.ff"
        if not fastfile.is_file():
            raise FileNotFoundError(fastfile)
        out = dump_root / zone
        out.mkdir(parents=True, exist_ok=True)
        base = [str(unlinker), "--no-color", "--search-path", search_path]
        listing = safe_exec(base + ["--list", str(fastfile)], timeout=300)
        extraction = safe_exec(base + [
            "--model-format", "GLB", "--image-format", "DDS",
            "--include-assets", ",".join(IW3_ASSET_TYPES),
            "--output-folder", str(out), str(fastfile)], timeout=900)
        inventory = scan_output(out)
        report["zones"][zone] = {"list": listing, "extract": extraction, "inventory": inventory}
        if listing["returncode"] or extraction["returncode"]:
            failed = True
        atomic_json(report_file, report)
    report["probe_success"] = not failed
    report["all_weapon_animations_verified"] = False
    report["reason"] = "Requires matching gun, viewhands, rig, ADS, reload and fire in Godot."
    atomic_json(report_file, report)
    return report


def unLinker_exists(path: Path) -> bool:
    return path.is_file() and path.stat().st_mode & 0o111 != 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--parts-dir", type=Path, default=Path("_release_assets/c4"))
    prep.add_argument("--staging", type=Path, default=Path("_iw3_private"))
    prep.add_argument("--zone", action="append", choices=ZONES)
    prep.add_argument("--with-iwds", action="store_true")
    prep.add_argument("--report", type=Path, default=Path("_iw3_reports/staging.json"))
    run = sub.add_parser("probe")
    run.add_argument("--unlinker", required=True, type=Path)
    run.add_argument("--staging", type=Path, default=Path("_iw3_private"))
    run.add_argument("--dump-dir", type=Path, default=Path("_iw3_private/dumps"))
    run.add_argument("--zone", action="append", choices=ZONES)
    run.add_argument("--report", type=Path, default=Path("_iw3_reports/results.json"))
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = stage_archive(args.parts_dir, args.staging, args.zone or ["common_mp", "mp_crash"], args.with_iwds)
            atomic_json(args.report, result)
            print(json.dumps({"selected_files": len(result["staged"]), "staged_bytes": result["total_bytes"]}))
        else:
            result = probe(args.unlinker, args.staging, args.dump_dir, args.zone or ["common_mp", "mp_crash"], args.report)
            print(json.dumps({"probe_success": result["probe_success"],
                              "zone_count": len(result["zones"]),
                              "models": sum(x["inventory"]["glb_total"] for x in result["zones"].values())}))
            return 0 if result["probe_success"] else 1
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print("IW3 probe failed: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
