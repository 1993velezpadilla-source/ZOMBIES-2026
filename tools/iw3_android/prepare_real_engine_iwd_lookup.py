#!/usr/bin/env python3
"""Stage the authentic lookup-only prefix of KisakCOD FS_FOpenFileReadForThread.

The extracted prefix ends immediately before handle allocation. It preserves
the original sanitizer and searchpath lookup branch verbatim, including the
IWD hash/name walk and directory fallback. It does NOT implement file handles
or FS_Read, and must never be described as a complete file-read port.
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
OPEN_SIGNATURE = (
    "uint32_t __cdecl FS_FOpenFileReadForThread("
    "const char *filename, int *file, FsThread thread)"
)
FUNCTIONS = (
    ("void __cdecl FS_CheckFileSystemStarted()", SOURCE),
    ("bool __cdecl FS_IsBackupSubStr(const char *filenameSubStr)", SOURCE),
    ("char __cdecl FS_SanitizeFilename(const char *filename, char *sanitizedName, int sanitizedNameSize)\n{", SOURCE),
    ("BOOL __cdecl FS_UseSearchPath(const searchpath_s *pSearch)\n{", SOURCE),
    ("void __cdecl FS_BuildOSPathForThread(const char *base, const char *game, const char *qpath, char *ospath, FsThread thread)", SOURCE),
)
HEADER = '#include "iw3_android_iwd_lookup_compat.h"\n'
GLOBALS = (
    "static dvar_s g_z2026_fs_ignore_localized{};\n"
    "const dvar_s *fs_ignoreLocalized = &g_z2026_fs_ignore_localized;\n"
)
PREFIX_START = "    if (!filename)"
PREFIX_END = "    *file = FS_HandleForFile(thread);"
REQUIRED = (
    "FS_CheckFileSystemStarted();",
    "if (!FS_SanitizeFilename(filename, sanitizedName, 256))",
    "if (!file)",
    "if (FS_UseSearchPath(search))",
    "FS_HashFileName(sanitizedName, search->iwd->hashSize)",
    "FS_FilenameCompare(iwdFile->name, sanitizedName)",
    "FS_BuildOSPathForThread(dir->path, dir->gamedir, sanitizedName, netpath, thread);",
    "filetemp = FS_FileOpenReadBinary(netpath);",
    "FS_FileClose(filetemp);",
    "return 1;",
    "return -1;",
)
FORBIDDEN = (
    "FS_HandleForFile(thread)",
    "fsh[*file]",
    "FS_Read(",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    original = source_path.read_bytes()
    text = original.decode("utf-8")
    full_function = function_source(text, OPEN_SIGNATURE)
    start = full_function.find(PREFIX_START)
    end = full_function.find(PREFIX_END, start)
    if start < 0 or end < 0:
        raise ValueError("Original FS_FOpenFileReadForThread lookup boundary changed")
    prefix = full_function[start:end]
    for marker in REQUIRED:
        if marker not in prefix:
            raise ValueError("Original file lookup contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in prefix:
            raise ValueError("Lookup-only extraction crossed into handle/read path: " + marker)

    bodies = [function_source(text, signature) for signature, _ in FUNCTIONS]
    rendered = (
        HEADER + GLOBALS + "\n\n".join(bodies) + "\n\n"
        "extern \"C\" int z2026_iw3_original_searchpath_lookup(\n"
        "        const char *filename, int *file, FsThread thread) {\n"
        "    char sanitizedName[256] = {};\n"
        "    char netpath[256] = {};\n"
        "    fileInIwd_s *iwdFile = nullptr;\n"
        "    directory_t *dir = nullptr;\n"
        "    int hash = 0;\n"
        "    const char *impureIwd = nullptr;\n"
        "    bool wasSkipped = false;\n"
        "    iwd_t *iwd = nullptr;\n"
        "    FILE *filetemp = nullptr;\n"
        "    searchpath_s *search = nullptr;\n"
        + prefix +
        "    return -1; // non-null handle path is intentionally outside this probe\n"
        "}\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored original changed during staging")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "original_function_sha256": hashlib.sha256(full_function.encode("utf-8")).hexdigest(),
        "lookup_prefix_sha256": hashlib.sha256(prefix.encode("utf-8")).hexdigest(),
        "helper_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_searchpath_lookup_prefix_preserved_verbatim": True,
        "original_filename_sanitizer_preserved": True,
        "original_iwd_hash_and_filename_compare_used": True,
        "directory_fallback_uses_original_os_path_builder_and_rooted_file_adapter": True,
        "file_handle_allocation_ported": False,
        "original_FS_Read_ported": False,
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
    print("IW3_ORIGINAL_FILE_SEARCHPATH_LOOKUP_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
