#!/usr/bin/env python3
"""Observe actual IW3 SP player weapons, shots, NPC logic and damage.

This is *observation only*: the temporary diagnostic source retains all game
simulation logic unchanged. A marker means an original function ran; its
absence means that the corresponding gameplay behavior is NOT verified.
No shots or enemies are fabricated by this instrument.
"""
from __future__ import annotations
import argparse
from pathlib import Path

FILES = {
    "weapon": Path("src/game/g_weapon.cpp"),
    "actor": Path("src/game/actor.cpp"),
    "combat": Path("src/game/g_combat.cpp"),
    "main": Path("src/game/g_main.cpp"),
}
WEAPON = "void __cdecl FireWeapon("
BULLET = "            Bullet_Fire(ent, fAimSpreadAmount, &wp, ent, gametime);"
ACTOR_THINK = "void __cdecl Actor_Think("
ACTOR_DIE = "void __cdecl Actor_Die("
ACTOR_PAIN = "void __cdecl Actor_Pain("
DAMAGE = "void __cdecl G_Damage("
FRAME = "int __cdecl G_RunFrame("

HELPER = r'''
// Diagnostic: first occurrence of gameplay callbacks only. No private data.
static void Z2026_CombatTrace(const char* stage)
{
    FILE* output = std::fopen("z2026-sp-combat-trace.txt", "a");
    if (output)
    {
        std::fprintf(output, "%s\n", stage);
        std::fclose(output);
    }
}
'''


def insert_entry(source: str, anchor: str, code: str) -> str:
    if source.count(anchor) != 1:
        raise ValueError(f"SP symbol not unique: {anchor}")
    pos = source.index(anchor)
    brace = source.index("{", pos)
    if ";" in source[pos:brace]:
        raise ValueError("Unexpected declaration, not a function body")
    return source[:brace+1] + "\n" + code + "\n" + source[brace+1:]


def one_shot(stage: str) -> str:
    var = "z2026_saw_" + stage.lower()
    return (
        f"    static bool {var} = false;\n"
        f"    if (!{var}) {{ {var} = true; Z2026_CombatTrace(\"{stage}\"); }}"
    )


def prepare(source_root: Path) -> dict:
    original = {key: (source_root / path).read_text(encoding="utf-8")
                for key, path in FILES.items()}
    for key, source in original.items():
        if "Z2026_CombatTrace" in source:
            raise ValueError(f"Already instrumented: {key}")
    for key, patterns in {
        "weapon": (WEAPON, BULLET),
        "actor": (ACTOR_THINK, ACTOR_DIE, ACTOR_PAIN),
        "combat": (DAMAGE,),
        "main": (FRAME,),
    }.items():
        for anchor in patterns:
            if original[key].count(anchor) != 1:
                raise ValueError(f"Missing/duplicate {key} anchor: {anchor}")
    if "Z2026_SPTrace" not in original["main"]:
        raise ValueError("Run instrument_sp_level.py before combat hooks")

    weapon = insert_entry(original["weapon"], WEAPON, one_shot("FIRE_WEAPON_ENTER"))
    weapon = weapon.replace(
        BULLET,
        "            {\n" +
        "                " + one_shot("BULLET_FIRE_DISPATCH").strip().replace("\n", "\n                ") +
        "\n            }\n" + BULLET,
        1,
    )
    actor = insert_entry(original["actor"], ACTOR_THINK, one_shot("ACTOR_THINK_ENTER"))
    actor = insert_entry(actor, ACTOR_PAIN, one_shot("ACTOR_PAIN_ENTER"))
    actor = insert_entry(actor, ACTOR_DIE, one_shot("ACTOR_DIE_ENTER"))
    combat = insert_entry(
        original["combat"], DAMAGE,
        one_shot("G_DAMAGE_ENTER") + "\n"
        "    static bool z2026_damaged_actor = false;\n"
        "    if (!z2026_damaged_actor && targ && targ->actor) {\n"
        "        z2026_damaged_actor = true;\n"
        '        Z2026_CombatTrace("G_DAMAGE_ACTOR");\n'
        "    }"
    )
    # Called each SP frame; log only the first time each fact becomes true.
    main = insert_entry(
        original["main"], FRAME,
        "    static unsigned int z2026_observed_frames = 0;\n"
        "    static bool z2026_player_seen = false;\n"
        "    static bool z2026_weapon_seen = false;\n"
        "    static bool z2026_actor_seen = false;\n"
        "    ++z2026_observed_frames;\n"
        "    if (z2026_observed_frames == 2) Z2026_SPTrace(\"G_SECOND_FRAME\");\n"
        "    if (g_entities[0].r.inuse && g_entities[0].client)\n"
        "    {\n"
        "        if (!z2026_player_seen) { z2026_player_seen = true; Z2026_SPTrace(\"PLAYER_ENTITY_ACTIVE\"); }\n"
        "        if (!z2026_weapon_seen && g_entities[0].client->ps.weapon > 0)\n"
        "        { z2026_weapon_seen = true; Z2026_SPTrace(\"PLAYER_WEAPON_EQUIPPED\"); }\n"
        "    }\n"
        "    if (!z2026_actor_seen)\n"
        "    {\n"
        "        for (int z2026_ent = 1; z2026_ent < level.num_entities; ++z2026_ent)\n"
        "        {\n"
        "            if (g_entities[z2026_ent].r.inuse && g_entities[z2026_ent].actor)\n"
        "            { z2026_actor_seen = true; Z2026_SPTrace(\"SP_ACTOR_PRESENT\"); break; }\n"
        "        }\n"
        "    }"
    )

    output = {"weapon": weapon, "actor": actor, "combat": combat, "main": main}
    # Note: source_root is a disposable copy. No repository source is changed.
    for key, text in output.items():
        path = source_root / FILES[key]
        if key != "main":
            text = "#include <cstdio>\n" + HELPER + "\n" + text
        path.write_text(text, encoding="utf-8")
    return {
        "mode": "passive single-player combat callbacks",
        "files_instrumented": list(FILES.keys()),
        "expected_markers": [
            "G_SECOND_FRAME", "PLAYER_ENTITY_ACTIVE", "PLAYER_WEAPON_EQUIPPED",
            "SP_ACTOR_PRESENT", "FIRE_WEAPON_ENTER", "BULLET_FIRE_DISPATCH",
            "ACTOR_THINK_ENTER", "ACTOR_PAIN_ENTER", "G_DAMAGE_ENTER",
            "G_DAMAGE_ACTOR", "ACTOR_DIE_ENTER",
        ],
        "injected_shots": False,
        "injected_enemies": False,
        "multiplayer_auth_changed": False,
    }


def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--source-copy", required=True, type=Path)
    cfg = args.parse_args()
    import json
    print(json.dumps(prepare(cfg.source_copy), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
