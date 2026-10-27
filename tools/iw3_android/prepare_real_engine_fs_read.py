#!/usr/bin/env python3
"""Extract authentic KisakCOD file-handle allocation/open/read/close bodies.

The exact upstream FS_HandleForFile and FS_FOpenFileReadForThread bodies are
compiled into the Android diagnostic with the original FS_Read/FS_FCloseFile
bodies. The handle table comes from the shared engine source
com_files_handle_table.cpp; the Android adapter supplies only narrow platform
services. The complete com_files.cpp translation unit is not linked.
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
SHARED_SOURCE = Path("src/universal/q_shared.cpp")
TABLE_SOURCE = Path("src/universal/com_files_handle_table.cpp")
HEADER_SOURCE = Path("src/universal/com_files.h")
SIGNATURE = "uint32_t __cdecl FS_Read(uint8_t *buffer, uint32_t len, int h)"
GLOBAL_POLICY_SIGNATURE = "char __cdecl FS_FilesAreLoadedGlobally(const char *filename)"
FUNCTIONS = (
    ("int __cdecl FS_filelength(int f)", SOURCE),
    ("int __cdecl FS_HandleForFile(FsThread thread)", SOURCE),
    ("FILE *__cdecl FS_FileForHandle(int f)", SOURCE),
    ("uint32_t __cdecl FS_FOpenFileReadForThread(const char *filename, int *file, FsThread thread)", SOURCE),
    ("BOOL __cdecl FS_PureIgnoresExtension(const char *extension)", SOURCE),
    (GLOBAL_POLICY_SIGNATURE, SOURCE),
    ("int __cdecl FS_IwdIsPure(iwd_t *iwd)", SOURCE),
    ("bool __cdecl FS_GameDirDomainFunc(dvar_s *dvar, DvarValue newValue)", SOURCE),
    (SIGNATURE, SOURCE),
    ("void __cdecl FS_FCloseFile(int h)", SOURCE),
    ("const char *__cdecl I_stristr(const char *s0, const char *substr)", SHARED_SOURCE),
    ("int __cdecl I_stricmpwild(const char *wild, const char *s)", SHARED_SOURCE),
    ("const char *__cdecl Com_GetExtensionSubString(const char *filename)", SHARED_SOURCE),
)
PROLOGUE = (
    '#include "iw3_android_fs_read_compat.h"\n'
    '#include <ctype.h>\n'
    '#define FS_FileOpenReadBinary z2026_iw3_lookup_file_open_read_binary\n'
    '#define FS_FileGetFileSize z2026_iw3_fs_file_get_size\n'
    '#define FS_CopyFile z2026_iw3_fs_copy_file\n'
    '#define SEH_SafeTranslateString z2026_iw3_safe_translate\n'
    '#define InterlockedCompareExchange z2026_iw3_interlocked_compare_exchange\n'
    '#define IsFastFileLoad z2026_iw3_is_fastfile_load\n'
    '#define Sys_IsDatabaseThread z2026_iw3_is_database_thread\n'
)
REQUIRED = (
    "*file = FS_HandleForFile(thread);",
    "unzReOpen(iwd->iwdFilename, iwd->handle)",
    "InterlockedCompareExchange(&iwd->hasOpenFile, 1, 0)",
    "fsh[*file].handleFiles.file.z = iwd->handle;",
    "return zfi->cur_file_info.uncompressed_size;",
    "return unzReadCurrentFile(fsh[h].handleFiles.file.z, buffer, len);",
    "FS_FileRead(buf, remaining, f)",
    "return FS_FileGetFileSize(h);",
    "unzCloseCurrentFile(fsh[h].handleFiles.file.z);",
    "Com_Memset((uint32_t *)&fsh[h], 0, sizeof(fsh[h]));",
    "FS_FilesAreLoadedGlobally(sanitizedName)",
    "const size_t extensionLen = strlen(extensions[extensionNum]);",
    "if (filenameLen >= extensionLen &&",
    "FS_IwdIsPure(iwd)",
    "return !I_stricmp(extension, \"cfg\")",
    "const char *__cdecl Com_GetExtensionSubString(const char *filename)",
    "v3 = tolower(static_cast<unsigned char>(s0[substrChar + s0Char]));",
    "v3 = tolower(static_cast<unsigned char>(charWild));",
    "delta = v3 - tolower(static_cast<unsigned char>(charRef));",
    "tolower(static_cast<unsigned char>(substr[substrChar]))",
)
FORBIDDEN = (
    "filenameLen - strlen(extensions[extensionNum])",
    "z2026_iw3_original_searchpath_lookup",
    "return -1; // non-null handle path is intentionally outside this probe",
    "Com_Memset((uint32_t *)&fsh[h], 0, 284);",
    "AAsset_read",
    "Godot",
    "tolower(s0[substrChar + s0Char])",
    "tolower(substr[substrChar])",
    "tolower(charWild)",
    "tolower(charRef)",
)


def definition_source(source: str, signature: str) -> str:
    """Remove declaration-only matches so the exact single upstream body is extracted."""
    positions = []
    cursor = 0
    while True:
        position = source.find(signature, cursor)
        if position < 0:
            break
        positions.append(position)
        cursor = position + len(signature)
    definitions = []
    prototypes = []
    for position in positions:
        after = position + len(signature)
        while after < len(source) and source[after].isspace():
            after += 1
        if after < len(source) and source[after] == "{":
            definitions.append(position)
        elif after < len(source) and source[after] == ";":
            prototypes.append(position)
    if len(definitions) != 1:
        raise ValueError("Expected one original IW3 definition for " + signature)
    filtered = source
    for position in reversed(prototypes):
        filtered = filtered[:position] + filtered[position + len(signature):]
    return function_source(filtered, signature)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_paths = {source_path for _, source_path in FUNCTIONS}
    source_bytes = {source_path: (engine / source_path).read_bytes()
                    for source_path in source_paths}
    output = output.resolve()
    if output in {(engine / source_path).resolve() for source_path in source_paths}:
        raise ValueError("Refusing to overwrite authentic KisakCOD source")
    source_text = {source_path: raw.decode("utf-8")
                   for source_path, raw in source_bytes.items()}
    table_bytes = (engine / TABLE_SOURCE).read_bytes()
    header_bytes = (engine / HEADER_SOURCE).read_bytes()
    table_text = table_bytes.decode("utf-8")
    header_text = header_bytes.decode("utf-8")
    if "extern fileHandleData_t fsh[65];" not in header_text:
        raise ValueError("Original com_files.h must declare the shared fsh table")
    if "fileHandleData_t fsh[65] = {};" not in table_text:
        raise ValueError("Shared engine handle-table definition is missing")
    if "static fileHandleData_t fsh[65]" in source_text[SOURCE]:
        raise ValueError("com_files.cpp still owns a private static fsh table")
    bodies = [definition_source(source_text[source_path], signature)
              for signature, source_path in FUNCTIONS]
    combined = "\n\n".join(bodies) + "\n"
    domain_signature = "bool __cdecl FS_GameDirDomainFunc(dvar_s *dvar, DvarValue newValue)"
    domain_index = next(i for i, (signature, _) in enumerate(FUNCTIONS)
                        if signature == domain_signature)
    domain_body = bodies[domain_index]
    for marker in (
        "if (!newValue.string[0])",
        "newValue.string[4] != '/'",
        'strstr(newValue.string, "..")',
        'strstr(newValue.string, "::")',
    ):
        if marker not in domain_body:
            raise ValueError("Original game-directory validator lost native-width string access: " + marker)
    if "newValue.integer" in domain_body or "(int)strstr" in domain_body:
        raise ValueError("Original game-directory validator truncates a string pointer")
    for marker in REQUIRED:
        if marker not in combined:
            raise ValueError("Original FS lifecycle contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in combined:
            raise ValueError("Unexpected replacement/lookup-only marker: " + marker)

    rendered = PROLOGUE + combined
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    for source_path, original in source_bytes.items():
        if (engine / source_path).read_bytes() != original:
            raise RuntimeError("Vendored original changed during staging: " + str(source_path))

    hashes = {signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
              for (signature, _), body in zip(FUNCTIONS, bodies)}
    evidence = {
        "source_sha256": {str(source_path): hashlib.sha256(raw).hexdigest()
                          for source_path, raw in source_bytes.items()},
        "function_signatures": [signature for signature, _ in FUNCTIONS],
        "function_body_sha256": hashes,
        "original_FS_filelength_body_preserved_exactly": True,
        "original_handle_allocation_body_preserved_exactly": True,
        "original_FS_FOpenFileReadForThread_body_preserved_exactly": True,
        "original_FS_FileForHandle_body_preserved_exactly": True,
        "original_FS_Read_body_preserved_exactly": True,
        "original_FS_FCloseFile_body_preserved_exactly": True,
        "original_extension_and_purity_helpers_preserved_exactly": True,
        "original_FS_GameDirDomainFunc_body_preserved_exactly": True,
        "original_FS_GameDirDomainFunc_uses_native_width_string_member": True,
        "original_FS_FilesAreLoadedGlobally_guards_short_suffixes": True,
        "game_directory_domain_validator_runtime_executed": False,
        "full_original_open_read_close_lifecycle_compiled_into_diagnostic": True,
        "engine_shared_fsh_table_source_present": True,
        "engine_shared_fsh_table_source_sha256": hashlib.sha256(table_bytes).hexdigest(),
        "full_original_com_files_translation_unit_linked": False,
        "report_is_static_staging_audit": True,
        "runtime_handle_path_executed": False,
        "fastfile_map_loading_proven": False,
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
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_FS_OPEN_READ_CLOSE_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
