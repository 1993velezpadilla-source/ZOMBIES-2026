#!/usr/bin/env python3
"""Report IW3 XANIM v17 headers and rifle action availability without copying assets.

The raw XANIM parser validates ONLY the format header and optional early bone
names (without delta); it does NOT decode keyframes or validate Godot playback.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import struct
import sys

from iw3_weapon_probe import atomic_json

FAMILY = {
    "M4": re.compile(r"^viewmodel_m4(?:a1)?(?:_|$)", re.I),
    "AK47": re.compile(r"^viewmodel_ak47(?:_|$)", re.I),
    "MP5": re.compile(r"^viewmodel_mp5(?:sd)?(?:_|$)", re.I),
}
ACTION = {
    "idle": re.compile(r"(?:^|_)idle(?:_|$)", re.I),
    "ads": re.compile(r"(?:^|_)ads(?:_|$)", re.I),
    "fire": re.compile(r"(?:^|_)(?:fire|shoot)(?:_|$)", re.I),
    "reload": re.compile(r"(?:^|_)reload(?:_|$)", re.I),
}


def parse_xanim_header(path: Path) -> dict:
    with path.open("rb") as fh:
        header = fh.read(10)
        if len(header) < 10:
            raise ValueError("truncated raw xanim header")
        version, frames, bones, flags, asset_type, fps = struct.unpack("<HHHBBH", header)
        if version != 17 or not 0 < frames < 30000 or not 0 < bones <= 1024 or not 0 < fps <= 240:
            raise ValueError("not a plausible IW3 XANIM v17 header")
        result = {"version": version, "frame_count_raw": frames, "bone_count": bones,
                  "flags": flags, "asset_type": asset_type, "frame_rate": fps,
                  "bone_name_parse": "unsupported_with_delta" if flags & 2 else "attempted"}
        result["bone_names_sample"] = []
        if not (flags & 2):
            # Raw format after header has 2 bitmasks of ceil(boneCount / 8).
            # Name strings follow, then variable-length keyframe tracks.
            fh.seek(10 + 2 * ((bones + 7) // 8))
            names = []
            for _ in range(bones):
                value = bytearray()
                for _ in range(128):
                    one = fh.read(1)
                    if not one:
                        break
                    if one == b"\x00":
                        break
                    value.extend(one)
                else:
                    break
                if not one or not value or any(x < 32 or x > 126 for x in value):
                    break
                names.append(value.decode("ascii", errors="replace"))
            result["bone_name_parse"] = "ok" if len(names) == bones else "unverified"
            result["bone_names_sample"] = names[:24] if len(names) == bones else []
        return result


def review(dump_root: Path) -> dict:
    report = {
        "format": "IW3 raw XANIM v17",
        "headers_only_not_decoded": True,
        "families": {n: {"action_counts": dict.fromkeys(ACTION, 0), "samples": []} for n in FAMILY},
        "zone_xanim_counts": {}, "valid_headers": 0, "invalid_headers": 0,
        "invalid_header_examples": [], "full_rig_animation_verified": False}
    for zone_dir in sorted(dump_root.iterdir() if dump_root.is_dir() else []):
        folder = zone_dir / "xanim"
        if not folder.exists():
            continue
        paths = sorted(p for p in folder.rglob("*") if p.is_file())
        report["zone_xanim_counts"][zone_dir.name] = len(paths)
        for path in paths:
            try:
                header = parse_xanim_header(path)
                report["valid_headers"] += 1
            except (OSError, ValueError) as exc:
                report["invalid_headers"] += 1
                if len(report["invalid_header_examples"]) < 10:
                    report["invalid_header_examples"].append({"file": path.name, "error": str(exc)})
                continue
            for name, rule in FAMILY.items():
                if not rule.search(path.name):
                    continue
                kind = [a for a, p in ACTION.items() if p.search(path.name)]
                for a in kind:
                    report["families"][name]["action_counts"][a] += 1
                if len(report["families"][name]["samples"]) < 50:
                    report["families"][name]["samples"].append({
                        "name": path.name, "action": kind or ["other"], **header})
    report["action_presence"] = {
        name: {action: count > 0 for action, count in data["action_counts"].items()}
        for name, data in report["families"].items()}
    report["note"] = ("Matching animation filename + valid v17 header does not prove matching "
                      "skin joints, keyframe decoding, timing, ADS offsets, or Godot playback.")
    return report


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "_iw3_private/dumps")
    destination = Path(sys.argv[2] if len(sys.argv) > 2 else "_iw3_reports/animation-gate.json")
    report = review(root)
    atomic_json(destination, report)
    print(json.dumps({"zone_xanim_counts": report["zone_xanim_counts"],
                      "valid_headers": report["valid_headers"],
                      "invalid_headers": report["invalid_headers"],
                      "action_presence": report["action_presence"],
                      "action_counts": {name: info["action_counts"]
                                        for name, info in report["families"].items()}}))
