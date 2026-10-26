#!/usr/bin/env python3
"""Exercise original single-player firing through bounded client usercmds.

The disposable KisakCOD-sp clone injects at most 12 attack-button commands after
the client snapshot reports a real weapon and aims them at the nearest already
existing live damageable actor. No actor is spawned and no weapon/damage callback
is called directly. The checked-in engine source is never modified.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SOURCE = Path("src/client/cl_input.cpp")
ANCHOR = "        CL_CmdButtons(result);"
AIM_ANCHOR = "    CL_FinishMove(result);"
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
AIM_CODE = r"""
#if defined(KISAK_SP)
    // Test-only deterministic aim. Target an existing live damageable actor;
    // never create an actor or call a weapon/damage function from this hook.
    static unsigned int z2026_test_aim_cmds = 0;
    static bool z2026_test_aim_logged = false;
    static bool z2026_no_aim_target_logged = false;
    if ((result->buttons & BUTTON_ATTACK) &&
        clients[0].snap.ps.weapon > 0 &&
        z2026_test_aim_cmds < 12 &&
        level.num_entities > 1 &&
        g_entities[0].r.inuse &&
        g_entities[0].client)
    {
        gentity_s *z2026_target = nullptr;
        float z2026_best_distance_squared = 1.0e30f;
        const float *z2026_player_origin = g_entities[0].client->ps.origin;
        for (int z2026_i = 1; z2026_i < level.num_entities; ++z2026_i)
        {
            gentity_s *z2026_candidate = &g_entities[z2026_i];
            if (!z2026_candidate->r.inuse ||
                !z2026_candidate->actor ||
                !z2026_candidate->takedamage ||
                z2026_candidate->health <= 0)
            {
                continue;
            }
            const float z2026_dx = z2026_candidate->r.currentOrigin[0] - z2026_player_origin[0];
            const float z2026_dy = z2026_candidate->r.currentOrigin[1] - z2026_player_origin[1];
            const float z2026_dz = z2026_candidate->r.currentOrigin[2] - z2026_player_origin[2];
            const float z2026_distance_squared =
                z2026_dx * z2026_dx + z2026_dy * z2026_dy + z2026_dz * z2026_dz;
            if (z2026_distance_squared < z2026_best_distance_squared)
            {
                z2026_best_distance_squared = z2026_distance_squared;
                z2026_target = z2026_candidate;
            }
        }
        if (z2026_target)
        {
            const float z2026_dx = z2026_target->r.currentOrigin[0] - z2026_player_origin[0];
            const float z2026_dy = z2026_target->r.currentOrigin[1] - z2026_player_origin[1];
            const float z2026_target_z = z2026_target->r.currentOrigin[2] +
                0.5f * (z2026_target->r.mins[2] + z2026_target->r.maxs[2]);
            const float z2026_eye_z = z2026_player_origin[2] + 60.0f;
            const float z2026_dz = z2026_target_z - z2026_eye_z;
            const float z2026_horizontal = std::sqrt(z2026_dx * z2026_dx + z2026_dy * z2026_dy);
            const float z2026_degrees = 57.29577951308232f;
            clients[0].viewangles[0] = -std::atan2(z2026_dz, z2026_horizontal) * z2026_degrees;
            clients[0].viewangles[1] = std::atan2(z2026_dy, z2026_dx) * z2026_degrees;
            clients[0].viewangles[2] = 0.0f;
            ++z2026_test_aim_cmds;
            if (!z2026_test_aim_logged)
            {
                z2026_test_aim_logged = true;
                Z2026_TestInputTrace("TEST_AIMED_AT_EXISTING_ACTOR");
            }
        }
        else if (!z2026_no_aim_target_logged)
        {
            z2026_no_aim_target_logged = true;
            Z2026_TestInputTrace("TEST_NO_AIMABLE_ACTOR");
        }
    }
#endif
"""

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
    if data.count(FN) != 1 or data.count(ANCHOR) != 1 or data.count(AIM_ANCHOR) != 1:
        raise ValueError("Missing/duplicate native client input anchors")
    if "BUTTON_ATTACK" not in data or "clients[0].snap.ps" not in data:
        raise ValueError("Missing genuine IW3 client button/snapshot contract")
    data = data.replace("#include <universal/q_shared.h>",
                        "#include <cstdio>\n#include <cmath>\n#include <game/g_level.h>\n#include <universal/q_shared.h>", 1)
    idx = data.index(FN)
    data = data[:idx] + HELPER + "\n" + data[idx:]
    data = data.replace(ANCHOR, ANCHOR + "\n" + CODE, 1)
    data = data.replace(AIM_ANCHOR, AIM_CODE + "\n" + AIM_ANCHOR, 1)
    file.write_text(data, encoding="utf-8")
    return {
        "test_only_input": True,
        "client_commands_limited_to": 12,
        "requires_player_snapshot_weapon": True,
        "fireweapon_called_directly": False,
        "game_assets_modified": False,
        "multiplayer_auth_changed": False,
        "runtime_fire_verified": False,
        "aims_at_existing_damageable_actor": True,
        "aim_commands_limited_to": 12,
        "injects_actor_or_damage": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-copy", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(apply(args.source_copy), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
