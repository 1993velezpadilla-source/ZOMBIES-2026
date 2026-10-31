#!/usr/bin/env python3
"""Stage the authentic KisakCOD G_UpdatePlayerTriggers body for an ARM64 frame-link audit.

The body is extracted verbatim from game/g_active.cpp. This is a compile/link
milestone only; the referenced sentient, path-node and trigger services remain
real unresolved engine dependencies until their original providers are linked.
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
SIGNATURE = "void __cdecl G_UpdatePlayerTriggers(gentity_s *ent)"
DECLARATIONS = (
    (Path("src/game/g_local.h"), "void __cdecl G_UpdatePlayerTriggers(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl Client_ClaimNode(gentity_s *ent);"),
    (Path("src/game/g_local.h"), "void __cdecl G_DoTouchTriggers(gentity_s *ent);"),
    (Path("src/game/sentient.h"), "void __cdecl Sentient_InvalidateNearestNode(sentient_s *self);"),
    (Path("src/game/sentient.h"), "void __cdecl Sentient_BanNearNodes(sentient_s *self);"),
    (Path("src/game/sentient.h"), "int __cdecl Sentient_NearestNodeDirty(sentient_s *self, bool originChanged);"),
    (Path("src/universal/com_math.h"), "float __cdecl Vec2DistanceSq(const vec2r p1, const vec2r p2);"),
)
HEADER = (
    "// Generated from the vendored KisakCOD G_UpdatePlayerTriggers body. Do not edit.\n"
    "#include <game/g_runframe.h>\n"
    "#include <game/g_local.h>\n"
    "#include <game/sentient.h>\n"
    "#include <universal/com_math.h>\n"
)
REQUIRED = (
    "void __cdecl G_UpdatePlayerTriggers(gentity_s *ent)",
    "if (ent->r.inuse)",
    "Vec2DistanceSq(ent->r.currentOrigin, ent->sentient->oldOrigin)",
    "Sentient_NearestNodeDirty(ent->sentient, v3 == 0)",
    "Sentient_InvalidateNearestNode(ent->sentient)",
    "Client_ClaimNode(ent);",
    "Sentient_BanNearNodes(ent->sentient);",
    "G_DoTouchTriggers(ent);",
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
        raise ValueError("Expected exactly one original G_UpdatePlayerTriggers definition")
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
            raise ValueError("Original G_UpdatePlayerTriggers contract missing: " + marker)
    if generated.count(SIGNATURE) != 1:
        raise ValueError("Generated source must define G_UpdatePlayerTriggers exactly once")
    if "void __cdecl G_UpdatePlayer(gentity_s *ent)" in body:
        raise ValueError("Unexpected G_UpdatePlayer body in G_UpdatePlayerTriggers source slice")

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
        "original_G_UpdatePlayerTriggers_body_preserved_verbatim": True,
        "actual_g_runframe_state_header_used": True,
        "external_declarations_verified_against_original_headers": declarations_checked,
        "sentient_path_and_trigger_services_are_stubs": False,
        "frame_edge_linked": False,
        "runtime_executed": False,
        "map_loaded": False,
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
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_G_UPDATE_PLAYER_TRIGGERS_SOURCE_VERIFIED", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
