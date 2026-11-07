#!/usr/bin/env python3
"""Stage the authentic KisakCOD G_UpdatePlayer body for an ARM64 frame-link audit.

The body is extracted verbatim from game/g_active.cpp. Its three external
services are declarations checked against the engine's real headers, not stubs.
This is a relocatable-link milestone only; it does not execute a game frame.
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
SIGNATURE = "void __cdecl G_UpdatePlayer(gentity_s *ent)"
DECLARATIONS = (
    (Path("src/server/server.h"), "bool __cdecl SV_ReadPacket(int framePos);"),
    (Path("src/client/cl_input.h"), "void __cdecl CL_WritePacket();"),
    (Path("src/game/sentient.h"), "void __cdecl Sentient_UpdatePlayerTrail(gentity_s *ent);"),
)
HEADER = (
    "// Generated from the vendored KisakCOD G_UpdatePlayer body. Do not edit.\n"
    "#include <game/g_runframe.h>\n"
    "// ABI declarations are validated against the original engine headers.\n"
    "bool __cdecl SV_ReadPacket(int framePos);\n"
    "void __cdecl CL_WritePacket();\n"
    "void __cdecl Sentient_UpdatePlayerTrail(gentity_s *ent);\n"
)
REQUIRED = (
    "void __cdecl G_UpdatePlayer(gentity_s *ent)",
    "if (ent->r.inuse)",
    "v2 = ++level.framePos;",
    "if (level.demoplaying)",
    "level.demoplaying = SV_ReadPacket(v2);",
    "CL_WritePacket();",
    "Sentient_UpdatePlayerTrail(ent);",
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
        raise ValueError("Expected exactly one original G_UpdatePlayer definition")
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
        declarations_checked[str(relative_path)] = declaration

    generated = HEADER + "\n" + body + "\n"
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original G_UpdatePlayer contract missing: " + marker)
    if generated.count(SIGNATURE) != 1:
        raise ValueError("Generated source must define G_UpdatePlayer exactly once")
    if "G_UpdatePlayerTriggers" in body or "void __cdecl CL_WritePacket()" in body:
        raise ValueError("Unexpected extra function body in G_UpdatePlayer source slice")

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
        "original_G_UpdatePlayer_body_preserved_verbatim": True,
        "actual_g_runframe_state_header_used": True,
        "external_declarations_verified_against_original_headers": declarations_checked,
        "CL_WritePacket_provider_is_stub": False,
        "SV_ReadPacket_provider_is_stub": False,
        "Sentient_UpdatePlayerTrail_provider_is_stub": False,
        "frame_edge_linked": False,
        "runtime_executed": False,
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
    print("IW3_ORIGINAL_G_UPDATE_PLAYER_STAGED_FOR_ARM64", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
