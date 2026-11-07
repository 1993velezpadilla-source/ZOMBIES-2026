#!/usr/bin/env python3
"""Stage authentic G_RunFrameForEntity bodies for the IW3 ARM64 frame-edge audit.

The bodies are extracted verbatim from the vendored KisakCOD g_main.cpp. Only
narrow declarations are emitted for external engine services; no service body
or gameplay behavior is replaced. This remains a compile/link audit, not a
running Android game.
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

SOURCE = Path("src/game/g_main.cpp")
SIGNATURES = (
    "void __cdecl G_RunFrameForEntityInternal(gentity_s *ent)",
    "void __cdecl G_RunFrameForEntity(gentity_s *ent)",
)
DECLARATIONS = (
    (Path("src/game/g_local.h"), "void __cdecl G_ApplyEntityEq(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl G_RunThink(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl Scr_Notify(gentity_s *ent, unsigned __int16 stringValue, unsigned int paramcount);"),
    (Path("src/game/g_local.h"), "void __cdecl G_DObjCalcPose(gentity_s *ent, int *partBits);"),
    (Path("src/game/g_local.h"), "void __cdecl G_GeneralLink(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl G_FreeEntity(gentity_s *ed);"),
    (Path("src/server/sv_world.h"), "void __cdecl SV_UnlinkEntity(gentity_s *gEnt);"),
    (Path("src/server/sv_game.h"), "void __cdecl SV_XModelDebugBoxes(gentity_s *ent);"),
    (Path("src/server/sv_game.h"), "bool __cdecl SV_DObjExists(gentity_s *ent);"),
    (Path("src/aim_assist/aim_target.h"), "void __cdecl AimTarget_ProcessEntity(gentity_s *ent);"),
    (Path("src/script/scr_stringlist.h"), "void __cdecl Scr_SetString(uint16_t *to, uint32_t from);"),
    (Path("src/sound/snd_public.h"), "extern const dvar_t *snd_enableEq;"),
    (Path("src/game/g_main.h"), "extern const dvar_t *g_debugLocDamage;"),
    (Path("src/universal/q_shared.h"), "inline bool __cdecl Com_IsRagdollTrajectory(const trajectory_t *trajectory)"),
)
PROVIDER_DEFINITIONS = (
    (Path("src/game/g_missile.cpp"), "void __cdecl G_RunMissile(gentity_s *ent)"),
    (Path("src/game/g_items.cpp"), "void __cdecl G_RunItem(gentity_s *ent)"),
    (Path("src/game/g_mover.cpp"), "void __cdecl G_RunMover(gentity_s *ent)"),
)
HEADER = """// Generated from the vendored KisakCOD g_main.cpp. Do not edit.
#include <universal/q_shared.h>
#include <game/g_runframe.h>
#include <bgame/bg_local.h>

// MAX_VEHICLES is verified against the original game/g_main.h declaration.
// Avoid including that broad SP header in this isolated Android ABI audit.
#ifndef MAX_VEHICLES
#define MAX_VEHICLES 64
#endif

void __cdecl G_ApplyEntityEq(gentity_s *ent);
void __cdecl G_RunThink(gentity_s *ent);
void __cdecl Scr_Notify(gentity_s *ent, unsigned __int16 stringValue, unsigned int paramcount);
void __cdecl G_DObjCalcPose(gentity_s *ent, int *partBits);
void __cdecl G_GeneralLink(gentity_s *ent);
void __cdecl G_FreeEntity(gentity_s *ed);
void __cdecl SV_UnlinkEntity(gentity_s *gEnt);
void __cdecl SV_XModelDebugBoxes(gentity_s *ent);
bool __cdecl SV_DObjExists(gentity_s *ent);
void __cdecl AimTarget_ProcessEntity(gentity_s *ent);
void __cdecl Scr_SetString(uint16_t *to, uint32_t from);
void __cdecl G_RunMissile(gentity_s *ent);
void __cdecl G_RunItem(gentity_s *ent);
void __cdecl G_RunMover(gentity_s *ent);
extern const dvar_t *snd_enableEq;
extern const dvar_t *g_debugLocDamage;
"""


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD g_main.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = []
    for signature in SIGNATURES:
        if source.count(signature) != 1:
            raise ValueError("Expected exactly one original definition: " + signature)
        bodies.append(function_source(source, signature))

    declarations_checked = {}
    for relative_path, declaration in DECLARATIONS:
        header_path = engine / relative_path
        header_text = header_path.read_text(encoding="utf-8")
        if header_text.count(declaration) != 1:
            raise ValueError(
                "Original engine declaration missing or ambiguous: "
                + str(relative_path) + ": " + declaration
            )
        declarations_checked[str(relative_path) + "::" + declaration] = True

    provider_definitions_checked = {}
    for relative_path, signature in PROVIDER_DEFINITIONS:
        provider_path = engine / relative_path
        provider_text = provider_path.read_text(encoding="utf-8")
        if provider_text.count(signature) != 1:
            raise ValueError(
                "Original engine provider definition missing or ambiguous: "
                + str(relative_path) + ": " + signature
            )
        # Parse the function too, so a declaration/comment alone cannot satisfy the gate.
        function_source(provider_text, signature)
        provider_definitions_checked[str(relative_path) + "::" + signature] = True

    main_header = (engine / "src/game/g_main.h").read_text(encoding="utf-8")
    if main_header.count("#define MAX_VEHICLES 64") != 1:
        raise ValueError("Expected original MAX_VEHICLES == 64 in game/g_main.h")

    generated = HEADER + "\n\n".join(bodies) + "\n"
    for signature in SIGNATURES:
        if generated.count(signature) != 1:
            raise ValueError("Generated source must define exactly one " + signature)
    required = (
        "G_RunMissile(ent);",
        "G_RunItem(v4);",
        "G_RunMover(ent);",
        "G_RunFrameForEntityInternal(ent);",
        "AimTarget_ProcessEntity(ent);",
        "G_DObjCalcPose(ent, partBits);",
        "SV_XModelDebugBoxes(ent);",
        "Scr_Notify(ent, ent->snd_wait.notifyString, 0);",
    )
    for marker in required:
        if marker not in generated:
            raise ValueError("Original entity-frame contract missing: " + marker)

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
            for signature, body in zip(SIGNATURES, bodies)
        },
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_G_RunFrameForEntity_bodies_preserved_verbatim": True,
        "actual_g_runframe_state_header_used": True,
        "complete_scr_vehicle_layout_header_used": True,
        "external_declarations_verified_against_original_headers": declarations_checked,
        "original_entity_service_definitions_verified": provider_definitions_checked,
        "MAX_VEHICLES_verified_against_original_g_main_h": True,
        "gameplay_service_stubs_added": False,
        "frame_edge_linked": False,
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
    print("IW3_ORIGINAL_G_RUNFRAME_ENTITY_STAGED_FOR_ARM64", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
