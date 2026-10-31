#!/usr/bin/env python3
"""Stage the authentic SP G_RunMover body for the Android ARM64 frame-edge audit.

This extracts upstream gameplay code verbatim. It does not add service stubs,
link the game runtime, or claim that a mover executes in Android.
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

SOURCE = Path("src/game/g_mover.cpp")
SIGNATURE = "void __cdecl G_RunMover(gentity_s *ent)"
MOVER_TEAM_SIGNATURE = "void __cdecl G_MoverTeam(gentity_s *ent)"

HEADER = """// Generated from the vendored KisakCOD g_mover.cpp. Do not edit.
#include <universal/q_shared.h>
#include <game/game_public.h>
#include <game/g_local.h>

// Keep this isolated source surface narrow. The broad server/client headers
// pulled in by sv_game.h, sv_public.h, g_main.h and actor.h expose Win32-only
// declarations (_iobuf and __declspec(align)) that G_RunMover does not need.
void __cdecl G_MoverTeam(gentity_s *ent);
void __cdecl SV_LinkEntity(gentity_s *gEnt);
"""

def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD g_mover.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    if source.count(SIGNATURE) != 1:
        raise ValueError("Expected exactly one original definition: " + SIGNATURE)
    if source.count(MOVER_TEAM_SIGNATURE) != 1:
        raise ValueError("Expected exactly one original provider definition: " + MOVER_TEAM_SIGNATURE)

    body = function_source(source, SIGNATURE)
    # Parse the actual provider too; a declaration or comment alone is not evidence.
    mover_team_body = function_source(source, MOVER_TEAM_SIGNATURE)
    generated = HEADER + "\n" + body + "\n"
    if generated.count(SIGNATURE) != 1:
        raise ValueError("Generated source must define exactly one original G_RunMover")
    for marker in (
        "G_Animscripted_Think(ent);",
        "G_SetOrigin(ent, ent->r.currentOrigin);",
        "G_SetAngle(ent, ent->r.currentAngles);",
        "G_MoverTeam(ent);",
        "G_RunThink(ent);",
    ):
        if marker not in generated:
            raise ValueError("Original G_RunMover contract missing: " + marker)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signature": SIGNATURE,
        "function_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_G_RunMover_body_preserved_verbatim": True,
        "G_MoverTeam_original_definition_verified": True,
        "G_MoverTeam_body_sha256": hashlib.sha256(mover_team_body.encode("utf-8")).hexdigest(),
        "G_MoverTeam_body_included": False,
        "gameplay_service_stubs_added": False,
        "G_RunMover_frame_edge_linked": False,
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
    print("IW3_ORIGINAL_G_RUNMOVER_STAGED_FOR_ARM64", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
