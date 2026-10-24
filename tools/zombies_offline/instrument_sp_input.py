#!/usr/bin/env python3
"""Exercise original single-player firing from actual client-generated usercmd.

This inserts a *test-only* finite attack-button input into the disposable
KisakCOD-sp source clone. Only after the client snapshot reports a nonzero
weapon, CL_CreateCmd builds genuine usercmd packets with BUTTON_ATTACK.
No direct calls to FireWeapon, Bullet_Fire or G_Damage; success is measured
downstream by separate passive callbacks. The checked-in engine is untouched.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SOURCE = Path("src/client/cl_input.cpp")
ANCHOR = "        CL_CmdButtons(result);"
FN = "void __cdecl CL_CreateCmd("

HELPER = r'''
// Z2026 diagnostic client input marker; no player names or game assets.
static void Z2026_TestInputTrace(const char* stage)
{
    FILE* file = std::fopen("z2026-sp-input-trace.txt", "a");
    if (file)
    {
        std::fprintf(file, "%s\n", stage);
        std::fclose(file);
    }
}
'''
CODE = """
#if defined(KISAK_SP)
        // Test-only, finite attack input; first require a loaded weapon.
        static unsigned int z2026_test_attack_cmds = 0;
        if (clients[0].snap.ps.weapon > 0 && z2026_test_attack_cmds < 12)
        {
            result->buttons |= BUTTON_ATTACK;
            if (z2026_test_attack_cmds++ == 0)
                Z2026_TestInputTrace("TEST_ATTACK_BUTTON_INJECTED");
        }
#endif
"""

def apply(copy: Path) -> dict:
    file = copy / SOURCE
    root = copy.resolve()
    vendor = (Path(__file__).resolve().parents[2] / "third_party/KisakCOD").resolve()
    if root == vendor or vendor in root.parents:
        raise ValueError("Will not edit original engine")
    if not file.is_file():
        raise ValueError("Missing single-player client source")
    data = file.read_text(encoding="utf-8")
    if "Z2026_TestInputTrace" in data:
        raise ValueError("Client input diagnostic already applied")
    if data.count(FN) != 1 or data.count(ANCHOR) != 1:
        raise ValueError("Missing/duplicate native client input anchors")
    if "BUTTON_ATTACK" not in data or "clients[0].snap.ps" not in data:
        raise ValueError("Missing genuine IW3 client button/snapshot contract")
    data = data.replace("#include <universal/q_shared.h>",
                        "#include <cstdio>\n#include <universal/q_shared.h>", 1)
    idx = data.index(FN)
    data = data[:idx] + HELPER + "\n" + data[idx:]
    data = data.replace(ANCHOR, ANCHOR + "\n" + CODE, 1)
    file.write_text(data, encoding="utf-8")
    return {
        "test_only_input": True,
        "client_commands_limited_to": 12,
        "requires_player_snapshot_weapon": True,
        "fireweapon_called_directly": False,
        "game_assets_modified": False,
        "multiplayer_auth_changed": False,
        "runtime_fire_verified": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-copy", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source_copy), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
