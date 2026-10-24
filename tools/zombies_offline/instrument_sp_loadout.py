#!/usr/bin/env python3
"""Test-only loadout bootstrap in a disposable SP IW3 source clone.

The previous native smoke confirmed an active player and actors, but no
weapon equipped. This module uses genuine engine weapon definitions that
were *already registered* by the SP scene; it NEVER creates made-up
stats/assets, invokes multiplayer code, or publishes game data.

The diagnostic explicitly labels a TEST-GRANTED weapon so a successful
selection can never be confused with a natural level-script loadout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MAIN = Path("src/game/g_main.cpp")

# Original engine symbols: G_GivePlayerWeapon() and G_SelectWeaponIndex()
# come from src/game/g_weapon.cpp, InitializeAmmo() from
# src/game/g_client_script_cmd.cpp. All are in the SP target.
DECLARES = """
// Z2026 test-only offline source clone; declarations of original SP APIs.
extern int __cdecl G_GivePlayerWeapon(playerState_s *pPS, int index, uint8_t model);
extern void __cdecl G_SelectWeaponIndex(int clientNum, int weaponIndex);
"""

# inject directly after the already validated passive diagnostic frame counter.
ANCHOR = '    ++z2026_observed_frames;'

CODE = r'''
    // Z2026 TEST BOOTSTRAP. Runs once, after player spawn and level load.
    // It exercises actual weapon registry, give, ammo and select APIs.
    // It is NOT a normal gameplay or level-script loadout.
    static bool z2026_loadout_probe_done = false;
    if (!z2026_loadout_probe_done &&
        z2026_observed_frames >= 4 &&
        !level.initializing &&
        !level.clientIsSpawning &&
        g_entities[0].r.inuse &&
        g_entities[0].client &&
        g_entities[0].client->ps.weapon == 0)
    {
        z2026_loadout_probe_done = true;
        Z2026_SPTrace("TEST_LOADOUT_BOOTSTRAP_BEGIN");
        bool z2026_found_valid = false;
        for (int z2026_i = 1; z2026_i < BG_GetNumWeapons(); ++z2026_i)
        {
            WeaponDef* z2026_def = BG_GetWeaponDef(z2026_i);
            if (!z2026_def ||
                z2026_def->weapType != WEAPTYPE_BULLET ||
                !z2026_def->gunXModel[0] ||
                !BG_CanPlayerHaveWeapon(z2026_i))
            {
                continue;
            }
            z2026_found_valid = true;
            Z2026_SPTrace("TEST_REGISTERED_BULLET_WEAPON_FOUND");
            const int z2026_granted = G_GivePlayerWeapon(
                &g_entities[0].client->ps, z2026_i, 0);
            if (z2026_granted)
            {
                Z2026_SPTrace("TEST_WEAPON_GRANTED");
                InitializeAmmo(&g_entities[0], z2026_i, 0, 0);
                Z2026_SPTrace("TEST_AMMO_INITIALIZED");
                G_SelectWeaponIndex(0, z2026_i);
                Z2026_SPTrace("TEST_WEAPON_SWITCH_REQUESTED");
            }
            else
            {
                Z2026_SPTrace("TEST_WEAPON_GRANT_REJECTED");
            }
            break;
        }
        if (!z2026_found_valid)
            Z2026_SPTrace("TEST_NO_VALID_REGISTERED_BULLET_WEAPON");
    }
'''


def apply(source_copy: Path) -> dict:
    path = source_copy / MAIN
    if not path.is_file():
        raise ValueError("Missing disposable SP game source")
    vendored = Path(__file__).resolve().parents[2] / "third_party/KisakCOD"
    root = source_copy.resolve()
    if root == vendored.resolve() or vendored.resolve() in root.parents:
        raise ValueError("Refusing edits to vendored engine")
    text = path.read_text(encoding="utf-8")
    if "Z2026 TEST BOOTSTRAP" in text:
        raise ValueError("Bootstrap already installed")
    for anchor in (ANCHOR, "Z2026_SPTrace", "z2026_observed_frames",
                   "int __cdecl G_RunFrame("):
        if text.count(anchor) < 1:
            raise ValueError(f"Missing prior SP diagnostic anchor {anchor}")
    if text.count(ANCHOR) != 1:
        raise ValueError("Unexpected duplicate frame counter")
    if "G_GivePlayerWeapon(" in text or "TEST_LOADOUT_BOOTSTRAP" in text:
        raise ValueError("Existing instrument/test conflict")
    header = text.index("void __cdecl G_InitGame(")
    text = text[:header] + DECLARES + "\n" + text[header:]
    text = text.replace(ANCHOR, ANCHOR + "\n" + CODE, 1)
    path.write_text(text, encoding="utf-8")
    return {
        "mode": "disposable-SP-source test-only real registered weapon grant",
        "gun_models_or_weapon_values_authored": False,
        "altered_mp_auth": False,
        "forged_fire_or_damage": False,
        "test_weapon_grant_injected": True,
        "runtime_success_not_assumed": True,
        "expected_evidence": [
            "TEST_LOADOUT_BOOTSTRAP_BEGIN",
            "TEST_REGISTERED_BULLET_WEAPON_FOUND",
            "TEST_WEAPON_GRANTED",
            "TEST_AMMO_INITIALIZED",
            "TEST_WEAPON_SWITCH_REQUESTED",
            "PLAYER_WEAPON_EQUIPPED",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-copy", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source_copy), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
