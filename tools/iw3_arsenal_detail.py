#!/usr/bin/env python3
"""Inspect all exported IW3 GLB metadata, by actual weapon/viewmodel identity.

Operates only on temporary extracted files; emits filenames and counts, not assets.
"""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import re
import sys

from iw3_weapon_probe import glb_metadata, atomic_json

LOD = re.compile(r"_lod\d+$", re.I)
TARGETS = {
    "M4_rifle": re.compile(r"^(?:viewmodel|weapon)_m4(?:_|$)|^viewmodel_m4a1(?:_|$)", re.I),
    "AK47": re.compile(r"^(?:viewmodel|weapon)_ak_?47(?:_|$)", re.I),
    "MP5": re.compile(r"^(?:viewmodel|weapon)_mp5(?:sd)?(?:_|$)", re.I),
    "viewhands": re.compile(r"(?:viewhands|view_hands|base_viewhands)", re.I),
}


def inspect(dump_dir: Path) -> dict:
    result = {"zones": {}, "total_glb": 0, "total_valid": 0,
              "total_skinned": 0, "total_animated": 0,
              "weapon_viewmodel_families": [], "targets": {k: [] for k in TARGETS}}
    families: set[str] = set()
    for zone_dir in sorted(dump_dir.iterdir() if dump_dir.is_dir() else []):
        if not zone_dir.is_dir():
            continue
        counts = Counter()
        viewmodel_names: set[str] = set()
        export_files = list(zone_dir.rglob("*.glb"))
        animation_paths = []
        for p in zone_dir.rglob("*"):
            if p.is_file() and ("xanim" in p.as_posix().lower() or p.suffix.lower() in
                                {".xanim_bin", ".xanim_export", ".anim"}):
                animation_paths.append(p.relative_to(zone_dir).as_posix())
        for p in export_files:
            counts["glb"] += 1
            stem = LOD.sub("", p.stem.lower())
            if stem.startswith("viewmodel_"):
                viewmodel_names.add(stem)
                families.add(stem)
            try:
                metadata = glb_metadata(p)
                counts["valid"] += 1
                counts["skinned"] += int(metadata["skins"] > 0)
                counts["animated"] += int(metadata["animations"] > 0)
            except (ValueError, OSError, UnicodeError, json.JSONDecodeError):
                counts["invalid"] += 1
                continue
            for name, pattern in TARGETS.items():
                if pattern.search(stem) and len(result["targets"][name]) < 80:
                    result["targets"][name].append({
                        "zone": zone_dir.name, "file": p.relative_to(zone_dir).as_posix(),
                        **metadata})
        result["zones"][zone_dir.name] = {
            "glb_files": counts["glb"], "valid_glb": counts["valid"],
            "skinned_glb": counts["skinned"], "animated_glb": counts["animated"],
            "invalid_glb": counts["invalid"],
            "viewmodel_unique_families": len(viewmodel_names),
            "viewmodel_families": sorted(viewmodel_names),
            "xanim_named_file_count": len(animation_paths),
            "xanim_named_file_samples": animation_paths[:20],
        }
        result["total_glb"] += counts["glb"]
        result["total_valid"] += counts["valid"]
        result["total_skinned"] += counts["skinned"]
        result["total_animated"] += counts["animated"]
    result["weapon_viewmodel_families"] = sorted(families)
    result["unique_viewmodel_families"] = len(families)
    result["target_counts"] = {k: len(v) for k, v in result["targets"].items()}
    result["ready_for_godot_animated_weapon"] = False
    result["note"] = ("GLB skin presence != matching first-person XANIM, ADS, fire, reload, "
                      "scale or correct attachment to viewhands.")
    return result


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "_iw3_private/dumps")
    path = Path(sys.argv[2] if len(sys.argv) > 2 else "_iw3_reports/arsenal-detail.json")
    report = inspect(root)
    atomic_json(path, report)
    print(json.dumps({k: report[k] for k in
                      ("total_glb", "total_valid", "total_skinned", "total_animated",
                       "unique_viewmodel_families", "target_counts")}))
    for name, rows in report["targets"].items():
        print(name + " examples=" + json.dumps(rows[:6]))
