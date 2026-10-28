#!/usr/bin/env python3
"""Stage authentic sentient/path-node services used by G_UpdatePlayerTriggers for ARM64 link auditing.

Function bodies are extracted verbatim from KisakCOD sentient.cpp. The actor
header is checked for Path_IsValidClaimNode's declaration but is not included,
because it embeds 32-bit actor-layout assertions unrelated to these services.
No service implementation or gameplay substitute is generated.
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

SOURCE = Path("src/game/sentient.cpp")
SIGNATURES = (
    "int __cdecl Sentient_NearestNodeDirty(sentient_s *self, bool originChanged)",
    "void __cdecl Sentient_InvalidateNearestNode(sentient_s *self)",
    "void __cdecl Sentient_BanNearNodes(sentient_s *self)",
)
DECLARATIONS = (
    (Path("src/game/sentient.h"), SIGNATURES[0] + ";"),
    (Path("src/game/sentient.h"), SIGNATURES[1] + ";"),
    (Path("src/game/sentient.h"), SIGNATURES[2] + ";"),
    (Path("src/game/actor.h"), "int __cdecl Path_IsValidClaimNode(const pathnode_t *node);"),
    (Path("src/game/pathnode.h"), "int __cdecl Path_NodesInCylinder("),
    (Path("src/game/pathnode.h"), "void __cdecl Path_MarkNodeInvalid(pathnode_t *node, team_t eTeam);"),
    (Path("src/universal/com_math.h"), "float __cdecl Vec2Normalize(vec2r v);"),
)
HEADER = (
    "// Generated from authentic KisakCOD sentient.cpp bodies. Do not edit.\n"
    "#include <game/g_runframe.h>\n"
    "#include <game/sentient.h>\n"
    "#include <game/pathnode.h>\n"
    "#include <universal/com_math.h>\n"
    "int __cdecl Path_IsValidClaimNode(const pathnode_t *node);\n"
    "static_assert(alignof(pathlocal_t) == 128, \"pathlocal_t alignment drift\");\n"
)
REQUIRED = (
    "if ((50 * self->ent->s.number + level.time) % 1000)",
    "self->bNearestNodeValid = 0;",
    "Path_IsValidClaimNode(node)",
    "Path_NodesInCylinder(node->constant.vOrigin, 80.0f, 80.0f, nodes, 64, 270332)",
    "Path_MarkNodeInvalid(pTestNode, eTeam);",
    "Vec2Normalize(delta);",
)

def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD sentient.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = []
    body_hashes = {}
    for signature in SIGNATURES:
        if source.count(signature) != 1:
            raise ValueError("Expected exactly one original definition: " + signature)
        body = function_source(source, signature)
        bodies.append(body)
        body_hashes[signature] = hashlib.sha256(body.encode("utf-8")).hexdigest()

    declarations_checked = {}
    for relative_path, declaration in DECLARATIONS:
        text = (engine / relative_path).read_text(encoding="utf-8")
        if text.count(declaration) != 1:
            raise ValueError("Original declaration missing or ambiguous: "
                             + str(relative_path) + ": " + declaration)
        declarations_checked[str(relative_path) + "::" + declaration] = True

    pathnode_header = (engine / "src/game/pathnode.h").read_text(encoding="utf-8")
    if pathnode_header.count("struct alignas(128) pathlocal_t") != 1:
        raise ValueError("pathlocal_t must retain its portable 128-byte alignment")
    if "struct __declspec(align(128)) pathlocal_t" in pathnode_header:
        raise ValueError("MSVC-only pathlocal_t alignment remains in the original header")

    generated = HEADER + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original sentient service contract missing: " + marker)
    for signature in SIGNATURES:
        if generated.count(signature) != 1:
            raise ValueError("Generated source must define each original service once: " + signature)
    if "return 0;\n}\nvoid __cdecl Sentient_" in generated:
        raise ValueError("Unexpected truncation between original sentient service bodies")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(SIGNATURES),
        "function_body_sha256": body_hashes,
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_function_bodies_preserved_verbatim": True,
        "pathlocal_alignment_128_preserved": True,
        "external_declarations_verified_against_original_headers": declarations_checked,
        "actor_header_included": False,
        "no_stub_service_added": True,
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
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_SENTIENT_TRIGGER_SERVICES_SOURCE_VERIFIED", json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
