#!/usr/bin/env python3
"""Stage the exact original KisakCOD Vec4Compare body for the Android dvar ABI port."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_math.cpp")
SIGNATURE = "bool __cdecl Vec4Compare(const float *a, const float *b)"
REQUIRED = (
    "return *b == *a && b[1] == a[1] && b[2] == a[2] && b[3] == a[3];",
)
FORBIDDEN = ("memcmp(", "std::", "isfinite(", "epsilon")
HEADER = '#include <universal/q_shared.h>\n'


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_math.cpp")
    raw = source_path.read_bytes()
    source = raw.decode("utf-8")
    if source.count(SIGNATURE) != 1:
        raise ValueError("Expected exactly one original Vec4Compare definition")
    body = function_source(source, SIGNATURE)
    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original Vec4Compare semantics missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Unexpected replacement semantics in Vec4Compare: " + marker)
    rendered = HEADER + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != raw:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "function_signature": SIGNATURE,
        "function_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "original_Vec4Compare_body_preserved_verbatim": True,
        "uses_exact_four_component_float_equality": True,
        "android_dvar_dependency_provider_staged": True,
        "full_dvar_runtime_linked": False,
        "renderer_or_gameplay_proven": False,
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
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_DVAR_VEC4_COMPARE_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
