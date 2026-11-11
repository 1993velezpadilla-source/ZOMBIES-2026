#!/usr/bin/env python3
"""Stage authentic directory-scan helpers without duplicating FS startup bodies.

The startup archive already owns FS_AddIwdFilesForGameDirectory and
FS_AddGameDirectory. This source slice contains only their original helper
functions, while the Android adapter supplies rooted Sys_ListFiles/free-list
and narrow logging/language boundaries for the link audit.
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
    ("int __cdecl FS_PathCmp(const char *s1, const char *s2)", FILES),
    ("int __cdecl iwdsort(const char **a, char **b)", FILES),
)
FORBIDDEN = (
    "void __cdecl FS_AddIwdFilesForGameDirectory(",
    "void __cdecl FS_AddGameDirectory(",
    "qsort(s0, numfiles, 4u,",
)
HEADER = (
    '#include "iw3_android_iwd_directory_compat.h"\n'
    '#include <cctype>\n'
    '#include <cstdint>\n'
    '#include <cstring>\n'
)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    source_paths = {path for _, path in FUNCTIONS}
    source_bytes = {path: (engine / path).read_bytes() for path in source_paths}
    if output in {(engine / path).resolve() for path in source_paths}:
        raise ValueError("Refusing to overwrite authentic KisakCOD source")
    source_text = {path: raw.decode("utf-8") for path, raw in source_bytes.items()}
    bodies = [function_source(source_text[path], signature) for signature, path in FUNCTIONS]
    rendered = HEADER + "\n\n".join(bodies) + "\n"
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Directory helper slice contains duplicated/unsafe body: " + marker)
    # Verify the original scanner uses native pointer width and keeps its
    # paired list-free operation before compiling the separated helper slice.
    startup = (engine / FILES).read_text(encoding="utf-8")
    if "qsort(s0, numfiles, sizeof(s0[0])," not in startup:
        raise ValueError("Original IWD scanner lost native pointer-width qsort")
    if "FS_FreeFileList((const char **)list);" not in startup:
        raise ValueError("Original IWD scanner lost its original list-free call")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    for path, raw in source_bytes.items():
        if (engine / path).read_bytes() != raw:
            raise RuntimeError("Vendored original changed during staging: " + str(path))
    return {
        "source_sha256": {str(path): hashlib.sha256(raw).hexdigest()
                          for path, raw in source_bytes.items()},
        "function_signatures": [signature for signature, _ in FUNCTIONS],
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for body in bodies],
        "helper_bodies_preserved_verbatim": True,
        "original_startup_owns_iwd_enumerator": True,
        "android_rooted_sys_list_files_adapter_included_by_build_target": True,
        "native_pointer_width_qsort_verified_in_original_scanner": True,
        "runtime_execution_proven": False,
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
    args.report.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("IW3_ORIGINAL_IWD_DIRECTORY_HELPERS_STAGED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
