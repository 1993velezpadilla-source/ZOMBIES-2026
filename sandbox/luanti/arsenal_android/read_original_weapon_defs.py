"""Read ONLY source-authentic COD4 weapon-definition metadata for 28 guns.

Requires OpenAssetTools temporary extracted weapon files. No invented magazine
sizes, fire rates, reload timings, handling stats, attachment support, or
licenses. Never upload original .weapon blobs or game assets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

NUMERIC = (
    "clipSize", "maxAmmo", "startAmmo", "shotCount", "fireTime",
    "fireDelay", "reloadTime", "reloadEmptyTime", "reloadAddTime",
    "adsTransInTime", "adsTransOutTime", "damage", "minDamage",
    "damageRange", "minDamageRange", "moveSpeedScale", "adsMoveSpeedScale",
    "hipGunKickPitchMin", "hipGunKickPitchMax",
    "hipGunKickYawMin", "hipGunKickYawMax",
    "adsGunKickPitchMin", "adsGunKickPitchMax",
    "adsGunKickYawMin", "adsGunKickYawMax",
    "gunMaxPitch", "gunMaxYaw",
)
STRINGS = (
    "displayName", "weaponType", "weaponClass", "fireType", "playerAnimType",
    "viewModel", "worldModel", "reloadAnim", "reloadEmptyAnim",
    "fireSound", "fireSoundPlayer", "emptyFireSoundPlayer", "reloadSound",
)
ESSENTIAL = ("clipSize", "fireTime", "reloadTime", "reloadEmptyTime")
MAX_SOURCE_DEF = 1024 * 1024


def weapon_fields(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    if not 2 < len(raw) <= MAX_SOURCE_DEF:
        raise ValueError("original weapon definition file invalid length")
    text = raw.decode("latin-1")
    tokens = text.split("\\")
    if len(tokens) < 4:
        raise ValueError("original COD4 backslash weapon fields missing")
    # OAT dumps start with a header token, followed by alternating key/value.
    fields = dict(zip(tokens[1::2], tokens[2::2]))
    if not fields or not any(k in fields for k in ESSENTIAL):
        raise ValueError("no numeric IW3 weapon definition fields")
    return fields


def read_number(fields, key):
    text = fields.get(key, "")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if not math.isfinite(value):
        raise ValueError("non-finite original weapon stat: " + key)
    return value


def lookup(root: Path, identifiers: list[str]) -> tuple[Path | None, str | None]:
    for candidate in identifiers:
        for folder in (root/"common_mp"/"weapons", root/"common"/"weapons"):
            path = folder/candidate
            if path.is_file():
                return path, candidate
    return None, None


def inspect(root: Path, manifest: dict) -> dict:
    weapons = manifest.get("weapons", [])
    if len(weapons) != 28 or len({w["id"] for w in weapons}) != 28:
        raise ValueError("needs 28 distinct source weapon identities")
    report = {}
    for weapon in weapons:
        wid = weapon["id"]
        candidates = weapon.get("source_weapon_candidates", [])
        if not candidates or not all(
                isinstance(c, str) and c and "/" not in c and ".." not in c
                for c in candidates):
            raise ValueError("unsafe original weapon source name: " + wid)
        path, match = lookup(root, candidates)
        row = {"id": wid, "source_definition_found": bool(path),
               "source_definition_name": match,
               "source_stats_valid": False,
               "has_required_timing_and_ammo": False,
               "luanti_gameplay_implemented": False}
        if path:
            try:
                fields = weapon_fields(path)
                numeric = {k: read_number(fields, k) for k in NUMERIC}
                numeric = {k: v for k, v in numeric.items() if v is not None}
                strings = {k: fields[k] for k in STRINGS if fields.get(k)}
                row.update({"source_stats_valid": bool(numeric),
                            "has_required_timing_and_ammo": all(
                                k in numeric for k in ESSENTIAL),
                            "numeric": numeric, "strings": strings,
                            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            except (ValueError, OSError) as error:
                row["source_error"] = str(error)[:180]
        report[wid] = row
    return {
        "source": "COD4 IW3 original weapon definitions (owned game archive)",
        "unique_weapons_expected": 28,
        "weapon_defs_present": sum(x["source_definition_found"] for x in report.values()),
        "weapon_defs_with_required_timing_and_ammo": sum(
            x["has_required_timing_and_ammo"] for x in report.values()),
        "zero_invented_weapon_numbers": True,
        "playable_arsenal_28": False,
        "weapons": report,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dumps", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = inspect(a.dumps, json.loads(a.manifest.read_text()))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print("COD4_ORIGINAL_28_WEAPON_DEFS", report["weapon_defs_present"],
          "of 28; full numeric source stats",
          report["weapon_defs_with_required_timing_and_ammo"],
          "of 28. No gameplay asserted.")


if __name__ == "__main__":
    main()
