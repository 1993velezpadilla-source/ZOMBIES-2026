#!/usr/bin/env python3
"""Stage the authentic KisakCOD ClientEndFrame body for an ARM64 frame-edge audit.

The body is extracted verbatim from game/g_active.cpp. All referenced engine
services are declared by their original headers; this generator creates no
gameplay implementations and never overwrites vendored source.
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

SOURCE = Path("src/game/g_active.cpp")
SIGNATURE = "void __cdecl ClientEndFrame(gentity_s *ent)"
DECLARATIONS = (
    (Path("src/game/g_local.h"), "void __cdecl ClientEndFrame(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl P_DamageFeedback(gentity_s *player);"),
    (Path("src/game/g_local.h"), "void __cdecl G_PlayerStateToEntityStateExtrapolate(playerState_s *ps, entityState_s *s, int time, int snap);"),
    (Path("src/game/g_local.h"), "void __cdecl G_UpdateGroundTilt(gclient_s *client);"),
    (Path("src/game/g_local.h"), "void __cdecl G_SetPlayerFixedLink(gentity_s *ent);"),
    (Path("src/game/sentient.h"), "void __cdecl Sentient_UpdateActualChainPos(sentient_s *self);"),
    (Path("src/game/turret.h"), "void __cdecl turret_think_client(gentity_s *self);"),
    (Path("src/game/player_use.h"), "void __cdecl Player_UpdateCursorHints(gentity_s *ent);"),
    (Path("src/game/player_use.h"), "void __cdecl Player_UpdateLookAtEntity(gentity_s *ent);"),
    (Path("src/game/g_main.h"), "extern level_locals_t level;"),
)
HEADER = """// Generated from the vendored KisakCOD ClientEndFrame body. Do not edit.
#include <universal/q_shared.h>
#include <game/g_level.h>
#include <game/g_local.h>
#include <game/sentient.h>
#include <game/turret.h>
#include <game/player_use.h>

// The level global declaration is verified against the original g_main.h.
extern level_locals_t level;
"""
REQUIRED = (
    "void __cdecl ClientEndFrame(gentity_s *ent)",
    "turret_think_client(&level.gentities[ent->client->ps.viewlocked_entNum]);",
    "G_SetPlayerFixedLink(ent);",
    "G_UpdateGroundTilt(ent->client);",
    "Sentient_UpdateActualChainPos(ent->sentient);",
    "Player_UpdateLookAtEntity(ent);",
    "Player_UpdateCursorHints(ent);",
    "P_DamageFeedback(ent);",
    "G_PlayerStateToEntityStateExtrapolate(&v8->ps, &ent->s, v8->ps.commandTime, 1);",
    "ent->client->buttonsSinceLastFrame = 0;",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD g_active.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    if source.count(SIGNATURE) != 1:
        raise ValueError("Expected exactly one original ClientEndFrame definition")
    body = function_source(source, SIGNATURE)

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

    generated = HEADER + "\n" + body + "\n"
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original ClientEndFrame contract missing: " + marker)
    if generated.count(SIGNATURE) != 1:
        raise ValueError("Generated source must define ClientEndFrame exactly once")
    if "void __cdecl ClientThink(" in body or "void __cdecl G_UpdatePlayer(" in body:
        raise ValueError("Unexpected adjacent function body in ClientEndFrame source slice")

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
        "original_ClientEndFrame_body_preserved_verbatim": True,
        "level_global_declaration_verified_against_original_g_main_h": True,
        "external_declarations_verified_against_original_headers": declarations_checked,
        "client_end_frame_service_stubs_added": False,
        "frame_edge_linked": False,
        "runtime_executed": False,
        "real_map_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_CLIENT_END_FRAME_STAGED_FOR_ARM64", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
