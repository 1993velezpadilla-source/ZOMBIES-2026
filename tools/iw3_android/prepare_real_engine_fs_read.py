#!/usr/bin/env python3
"""Stage the exact original KisakCOD FS_Read implementation for the Android file-read port.

This deliberately does not invent a replacement read routine. It extracts the
upstream FS_Read body and emits an ABI/dependency report. The output is a
source-stage artifact only until the original file-handle table and open/close
lifecycle are linked into the Android engine target.
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
SIGNATURE = "uint32_t __cdecl FS_Read(uint8_t *buffer, uint32_t len, int h)"
PROLOGUE = '#include "iw3_android_fs_read_compat.h"\n'
REQUIRED = (
    "FS_CheckFileSystemStarted();",
    "if (!h)",
    "if (fsh[h].zipFile)",
    "unzReadCurrentFile(fsh[h].handleFiles.file.z, buffer, len)",
    "FS_FileForHandle(h)",
    "FS_FileRead(buf, remaining, f)",
    'Com_Error(ERR_FATAL, "FS_Read: -1 bytes read");',
)
FORBIDDEN = (
    "fread(buffer",
    "std::fread",
    "AAsset_read",
    "Godot",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    source_path = engine.resolve() / SOURCE
    original = source_path.read_bytes()
    text = original.decode("utf-8")
    body = function_source(text, SIGNATURE)
    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original FS_Read contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Unexpected replacement implementation marker: " + marker)

    rendered = PROLOGUE + body + "\n"
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored original changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "original_fs_read_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "staged_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_FS_Read_body_preserved_exactly": True,
        "uses_original_zip_read_and_original_file_read_branches": True,
        "android_file_handle_table_integrated": False,
        "open_close_lifecycle_integrated": False,
        "compiles_as_standalone_android_game_runtime": False,
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
    print("IW3_ORIGINAL_FS_READ_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
