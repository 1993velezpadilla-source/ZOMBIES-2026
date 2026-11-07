#!/usr/bin/env python3
"""Export the GPL engine's IW3 weapon field layout, not proprietary weapon assets.

Reads the 502 parser field declarations and the pinned legacy-offset audit
fixture. Native offsetof expressions are preserved separately from 32-bit offsets.
Does not read game IWDs, synthesize weapon statistics, or publish any models.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

DECL = re.compile(r'cspField_t\s+weaponDefFields\[(\d+)\]\s*=\s*\{')
ROW = re.compile(r'\{\s*"([^"]+)"\s*,\s*(\d+|offsetof\(WeaponDef,\s*\w+(?:\[\d+\])?\))\s*,\s*([A-Z][A-Z0-9_]*)\s*\}')
LEGACY = Path(__file__).resolve().parents[2] / "tests/fixtures/iw3_weapon_fields_legacy_offsets.tsv"

def parse_weapon_schema(source_text: str) -> dict:
    match = DECL.search(source_text)
    if not match:
        raise ValueError("weaponDefFields declaration not found")
    body_end = source_text.find("\n};", match.end())
    if body_end < 0:
        raise ValueError("weaponDefFields closing brace not found")
    body = source_text[match.end():body_end]
    entries = list(ROW.finditer(body))
    expected = int(match.group(1))
    if expected != 502 or len(entries) != expected:
        raise ValueError(f"Incomplete weapon schema: {len(entries)} of {expected}")
    # Keep the original 32-bit export contract for source-only consumers,
    # but never present those offsets as usable native Android addresses.
    legacy = [
        line.split("\t") for line in LEGACY.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    if len(legacy) != expected:
        raise ValueError("Incomplete legacy weapon offset audit fixture")
    fields = []
    for i, entry in enumerate(entries):
        name, offset, field_type = entry.groups()
        old_name, old_offset, old_type = legacy[i]
        if (name, field_type) != (old_name, old_type):
            raise ValueError(f"Weapon schema mismatch at entry {i}: {name}")
        if offset.isdigit() and int(offset) != int(old_offset):
            raise ValueError(f"Legacy weapon offset mismatch at entry {i}")
        fields.append({
            "name": name,
            "offset_bytes": int(old_offset),
            "offset_abi": "legacy_32bit_only",
            "native_offset_expression": offset if offset.startswith("offsetof(") else None,
            "field_type": field_type,
        })
    names = [row["name"] for row in fields]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    return {
        "source": "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp",
        "license_note": "Derived from KisakCOD GPLv3 source field declarations",
        "field_count": len(fields),
        "offsets_are_native_android_offsets": False,
        "unique_names": len(set(names)),
        "duplicate_names_in_upstream_source": duplicates,
        "weapon_stats_or_models": "NOT_INCLUDED",
        "runtime_weapon_files_loaded": False,
        "fields": fields,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = parse_weapon_schema(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("WEAPON_SCHEMA_EXPORT field_count=502 unique_names=" + str(data["unique_names"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
