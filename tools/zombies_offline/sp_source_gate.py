#!/usr/bin/env python3
"""Prepare a disposable *single-player-only* IW3 source build for ZOMBIES-2026.

This does not alter the pinned third_party/KisakCOD source, ship COD4 game
assets, or bypass multiplayer authentication. KisakCOD-sp's WinMain alone
skips the unnecessary Steam startup call; KisakCOD-mp and dedicated are not
compiled by this gate. This is a *source/build* gate, not gameplay validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

WINMAIN = Path("src/win32/win_main.cpp")
WEAPON_SOURCE = Path("src/bgame/bg_weapons_load_obj.cpp")
COMMON = Path("scripts/common_files.cmake")
SP = Path("scripts/sp/sp_files.cmake")
SP_CMAKE = Path("scripts/sp/CMakeLists.txt")

STEAM_CALL = "\t\t\tSteam_Init();"
STEAM_REPLACEMENT = """\t\t\t// Z2026: single-player only. Do not start Steam for offline
\t\t\t// gameplay. This guard does NOT touch MP ticket validation.
#ifndef KISAK_SP
\t\t\tSteam_Init();
#endif"""

# These are engine WeaponDef *field names*, NOT COD4 weapon values or assets.
# Nothing here fabricates timings, magazine sizes, or weapon ballistics.
WEAPON_FIELDS = (
    "displayName",
    "gunModel",
    "handModel",
    "fireType",
    "damage",
    "clipSize",
    "fireTime",
    "reloadTime",
    "reloadEmptyTime",
    "adsTransInTime",
    "adsTransOutTime",
    "fireAnim",
    "adsFireAnim",
    "reloadAnim",
)


def inspect(source: Path) -> dict:
    """Check that SP actor and weapon source is actually selected for build."""
    def read(p: Path) -> str:
        f = source / p
        return f.read_text(encoding="utf-8") if f.is_file() else ""

    weapon = read(WEAPON_SOURCE)
    common = read(COMMON)
    sp = read(SP)
    cmake = read(SP_CMAKE)
    winmain = read(WINMAIN)
    fields = set(re.findall(r'\{\s*"([^"]+)"\s*,\s*\d+\s*,', weapon))
    checks = {
        "single_player_target": (
            'project(KisakCOD-sp)' in cmake
            and 'KISAK_SP' in cmake
            and 'add_executable(' in cmake
        ),
        "single_player_actors": all(name in sp for name in (
            'actor.cpp', 'actor_spawner.cpp',
            'actor_navigation.cpp', 'g_main.cpp', 'g_runframe.cpp'
        )),
        "weapon_engine_in_shared_sources": all(name in common for name in (
            'bg_weapons.cpp', 'bg_weapons_load_obj.cpp',
            'g_weapon.cpp'
        )),
        "weapon_definition_schema": all(name in fields for name in WEAPON_FIELDS),
        "single_player_steam_init_guarded": (
            winmain.count(STEAM_REPLACEMENT) == 1
            and winmain.count(STEAM_CALL) == 1
        ),
    }
    return {
        "project": "ZOMBIES-2026",
        "mode": "OFFLINE_SINGLE_PLAYER_SOURCE_BUILD",
        "steamsession_required_by_this_gate": False,
        "multiplayer_client_built_by_this_gate": False,
        "dedicated_server_built_by_this_gate": False,
        "single_player_source_gate": all(checks.values()),
        "checks": checks,
        "weapon_fields_detected": [name for name in WEAPON_FIELDS if name in fields],
        "weapon_values_invented": False,
        "cod4_proprietary_assets_included": False,
        "sp_executable_compiled": False,
        "zombie_gameplay_verified": False,
        "android_apk_verified": False,
        "warning": (
            "KisakCOD-sp still needs appropriate runtime data/maps. "
            "Compilation does not prove offline gameplay. Original COD4 "
            "weapon models, sounds and data require permission before "
            "repackaging or distribution."
        ),
    }


def prepare(source: Path) -> dict:
    if not (source / "CMakeLists.txt").is_file():
        raise ValueError("Missing disposable KisakCOD source root")
    path = source / WINMAIN
    contents = path.read_text(encoding="utf-8")
    if contents.count(STEAM_CALL) != 1:
        raise ValueError("WinMain must have precisely one expected Steam_Init call")
    if "Z2026: single-player only" in contents:
        raise ValueError("Diagnostic guard already applied")
    # Single-player opt-out only. The original MP client authentication source
    # src/client_mp/cl_main_pc_mp.cpp and the Steam validation routines are
    # never edited, so the code cannot fabricate a successful MP handshake.
    path.write_text(contents.replace(STEAM_CALL, STEAM_REPLACEMENT, 1),
                    encoding="utf-8")
    report = inspect(source)
    if not report["single_player_source_gate"]:
        raise ValueError("Offline SP source checks failed: " +
                         json.dumps(report["checks"], sort_keys=True))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-copy", type=Path, required=True,
                        help="Disposable copy of KisakCOD (NOT third_party source)")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_copy.resolve()
    upstream = (Path(__file__).resolve().parents[2] /
                "third_party/KisakCOD").resolve()
    if source == upstream or upstream in source.parents:
        parser.error("Refusing to patch vendored KisakCOD in place")
    report = prepare(source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n",
                           encoding="utf-8")
    print("OFFLINE_SP_SOURCE_GATE", json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
