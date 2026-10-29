#!/usr/bin/env python3
"""Extract the authentic SP mover physics chain and native-width pushed state."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/game/g_mover.cpp")
TEAM_SIGNATURE = "void __cdecl G_MoverTeam(gentity_s *ent)"
TRACK_SIGNATURE = "void __cdecl TRACK_g_mover()"
FUNCTION_SIGNATURES = (
    "gentity_s *__cdecl G_TestEntityPosition(gentity_s *ent, float *vOrigin)",
    "void __cdecl G_CreateRotationMatrix(const float *angles, float (*matrix)[3])",
    "void __cdecl G_TransposeMatrix(float (*matrix)[3], float (*transpose)[3])",
    "void __cdecl G_RotatePoint(float *point, float (*matrix)[3])",
    "int __cdecl G_TryPushingEntity(gentity_s *check, gentity_s *pusher, float *move, float *amove)",
    "char __cdecl G_MoverPush(gentity_s *pusher, float *move, float *amove, gentity_s **obstacle)",
    TEAM_SIGNATURE,
)
GLOBAL_DECLARATIONS = ("pushed_t pushed[1024];", "pushed_t *pushed_p;")
HEADER = """// Generated from authentic KisakCOD g_mover.cpp bodies. Do not edit.
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
#include <game/actor_orientation.h>
#include <game/sentient.h>
#include <server/sv_world.h>
#include <universal/com_math.h>

// Exact upstream declaration from g_main.h; entityHandler_t is defined in g_local.h.
extern struct entityHandler_t entityHandlers[27];
"""


def struct_source(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError("Expected exactly one original definition: " + signature)
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                end = source.index(";", index) + 1
                return source[start:end]
    raise ValueError("Unbalanced original struct: " + signature)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD g_mover.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = {}
    for signature in FUNCTION_SIGNATURES:
        if source.count(signature) != 1:
            raise ValueError("Expected exactly one original definition: " + signature)
        bodies[signature] = function_source(source, signature)
    track_body = function_source(source, TRACK_SIGNATURE)
    pushed_struct = struct_source(source, "struct pushed_t")

    for declaration in GLOBAL_DECLARATIONS:
        if source.count(declaration) != 1:
            raise ValueError("Expected one original mover state declaration: " + declaration)
    if 'track_static_alloc_internal(pushed, sizeof(pushed), "pushed", 9);' not in track_body:
        raise ValueError("Mover allocation tracker must use sizeof(pushed)")
    if 'track_static_alloc_internal(pushed, 45056, "pushed", 9);' in track_body:
        raise ValueError("32-bit pushed allocation byte count remains")

    main_header = (engine / "src/game/g_main.h").read_text(encoding="utf-8")
    if main_header.count("extern struct entityHandler_t entityHandlers[27];") != 1:
        raise ValueError("Original entityHandlers declaration changed in g_main.h")
    local_header = (engine / "src/game/g_local.h").read_text(encoding="utf-8")
    if local_header.count("struct entityHandler_t") != 1:
        raise ValueError("Original entityHandler_t definition changed in g_local.h")

    team_body = bodies[TEAM_SIGNATURE]
    mover_push_signature = FUNCTION_SIGNATURES[5]
    mover_push_body = bodies[mover_push_signature]
    if "G_MoverPush(ent, move, amove, &obstacle)" not in team_body:
        raise ValueError("Original G_MoverTeam -> G_MoverPush call changed")
    if "G_TryPushingEntity" not in mover_push_body or "G_TestEntityPosition" not in mover_push_body:
        raise ValueError("Original G_MoverPush physics helper chain changed")
    if "Actor_ClearPath(p->ent->actor);" not in team_body:
        raise ValueError("Single-player actor path invalidation was not preserved")
    if "Sentient_InvalidateNearestNode(p->ent->actor->sentient);" not in team_body:
        raise ValueError("Single-player sentient invalidation was not preserved")

    generated = (
        HEADER + pushed_struct + "\n"
        + 'static_assert(sizeof(pushed_t) == (sizeof(void *) == 8 ? 0x30 : 0x2C), '
          '"pushed_t native pointer-width layout drift");\n\n'
        + "\n".join(GLOBAL_DECLARATIONS) + "\n\n"
        + "\n\n".join(bodies[signature] for signature in FUNCTION_SIGNATURES) + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in bodies.items()
        },
        "pushed_t_struct_sha256": hashlib.sha256(pushed_struct.encode("utf-8")).hexdigest(),
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_function_bodies_preserved_verbatim": True,
        "original_pushed_t_layout_preserved": True,
        "pushed_array_and_cursor_owned_once": True,
        "pushed_tracker_uses_native_sizeof": True,
        "entity_handlers_declared_from_original_header": True,
        "SP_actor_and_sentient_invalidation_preserved": True,
        "G_MoverPush_and_physics_helpers_included": True,
        "collision_world_services_remain_external": True,
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
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_G_MOVER_TEAM_SOURCE_VERIFIED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
