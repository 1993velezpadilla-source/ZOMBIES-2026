#!/usr/bin/env python3
"""Stage the two authentic file-comparison functions from KisakCOD qcommon/files.cpp.

The full translation unit includes Windows/D3D renderer headers that cannot be
compiled as an Android object in isolation. This generator preserves the two
original function bodies verbatim and supplies only declarations for their
real engine dependencies, so their LP64 pointer arithmetic can be compiled
against the Android ABI without pretending the whole filesystem runtime links.
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

SOURCE = Path("src/qcommon/files.cpp")
FUNCTIONS = (
    "int __cdecl FS_CompareIwds(char *needediwds, int len, int dlstring)",
    "int __cdecl FS_CompareFFs(char *neededFFs, int len, int dlstring)",
)
REQUIRED = (
    "const char *v7;",
    "v7 = &string[strlen(string) + 1];",
    "static_cast<int>(v7 - v5)",
    "fs_serverReferencedIwdNames",
    "fs_serverReferencedFFCheckSums",
)
FORBIDDEN = (
    "uint32_t v7",
    "(uint32_t)&string",
    "v7 - (_DWORD)v5",
    "Godot",
    "fake FS_CompareIwds",
    "stub FS_CompareFFs",
)
HEADER = '#include "iw3_android_file_comparisons_compat.h"\n'


def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    source_path = engine / SOURCE
    raw = source_path.read_bytes()
    source = raw.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered = HEADER + "\n\n".join(bodies) + "\n"

    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original file-comparison slice missing required marker: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Unsafe/obsolete file-comparison marker remains: " + marker)
    if rendered.count("int __cdecl FS_CompareIwds(") != 1:
        raise ValueError("Expected exactly one original FS_CompareIwds body")
    if rendered.count("int __cdecl FS_CompareFFs(") != 1:
        raise ValueError("Expected exactly one original FS_CompareFFs body")
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD source")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != raw:
        raise RuntimeError("Vendored qcommon/files.cpp changed during extraction")

    return {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for body in bodies],
        "original_function_bodies_preserved_verbatim": True,
        "native_width_pointer_difference_verified": True,
        "full_qcommon_files_translation_unit_compiled": False,
        "full_translation_unit_excluded_because_renderer_headers_are_not_an_android_port": True,
        "runtime_execution_proven": False,
        "fs_startup_invoked": False,
        "real_map_loaded": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("IW3_ORIGINAL_FILE_COMPARISONS_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
