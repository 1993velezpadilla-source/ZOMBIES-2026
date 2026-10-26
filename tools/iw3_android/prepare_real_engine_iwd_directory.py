#!/usr/bin/env python3
"""Stage the authentic KisakCOD IWD directory scanner with Android filesystem adapters.

The FS_AddGameDirectory and FS_AddIwdFilesForGameDirectory, IwdFileLanguage,
FS_PathCmp, iwdsort and I_strncmp bodies are extracted from vendored source. Only the
OS directory enumeration/path services and language/logging boundary are
provided by the Android adapter; this is not a replacement game runtime.
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

FILES = Path("src/universal/com_files.cpp")
SHARED = Path("src/universal/q_shared.cpp")
FUNCTIONS = (
    ("int __cdecl I_strncmp(const char *s0, const char *s1, int n)", SHARED),
    ("char *__cdecl IwdFileLanguage(const char *pszIwdFileName)", FILES),
    ("int __cdecl FS_PathCmp(const char *s1, const char *s2)", FILES),
    ("int __cdecl iwdsort(const char **a, char **b)", FILES),
    ("void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)", FILES),
    ("void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)", FILES),
)
HEADER = (
    '#include "iw3_android_iwd_directory_compat.h"\n'
    '#include <cctype>\n'
    '#include <cstdint>\n'
    '#include <cstring>\n'
)
GLOBALS = (
    "char szIwdLanguageName[2][64];\n"
    "int iString = 0;\n"
    "int bLanguagesListed = 0;\n"
    "char fs_gamedir[256] = {};\n"
)
REQUIRED = (
    "int __cdecl I_strncmp(const char *s0, const char *s1, int n)",
    "char *__cdecl IwdFileLanguage(const char *pszIwdFileName)",
    "int __cdecl FS_PathCmp(const char *s1, const char *s2)",
    "int __cdecl iwdsort(const char **a, char **b)",
    "void __cdecl FS_AddIwdFilesForGameDirectory(char *path, char *pszGameFolder)",
    "void __cdecl FS_AddGameDirectory(char *path, char *dir, int bLanguageDirectory, int iLanguage)",
    "FS_AddIwdFilesForGameDirectory(path, szGameFolder);",
    "I_strncpyz(fs_gamedir, szGameFolder, 256);",
    "numfiles = 0;",
    "if (!list || numfiles <= 0)",
    "qsort(s0, numfiles, sizeof(s0[0]),",
    "ZipFile = FS_LoadZipFile(ospath, s0[i]);",
    "FS_AddSearchPath(search);",
    "FS_FreeFileList((const char **)list);",
)
FORBIDDEN = (
    '*(_DWORD *)v2',
    '*((_DWORD *)v2 + 1)',
    '*((_WORD *)v2 + 4)',
    'qsort(s0, numfiles, 4u,',
)


def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    source_paths = {path for _, path in FUNCTIONS}
    originals = {path: (engine / path).read_bytes() for path in source_paths}
    if output in {(engine / path).resolve() for path in source_paths}:
        raise ValueError("Refusing to overwrite authentic KisakCOD source")
    texts = {path: raw.decode("utf-8") for path, raw in originals.items()}
    bodies = [function_source(texts[path], signature) for signature, path in FUNCTIONS]
    rendered = HEADER + GLOBALS + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original IWD directory-scan contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Unsafe legacy IWD directory code remains: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    for path, raw in originals.items():
        if (engine / path).read_bytes() != raw:
            raise RuntimeError("Vendored original changed during staging: " + str(path))
    return {
        "source_sha256": {str(path): hashlib.sha256(raw).hexdigest()
                          for path, raw in originals.items()},
        "function_signatures": [signature for signature, _ in FUNCTIONS],
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for body in bodies],
        "original_directory_scanner_preserved_from_vendored_source": True,
        "original_game_directory_registration_preserved_from_vendored_source": True,
        "game_directory_source_staged_for_android_diagnostic": True,
        "null_or_failed_directory_listing_fails_closed": True,
        "native_pointer_width_qsort": True,
        "android_os_directory_adapter": "rooted z2026_platform_list_iwd_files",
        "localized_language_registry": "English-only adapter; full game language registry pending",
        "fixture_directory_scan_runtime_proven": False,
        "real_game_iwd_mounted": False,
        "fastfile_map_loading_proven": False,
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
    args.report.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("IW3_ORIGINAL_IWD_DIRECTORY_SCAN_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
