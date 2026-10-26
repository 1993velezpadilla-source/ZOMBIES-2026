#!/usr/bin/env python3
"""Extract the authentic IW3 location-filter function for native ABI compilation.

The output preserves FS_ListFilteredFilesInLocation verbatim from vendored
KisakCOD. It is compiled as a separate static audit archive: its original
Hunk and file-list services remain unresolved, and it is not linked into JNI.
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

SOURCE = Path("src/universal/com_files.cpp")
SIGNATURE = "const char **__cdecl FS_ListFilteredFilesInLocation("
HEADER = '#include "iw3_android_filtered_files_compat.h"\n'
ALLOCATION = (
    "Hunk_UserAlloc(user, sizeof(searchpath_s), "
    "static_cast<int>(alignof(searchpath_s)))"
)
REQUIRED = (
    'user = Hunk_UserCreate(0x20000, "FS_ListFilteredFilesInLocation", 0, 0, 3);',
    "if (FS_CheckLocation(pathDir, lookInFlags))",
    ALLOCATION,
    "result = FS_ListFilteredFiles(locationSearchPath, path, extension, filter, behavior, numfiles);",
    "Hunk_UserDestroy(user);",
)
FORBIDDEN = (
    "Hunk_UserAlloc(user, 0x1Cu, 4)",
    "Hunk_UserAlloc(user, 0x1C, 4)",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")

    original = source_path.read_bytes()
    source_text = original.decode("utf-8")
    body = function_source(source_text, SIGNATURE)
    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original location-filter contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Win32-sized allocation remains in original body: " + marker)
    if body.count(ALLOCATION) != 2:
        raise ValueError("Expected both native-width searchpath allocations")

    rendered = HEADER + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored original changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "original_function_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_function_body_preserved_verbatim": True,
        "native_size_and_alignment_allocations": 2,
        "win32_fixed_size_allocations": 0,
        "source_staged_for_host_and_arm64_compile": True,
        "runtime_execution_proven": False,
        "full_filesystem_runtime_linked": False,
        "fastfile_map_loading_proven": False,
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
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_FILTERED_FILES_LOCATION_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
