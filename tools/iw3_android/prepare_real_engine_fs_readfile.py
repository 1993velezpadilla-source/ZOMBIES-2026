#!/usr/bin/env python3
"""Stage original KisakCOD FS_ReadFile and its memory/read wrappers for ARM64 audit.

Bodies are extracted verbatim from com_files.cpp. Hunk allocation remains a
real unresolved engine dependency; this generator never substitutes an allocator
or invokes FS_Startup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_files.cpp")
STATE = Path("src/universal/com_files_state.cpp")
FUNCTIONS = (
    ("void __cdecl FS_CheckFileSystemStarted()", SOURCE),
    ("uint32_t __cdecl FS_FOpenFileRead(const char *filename, int *file)", SOURCE),
    ("int __cdecl FS_ReadFile(const char *qpath, void **buffer)", SOURCE),
    ("uint32_t *__cdecl FS_AllocMem(int bytes)", SOURCE),
    ("void __cdecl FS_FreeFile(char *buffer)", SOURCE),
    ("void __cdecl FS_FreeMem(char *buffer)", SOURCE),
    ("void __cdecl FS_ResetFiles()", SOURCE),
    ("int __cdecl FS_LoadStack()", SOURCE),
)
REQUIRED = (
    "FS_CheckFileSystemStarted();",
    "len = FS_FOpenFileRead(qpath, &h);",
    "buf = (uint8_t *)FS_AllocMem(len + 1);",
    "FS_Read(buf, len, h);",
    "buf[len] = 0;",
    "com_fileAccessed = 1;",
    "Hunk_AllocateTempMemory(bytes, \"FS_AllocMem\")",
    "Hunk_FreeTempMemory(buffer);",
    "--fs_loadStack;",
    "fs_loadStack = 0;",
)
HEADER = (
    '#include "iw3_android_fs_read_compat.h"\n'
    '#include "iw3_android_iwd_directory_compat.h"\n'
    '#include <universal/com_memory.h>\n'
    '#include <cstdint>\n'
    '#include <cstdlib>\n'
)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    source_path = engine / SOURCE
    state_path = engine / STATE
    original = source_path.read_bytes()
    state_bytes = state_path.read_bytes()
    source = original.decode("utf-8")
    state = state_bytes.decode("utf-8")
    if output == source_path or output == state_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD engine source")
    for marker in ("int com_fileAccessed = 0;", "int fs_loadStack = 0;"):
        if marker not in state:
            raise ValueError("Shared filesystem state is missing: " + marker)
    for symbol in ("com_fileAccessed", "fs_loadStack"):
        if re.search(r"(?m)^\\s*int\\s+" + symbol + r"\\s*;\\s*$", source):
            raise ValueError("Original global still has a private definition in com_files.cpp: " + symbol)
    bodies = [function_source(source, signature) for signature, _ in FUNCTIONS]
    rendered = HEADER + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original FS_ReadFile contract missing: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original or state_path.read_bytes() != state_bytes:
        raise RuntimeError("Vendored engine source changed during staging")
    return {
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "shared_state_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "function_signatures": [signature for signature, _ in FUNCTIONS],
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for body in bodies],
        "original_fs_readfile_bodies_preserved_verbatim": True,
        "com_file_accessed_and_load_stack_have_single_shared_state": True,
        "original_hunk_allocator_calls_preserved": True,
        "hunk_allocate_temp_memory_remains_engine_dependency": True,
        "hunk_free_temp_memory_remains_engine_dependency": True,
        "startup_runtime_invoked": False,
        "real_game_data_mounted": False,
        "map_loading_proven": False,
        "renderer_or_gameplay_proven": False,
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
    print("IW3_ORIGINAL_FS_READFILE_STAGED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
