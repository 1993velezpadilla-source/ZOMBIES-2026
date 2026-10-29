#!/usr/bin/env python3
"""Stage authentic actor routines after fixing 32-bit record-stride assumptions.

The extracted C++ bodies remain the vendored KisakCOD implementation. This is
an ARM64 compile audit only; it does not initialize actors or prove gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/game/actor.cpp")
SIGNATURES = (
    "void __cdecl SentientInfo_Clear(sentient_info_t *pInfo)",
    "gentity_s *__cdecl Actor_IsKnownEnemyInRegion(",
)
REQUIRED = (
    "memset(pInfo, 0, sizeof(*pInfo));",
    "info = &self->sentientInfo[v9];",
    "v12 = info->lastKnownPosTime;",
    "i = info->vLastKnownPos;",
)
HEADER = """// Generated from authentic KisakCOD actor.cpp bodies. Do not edit.
#ifndef KISAK_SP
#define KISAK_SP 1
#endif
#define IW3_ANDROID_PORTABLE_PATHNODE_SERVICES 1
#include <universal/q_shared.h>
#include <universal/assertive.h>
#include <game/game_public.h>
#include <game/g_local.h>
#include <game/g_runframe.h>
#include <game/actor.h>
#include <universal/com_math.h>

// Narrow declaration verified against the original server/sv_game.h.
bool __cdecl SV_EntityContact(const float *mins, const float *maxs, const gentity_s *gEnt);
"""


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD actor.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = {}
    for signature in SIGNATURES:
        if source.count(signature) != 1:
            raise ValueError("Expected exactly one original definition: " + signature)
        bodies[signature] = function_source(source, signature)

    actor_header = (engine / "src/game/actor.h").read_text(encoding="utf-8")
    for marker in (
        "sizeof(void *) != 4 || sizeof(actor_s) == 0x1e90",
        "sizeof(void *) != 4 || offsetof(actor_s, sentientInfo) == 0x834",
        "sizeof(sentient_info_t) == (sizeof(void *) == 8 ? 0x30 : 0x28)",
    ):
        if actor_header.count(marker) != 1:
            raise ValueError("Native-width actor header contract missing: " + marker)

    nav_header = (engine / "src/game/actor_navigation.h").read_text(encoding="utf-8")
    for marker in (
        "struct actor_goal_s",
        "float pos[3];",
        "float radius;",
        "float height;",
        "pathnode_t *node;",
        "gentity_s *volume;",
    ):
        if marker not in nav_header:
            raise ValueError("Original actor_goal_s field contract missing: " + marker)

    sv_header = (engine / "src/server/sv_game.h").read_text(encoding="utf-8")
    sv_declaration = "bool __cdecl SV_EntityContact(const float *mins, const float *maxs, const gentity_s *gEnt);"
    if sv_header.count(sv_declaration) != 1:
        raise ValueError("SV_EntityContact declaration changed in original server header")

    generated = HEADER + "\n\n".join(bodies.values()) + "\n"
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original actor portability fix missing: " + marker)
    for old_marker in (
        "i += 10",
        "*((unsigned int *)i - 2)",
        "(char *)v2 + 4",
        "(char *)p_scriptGoal + 4",
        "(char *)p_codeGoal + 4",
    ):
        if old_marker in source:
            raise ValueError("32-bit actor record arithmetic remains: " + old_marker)
    if generated.count(SIGNATURES[0]) != 1 or generated.count(SIGNATURES[1]) != 1:
        raise ValueError("Generated actor audit must define both original routines once")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(SIGNATURES),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in bodies.items()
        },
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "sentient_info_clear_uses_native_size": True,
        "known_enemy_region_uses_typed_record_stride": True,
        "actor_goal_copy_uses_native_pointer_width": True,
        "32bit_actor_layout_assertions_guarded": True,
        "original_function_bodies_preserved_verbatim": True,
        "service_stubs_added": False,
        "runtime_executed": False,
        "map_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_ACTOR_POINTER_WIDTH_SOURCE_VERIFIED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
