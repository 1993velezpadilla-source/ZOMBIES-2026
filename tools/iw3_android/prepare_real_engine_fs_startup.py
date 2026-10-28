#!/usr/bin/env python3
"""Stage authentic KisakCOD filesystem startup bodies for an ARM64 dependency audit.

This extracts the original path builder, directory setup, and FS startup bodies
from KisakCOD. FS_BuildOSPathForThread uses bounded native-width lengths and
fails closed at the 256-byte engine path boundary. Android path defaults are
supplied by a separate narrow platform adapter. The generated archive is
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
    "void __cdecl FS_AddSearchPath(searchpath_s *search)",
    "void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)",
    "void __cdecl FS_AddLocalizedGameDirectory(char *path, char *dir)",
    "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
    "void __cdecl FS_ReplaceSeparators(char *path)",
    "void __cdecl FS_BuildOSPath(const char *base, const char *game, const char *qpath, char *ospath)",
    "void __cdecl FS_BuildOSPathForThread(const char *base, const char *game, const char *qpath, char *ospath, FsThread thread)",
    "void FS_RegisterDvars()",
    "void __cdecl FS_Startup(char *gameName)",
    "void __cdecl FS_SetRestrictions()",
    "bool __cdecl FS_IsBasePathValid()",
    "void __cdecl FS_InitFilesystem()",
)
REQUIRED = (
    'search->dir = (directory_t *)Z_Malloc(sizeof(directory_t), "FS_AddGameDirectory", 3);',
    "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
    "FS_AddIwdFilesForGameDirectory(path, szGameFolder);",
    "numfiles = 0;",
    "if (!list || numfiles <= 0)",
    "qsort(s0, numfiles, sizeof(s0[0]),",
    "ZipFile = FS_LoadZipFile(ospath, s0[i]);",
    "FS_FreeFileList((const char **)list);",
    "FS_AddSearchPath(search);",
    "FS_AddGameDirectory(path, dir, 1, i);",
    "FS_AddGameDirectory(path, dir, 0, 0);",
    "if (!pszLanguage || !pszLanguage[0])",
    "baseLength = boundedLength(base);",
    "gameLength = boundedLength(game);",
    "qpathLength = boundedLength(qpath);",
    "baseLength >= 256 || gameLength >= 256 || qpathLength >= 256",
    "FS_ReplaceSeparators(ospath);",
    'Dvar_RegisterString("fs_basepath"',
    'Dvar_RegisterString("fs_homepath"',
    "homePath = nullptr;",
    'FS_AddLocalizedGameDirectory((char *)fs_basepath->current.string, (char*)"raw")',
    'FS_AddCommands();',
    'FS_Startup((char*)"main")',
    'FS_ReadFile("fileSysCheck.cfg", 0) > 0',
    'I_strncpyz(lastValidBase, (char *)fs_basepath->current.string, 256)',
    'I_strncpyz(lastValidGame, (char *)fs_gameDirVar->current.string, 256)',
)
FORBIDDEN = (
    'Z_Malloc(512, "FS_AddGameDirectory"',
    "uint32_t *v4; // eax",
    "uint32_t v5; // [esp+0h] [ebp-3Ch]",
    "uint32_t v6; // [esp+10h] [ebp-2Ch]",
    "uint32_t v7; // [esp+20h] [ebp-1Ch]",
    'qsort(s0, numfiles, 4u,',
    '*(_DWORD *)v2',
    "fs_basepath->current.integer",
    "fs_homepath->current.integer",
    "fs_cdpath->current.integer",
    "fs_basegame->current.integer",
    "fs_gameDirVar->current.integer",
    "homePath = (char *)RETURN_ZERO32();",
    "Godot",
    "fake FS_Startup",
    "diagnostic FS_Startup stub",
)

HEADER = ('#include "iw3_android_fs_startup_compat.h"\n'
          '#include "iw3_android_iwd_directory_compat.h"\n'
          '#include <cstdint>\n'
          '#include <cstring>\n')


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered_bodies = []
    for signature, body in zip(FUNCTIONS, bodies):
        if signature == "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)":
            # The dependency archive includes the original enumerator. The
            # focused localized-path host test deliberately keeps its narrow
            # service stub so it does not need to fabricate IWD archive state.
            rendered_bodies.append(
                "#if !defined(IW3_FS_STARTUP_HOST_TEST)\n" + body + "\n#endif"
            )
        else:
            rendered_bodies.append(body)
    rendered = HEADER + "\n\n".join(rendered_bodies) + "\n"
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
        "original_FS_AddSearchPath_body_staged_verbatim": True,
        "original_FS_AddGameDirectory_body_staged_verbatim": True,
        "original_FS_AddLocalizedGameDirectory_body_staged_verbatim": True,
        "original_FS_AddIwdFilesForGameDirectory_body_staged_verbatim": True,
        "original_iwd_directory_enumeration_in_startup_archive": True,
        "iwd_directory_scan_fails_closed_on_missing_listing": True,
        "iwd_sort_uses_native_pointer_width": True,
        "original_FS_ReplaceSeparators_body_staged_verbatim": True,
        "original_FS_BuildOSPath_body_staged_verbatim": True,
        "original_FS_BuildOSPathForThread_body_staged_verbatim": True,
        "path_builder_uses_bounded_native_size_lengths": True,
        "path_builder_fails_closed_on_overflow": True,
        "directory_allocation_uses_native_sizeof": True,
        "unsupported_localized_language_fails_closed": True,
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
