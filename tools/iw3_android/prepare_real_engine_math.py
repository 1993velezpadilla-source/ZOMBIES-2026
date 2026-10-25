#!/usr/bin/env python3
"""Port a *real* KisakCOD SP math translation unit to Android C++.

Phase A: only replace platform-dependent headers in a disposable copy.
NO game implementation statements, coordinate formulas, names or function
bodies are rewritten. This does NOT make the IW3 renderer or game loop run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ENGINE_FILE = Path("src/universal/com_math_anglevectors.cpp")
ORIGINAL_PROLOGUE = (
    '#include <universal/q_shared.h>\n'
    '#include "com_math.h"\n'
)
ORIGINAL_THIRD_HEADER = '#include "q_shared.h"'
REQUIRED_FUNCTIONS = (
    "void __cdecl AngleVectors(",
    "void __cdecl AnglesToAxis(",
    "float __cdecl Vec4Normalize(",
    "void __cdecl AnglesToQuat(",
)

def prepare(source_root: Path, output: Path) -> dict:
    source_root = source_root.resolve()
    dest = output.resolve()
    vendor = (Path(__file__).resolve().parents[2] / "third_party/KisakCOD").resolve()
    if dest == source_root / ENGINE_FILE or dest == vendor / ENGINE_FILE:
        raise ValueError("Refusing to overwrite the original IW3 source file")
    src = source_root / ENGINE_FILE
    if not src.is_file():
        raise ValueError(f"Missing IW3 source: {src}")
    text = src.read_text(encoding="utf-8")
    if not text.startswith(ORIGINAL_PROLOGUE):
        raise ValueError("IW3 source headers changed; refusing a risky patch")
    if text.count(ORIGINAL_THIRD_HEADER) != 1:
        raise ValueError("Original IW3 shared include is missing or duplicated")
    for name in REQUIRED_FUNCTIONS:
        if text.count(name) != 1:
            raise ValueError(f"Expected exactly one original IW3 function: {name}")
    raw_sha = hashlib.sha256(src.read_bytes()).hexdigest()
    body = text[len(ORIGINAL_PROLOGUE):]
    body = body.replace(ORIGINAL_THIRD_HEADER, "", 1)
    # The *only* changes are these source includes. The engine math bodies
    # remain byte-for-byte the original KisakCOD implementation.
    patched = '#include "iw3_android_math_compat.h"\n' + body
    if "z2026_iw3_" in patched:
        raise ValueError("Native wrapper must remain separate from real IW3 source")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(patched, encoding="utf-8")
    if hashlib.sha256(src.read_bytes()).hexdigest() != raw_sha:
        raise RuntimeError("Vendored KisakCOD file was modified")
    return {
        "engine_origin": str(ENGINE_FILE),
        "source_sha256": raw_sha,
        "output_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        "platform_header_replacement_only": True,
        "original_function_bodies_preserved": True,
        "original_iw3_math_functions": list(REQUIRED_FUNCTIONS),
        "native_arm64_library_compiled": False,
        "full_iw3_game_loop_ported": False,
        "renderer_gles_ported": False,
        "android_iw3_apk_exists": False,
        "engine_assets_bundled": False,
        "godot_used": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    options = parser.parse_args()
    evidence = prepare(options.engine, options.output)
    options.report.parent.mkdir(parents=True, exist_ok=True)
    options.report.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("IW3_ANDROID_NATIVE_REAL_SOURCE_PREPARED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
