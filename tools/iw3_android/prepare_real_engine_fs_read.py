#!/usr/bin/env python3
"""Extract authentic file-read helpers for an Android ABI and IWD-branch probe.

The emitted FS_CheckFileSystemStarted, FS_FileForHandle and FS_Read bodies are
verbatim from KisakCOD. Android supplies a native-width fileHandleData_t table
for the isolated ZIP-branch fixture; this is not the original complete open /
close lifecycle and must not be described as a playable runtime.
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
FUNCTIONS = (
    "void __cdecl FS_CheckFileSystemStarted()",
    "FILE *__cdecl FS_FileForHandle(int f)",
    SIGNATURE,
)
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
    bodies = [function_source(text, signature) for signature in FUNCTIONS]
    body = bodies[-1]
    combined = "\n\n".join(bodies)
    for marker in REQUIRED:
        if marker not in combined:
            raise ValueError("Original FS_Read contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in combined:
            raise ValueError("Unexpected replacement implementation marker: " + marker)

    rendered = PROLOGUE + combined + "\n"
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
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(source_body.encode("utf-8")).hexdigest()
            for signature, source_body in zip(FUNCTIONS, bodies)
        },
        "original_fs_read_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "staged_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_FS_CheckFileSystemStarted_body_preserved_exactly": True,
        "original_FS_FileForHandle_body_preserved_exactly": True,
        "original_FS_Read_body_preserved_exactly": True,
        "uses_original_zip_read_and_original_file_read_branches": True,
        "original_upstream_fsh_table_integrated": False,
        "android_native_width_fsh_table_adapter_required": True,
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
