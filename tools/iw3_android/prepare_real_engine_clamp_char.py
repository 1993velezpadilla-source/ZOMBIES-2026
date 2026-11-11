#!/usr/bin/env python3
"""Stage the authentic KisakCOD ClampChar provider for ARM64 client-input edge auditing.

The body is extracted verbatim from universal/com_math.cpp. This resolves a
real engine dependency; it is not a replacement input implementation and does
not link or invoke the live Android client.
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

SOURCE = Path("src/universal/com_math.cpp")
SIGNATURE = "signed char ClampChar(int i)"
HEADER = '#include <universal/com_math.h>\n'
REQUIRED = (
    "if (i < -128)",
    "return -128;",
    "if (i > 127)",
    "return 127;",
    "return i;",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_math.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    body = function_source(source, SIGNATURE)
    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original ClampChar contract missing: " + marker)

    rendered = HEADER + "\n" + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD com_math.cpp changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signature": SIGNATURE,
        "function_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "original_ClampChar_body_preserved_verbatim": True,
        "clamps_to_signed_char_min_minus_128": True,
        "clamps_to_signed_char_max_127": True,
        "android_arm64_object_compiled": False,
        "client_input_edge_resolved": False,
        "client_runtime_linked": False,
        "client_runtime_invoked": False,
        "real_map_loaded": False,
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
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_CLAMPCHAR_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
