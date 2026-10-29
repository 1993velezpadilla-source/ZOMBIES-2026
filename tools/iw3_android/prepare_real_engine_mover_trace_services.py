#!/usr/bin/env python3
"""Stage authentic IW3 trace services needed by the original mover physics chain.

Function bodies are copied verbatim from vendored KisakCOD. This creates a
compile/link audit object only; SV_Trace and SV_SetupIgnoreEntParams remain
real unresolved world-runtime services. It is not an Android game runtime.
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

GAME_SOURCE = Path("src/game/g_main.cpp")
TRACE_SOURCE = Path("src/qcommon/cm_trace.cpp")
WORLD_HEADER = Path("src/server/sv_world.h")
QCOMMON_HEADER = Path("src/qcommon/qcommon.h")

G_TRACE_SIGNATURE = "void __cdecl G_TraceCapsule("
TRACE_HIT_ID_SIGNATURE = "uint16_t __cdecl Trace_GetEntityHitId(const trace_t *trace)"

HEADER = """// Generated from original KisakCOD IW3 trace functions. Do not edit.
#include <universal/q_shared.h>
#include <qcommon/qcommon.h>
#include <game/game_public.h>
#include <server/sv_world.h>
#include <universal/profile.h>
#include <universal/assertive.h>
"""


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    game_path = engine / GAME_SOURCE
    trace_path = engine / TRACE_SOURCE
    output = output.resolve()
    if output in (game_path.resolve(), trace_path.resolve()):
        raise ValueError("Refusing to overwrite authentic KisakCOD source")

    game_bytes = game_path.read_bytes()
    trace_bytes = trace_path.read_bytes()
    game_source = game_bytes.decode("utf-8")
    trace_source = trace_bytes.decode("utf-8")
    if game_source.count(G_TRACE_SIGNATURE) != 1:
        raise ValueError("Expected exactly one original G_TraceCapsule definition")
    if trace_source.count(TRACE_HIT_ID_SIGNATURE) != 1:
        raise ValueError("Expected exactly one original Trace_GetEntityHitId definition")

    g_trace_body = function_source(game_source, G_TRACE_SIGNATURE)
    trace_hit_id_body = function_source(trace_source, TRACE_HIT_ID_SIGNATURE)

    world_header = (engine / WORLD_HEADER).read_text(encoding="utf-8")
    for marker in (
        "void __cdecl SV_SetupIgnoreEntParams(IgnoreEntParams *ignoreEntParams, int baseEntity);",
        "void __cdecl SV_Trace(",
        "const IgnoreEntParams *ignoreEntParams,",
    ):
        if world_header.count(marker) != 1:
            raise ValueError("Original world-service declaration missing/ambiguous: " + marker)

    qcommon_header = (engine / QCOMMON_HEADER).read_text(encoding="utf-8")
    if qcommon_header.count("struct IgnoreEntParams") != 1:
        raise ValueError("Original IgnoreEntParams layout declaration changed")
    for marker in (
        "trace_t",
        "TRACE_HITTYPE_DYNENT_MODEL",
        "TRACE_HITTYPE_DYNENT_BRUSH",
        "TRACE_HITTYPE_ENTITY",
    ):
        if marker not in qcommon_header:
            raise ValueError("Original trace ABI marker missing from qcommon.h: " + marker)

    for marker in (
        "SV_SetupIgnoreEntParams(&ignoreEntParams, passEntityNum);",
        "SV_Trace(results, start, mins, maxs, end, &ignoreEntParams, contentmask, 0, 0, 0);",
    ):
        if marker not in g_trace_body:
            raise ValueError("Original G_TraceCapsule call sequence changed: " + marker)
    for marker in (
        "trace->hitType == TRACE_HITTYPE_DYNENT_MODEL",
        "trace->hitType == TRACE_HITTYPE_DYNENT_BRUSH",
        "trace->hitType == TRACE_HITTYPE_ENTITY",
        "return trace->hitId;",
        "return ENTITYNUM_NONE;",
    ):
        if marker not in trace_hit_id_body:
            raise ValueError("Original Trace_GetEntityHitId behavior changed: " + marker)

    generated = HEADER + "\n" + g_trace_body + "\n\n" + trace_hit_id_body + "\n"
    if generated.count(G_TRACE_SIGNATURE) != 1:
        raise ValueError("Generated source must define exactly one G_TraceCapsule")
    if generated.count(TRACE_HIT_ID_SIGNATURE) != 1:
        raise ValueError("Generated source must define exactly one Trace_GetEntityHitId")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if game_path.read_bytes() != game_bytes or trace_path.read_bytes() != trace_bytes:
        raise RuntimeError("Vendored KisakCOD sources changed during extraction")

    evidence = {
        "game_source": str(GAME_SOURCE),
        "game_source_sha256": hashlib.sha256(game_bytes).hexdigest(),
        "trace_source": str(TRACE_SOURCE),
        "trace_source_sha256": hashlib.sha256(trace_bytes).hexdigest(),
        "G_TraceCapsule_body_sha256": hashlib.sha256(g_trace_body.encode("utf-8")).hexdigest(),
        "Trace_GetEntityHitId_body_sha256": hashlib.sha256(trace_hit_id_body.encode("utf-8")).hexdigest(),
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_function_bodies_preserved_verbatim": True,
        "original_world_service_declarations_verified": True,
        "original_trace_abi_header_verified": True,
        "G_TraceCapsule_calls_original_SV_SetupIgnoreEntParams_and_SV_Trace": True,
        "Trace_GetEntityHitId_semantics_preserved": True,
        "service_stubs_added": False,
        "SV_Trace_runtime_linked": False,
        "runtime_executed": False,
        "map_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_MOVER_TRACE_SERVICES_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
