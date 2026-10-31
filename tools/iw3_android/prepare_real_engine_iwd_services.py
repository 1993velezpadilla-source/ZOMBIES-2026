#!/usr/bin/env python3
"""Stage the exact KisakCOD services needed to execute original FS_LoadZipFile.

The function bodies are extracted from their original engine translation units.
Only the include preamble and assertion adapter are supplied for the isolated
Android ABI module; this is not a replacement archive index or game simulation.
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
STATE_SOURCE = Path("src/universal/com_files_state.cpp")
SHARED_STATE_GLOBALS = ("int fs_iwdFileCount = 0;", "int fs_checksumFeed = 0;")
FUNCTIONS = (
    ("bool I_isupper(int c)", Path("src/universal/q_shared.cpp")),
    ("void I_strncpyz(char* dest, const char* src, int destsize)", Path("src/universal/q_shared.cpp")),
    ("int I_strnicmp(const char* s0, const char* s1, int n)", Path("src/universal/q_shared.cpp")),
    ("int I_stricmp(const char* s0, const char* s1)", Path("src/universal/q_shared.cpp")),
    ("char *__cdecl I_strlwr(char *s)", Path("src/universal/q_shared.cpp")),
    ("void _copyDWord(uint32_t* dest, const uint32_t constant, const uint32_t count)", Path("src/qcommon/common.cpp")),
    ("void __cdecl Com_Memset(void *dest_p, const int val, const size_t count)", Path("src/universal/com_shared.cpp")),
    ("static char* __cdecl Z_TryMallocGarbage(int32_t size, const char* name, int32_t type)", Path("src/universal/com_memory.cpp")),
    ("static uint32_t* __cdecl Z_TryMalloc(int32_t size, const char* name, int32_t type)", Path("src/universal/com_memory.cpp")),
    ("void* Z_Malloc(int32_t size, const char* name, int32_t type)", Path("src/universal/com_memory.cpp")),
    ("void __cdecl Z_Free(void *ptr, int32_t type)", Path("src/universal/com_memory.cpp")),
    ("int __cdecl Com_BlockChecksumKey32(const uint8_t *data, uint32_t length, uint32_t initialCrc)", Path("src/qcommon/com_bsp_load_obj.cpp")),
)
HEADER = (
    '#include <universal/q_shared.h>\n'
    '#include <qcommon/qcommon.h>\n'
    '#include "iw3_android_iwd_mount_compat.h"\n'
    '#include <cassert>\n'
    '#include <cstdlib>\n'
    '#include <cstring>\n'
    '#include <cstdint>\n'
    '#undef iassert\n'
    '#define iassert(expr) assert(expr)\n'
)
GLOBALS = ()
REQUIRED = (
    "return 2 * (c0 >= c1) - 1;",
    "buf = (char*)malloc(size);",
    "Com_Memset(buf, 0, size);",
    "void* Z_Malloc(int32_t size, const char* name, int32_t type)",
    "free(ptr);",
    "crc = ~initialCrc;",
    "return ~crc;",
    "void __cdecl Com_Memset(void *dest_p, const int val, const size_t count)",
    "_copyDWord(dest, val |",
)
FORBIDDEN = ("MyAssertHandler", "Com_BlockChecksumKey32(const unsigned char *data, int length, int key)")


def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    output = output.resolve()
    source_paths = {path for _, path in FUNCTIONS} | {FILES}
    source_bytes = {path: (engine / path).read_bytes() for path in source_paths}
    if output in {(engine / path).resolve() for path in source_paths}:
        raise ValueError("Never overwrite authentic KisakCOD source")

    source_text = {path: raw.decode("utf-8") for path, raw in source_bytes.items()}
    state_bytes = (engine / STATE_SOURCE).read_bytes()
    state_text = state_bytes.decode("utf-8")
    for marker in SHARED_STATE_GLOBALS:
        if marker not in state_text:
            raise ValueError("Shared engine IWD state definition missing: " + marker)
    for marker in ("int fs_iwdFileCount;", "int fs_checksumFeed;"):
        if marker in source_text[FILES]:
            raise ValueError("com_files.cpp still owns a private IWD state definition: " + marker)

    bodies = [
        function_source(source_text[path], signature)
        for signature, path in FUNCTIONS
    ]
    rendered = HEADER + "\n\n".join(bodies) + "\n"
    for marker in REQUIRED:
        if marker not in rendered:
            raise ValueError("Original IWD service body changed: " + marker)
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("Unexpected assertion/checksum substitute in staged source: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    for path, raw in source_bytes.items():
        if (engine / path).read_bytes() != raw:
            raise RuntimeError("Vendored original changed during staging: " + str(path))

    return {
        "source_sha256": {str(path): hashlib.sha256(raw).hexdigest()
                          for path, raw in source_bytes.items()},
        "engine_shared_fs_state_source_present": True,
        "engine_shared_fs_state_source_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "function_signatures": [signature for signature, _ in FUNCTIONS],
        "function_sha256": [hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for body in bodies],
        "function_bodies_preserved_verbatim": True,
        "original_allocator_and_free_staged": True,
        "original_checksum_algorithm_staged": True,
        "original_string_helpers_staged": True,
        "iwd_state_globals_from_shared_engine_source": True,
        "assertion_adapter": "standard assert for isolated original string helpers",
        "source_staged_for_android_diagnostic_link": True,
        "runtime_execution_proven": False,
        "real_iwd_index_runtime_proven": False,
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
    print("IW3_ORIGINAL_IWD_RUNTIME_SERVICES_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
