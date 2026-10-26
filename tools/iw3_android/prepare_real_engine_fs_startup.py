#!/usr/bin/env python3
"""Stage authentic KisakCOD filesystem startup bodies for an ARM64 dependency audit.

This extracts the original FS_RegisterDvars, FS_Startup, FS_SetRestrictions,
FS_IsBasePathValid, and FS_InitFilesystem bodies verbatim. Android path defaults
are supplied by a separate narrow platform adapter. The generated archive is
not linked into the diagnostic APK until the real dvar registry and remaining
engine services are ported.
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
FUNCTIONS = (
    "void FS_RegisterDvars()",
    "void __cdecl FS_Startup(char *gameName)",
    "void __cdecl FS_SetRestrictions()",
    "bool __cdecl FS_IsBasePathValid()",
    "void __cdecl FS_InitFilesystem()",
)
REQUIRED = (
    'Dvar_RegisterString("fs_basepath"',
    'Dvar_RegisterString("fs_homepath"',
    'FS_AddLocalizedGameDirectory((char *)fs_basepath->current.string, (char*)"raw")',
    'FS_AddIwdFilesForGameDirectory(path, szGameFolder);',
    'FS_Startup((char*)"main")',
    'FS_ReadFile("fileSysCheck.cfg", 0) > 0',
    'I_strncpyz(lastValidBase, (char *)fs_basepath->current.string, 256)',
    'I_strncpyz(lastValidGame, (char *)fs_gameDirVar->current.string, 256)',
)
FORBIDDEN = (
    "fs_basepath->current.integer",
    "fs_homepath->current.integer",
    "fs_cdpath->current.integer",
    "fs_basegame->current.integer",
    "fs_gameDirVar->current.integer",
    "Godot",
    "fake FS_Startup",
    "diagnostic FS_Startup stub",
)

HEADER = '#include "iw3_android_fs_startup_compat.h"\n'


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered = HEADER + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original filesystem startup contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Unsafe or 32-bit-only startup code remains: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "original_FS_RegisterDvars_body_preserved_verbatim": True,
        "original_FS_Startup_body_preserved_verbatim": True,
        "original_FS_SetRestrictions_body_preserved_verbatim": True,
        "original_FS_IsBasePathValid_body_preserved_verbatim": True,
        "original_FS_InitFilesystem_body_preserved_verbatim": True,
        "string_dvars_use_native_pointer_members": True,
        "android_data_root_path_adapter_required": True,
        "dvar_registry_linked": False,
        "startup_runtime_invoked": False,
        "licensed_fastfile_or_map_loaded": False,
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
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_FS_STARTUP_STAGED_FOR_ARM64_AUDIT", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
