#!/usr/bin/env python3
"""Stage verbatim KisakCOD IWD filename and language helpers for Android.

Extract actual FS_HashFileName, FS_FilenameCompare, FS_ConvertPath and
IwdFileLanguage from src/universal/com_files.cpp, plus the real I_islower
dependency from src/universal/q_shared.cpp. This is not an archive reader or
playable game.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
if __package__:
    from .prepare_g_runframe_prereqs import function_source
else:
    from prepare_g_runframe_prereqs import function_source

FILES = Path("src/universal/com_files.cpp")
SHARED = Path("src/universal/q_shared.cpp")
FUNCTIONS = (
    ("bool I_islower(int c)", SHARED),
    ("int __cdecl FS_HashFileName(const char *fname, int hashSize)", FILES),
    ("int __cdecl FS_FilenameCompare(const char *s1, const char *s2)", FILES),
    ("void __cdecl FS_ConvertPath(char *s)", FILES),
    ("char *__cdecl IwdFileLanguage(const char *pszIwdFileName)", FILES),
)
HEADER = '#include "iw3_android_iwd_names_compat.h"\n'
GLOBALS = "char szIwdLanguageName[2][64];\nint iString = 0;\n"
REQUIRED = (
    "letter = tolower(static_cast<unsigned char>(fname[i]));",
    "return ((hash >> 20) ^ hash ^ (hash >> 10)) & (hashSize - 1);",
    "if (I_islower(c1))",
    "if (c1 == '\\\\' || c1 == ':')",
    "if (*s == 92 || *s == 58)",
    "isalpha(static_cast<unsigned char>(pszIwdFileName[iCurrChar]))",
    "char szIwdLanguageName[2][64];",
    "int iString = 0;",
)
FORBIDDEN = (
    "letter = tolower(fname[i]);",
    "isalpha(pszIwdFileName[iCurrChar])",
)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    originals = {path: engine / path for _, path in FUNCTIONS}
    if output in originals.values():
        raise ValueError("Never overwrite authentic KisakCOD source")
    raw = {path: origin.read_bytes() for path, origin in originals.items()}
    original_file_text = raw[FILES].decode("utf-8")
    for declaration in ("char szIwdLanguageName[2][64];", "int iString = 0;"):
        if declaration not in original_file_text:
            raise ValueError("Original IWD language sort state missing: " + declaration)
    bodies = []
    for signature, path in FUNCTIONS:
        body = function_source(raw[path].decode("utf-8"), signature)
        bodies.append(body)
    rendered = HEADER + GLOBALS + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original IW3 IWD filename algorithm changed: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Unsafe signed-char ctype call in original IWD filename hash: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    for path, origin in originals.items():
        if origin.read_bytes() != raw[path]:
            raise RuntimeError("Vendored original changed during staging")
    return {
        "source_sha256": {str(p): hashlib.sha256(b).hexdigest() for p, b in raw.items()},
        "verbatim_functions": [name for name, _ in FUNCTIONS],
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest() for body in bodies],
        "source_bodies_preserved": True,
        "iwd_filename_hash_and_compare_ported": True,
        "iwd_filename_hash_high_bit_safe": True,
        "iwd_language_sort_key_high_bit_safe": True,
        "iwd_language_sort_state_staged_from_original": True,
        "iwd_zip_archive_mount_ported": False,
        "fastfile_map_loading_ported": False,
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
    args.report.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("IW3_ORIGINAL_IWD_FILENAME_LOOKUP_STAGED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
