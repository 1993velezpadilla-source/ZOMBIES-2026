#!/usr/bin/env python3
"""Stage corrected original KisakCOD Hunk temporary allocator bodies for ARM64."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_memory.cpp")
STATE = Path("src/universal/com_memory_state.cpp")
STATE_HEADER = Path("src/universal/com_memory_state.h")
FUNCTIONS = (
    "void __cdecl Hunk_ClearToMarkLow(int32_t mark)",
    "uint8_t* __cdecl Hunk_AllocAlign(uint32_t size, int32_t alignment, const char* name, int32_t type)",
    "uint8_t* __cdecl Hunk_AllocateTempMemoryHigh(int32_t size, const char* name)",
    "void Hunk_ClearTempMemoryHigh()",
    "uint8_t* __cdecl Hunk_AllocLowAlign(uint32_t size, int32_t alignment, const char* name, int32_t type)",
    "void Hunk_ClearTempMemory()",
    "uint32_t* __cdecl Hunk_AllocateTempMemory(int32_t size, const char* name)",
    "void __cdecl Hunk_FreeTempMemory(char* buf)",
)
HEADER = (
    '#include <universal/com_memory_state.h>\n'
    '#include <qcommon/qcommon.h>\n'
    '#include <qcommon/mem_track.h>\n'
    '#include <assertive.h>\n'
    '#include <cstdint>\n'
    // Declarations only: these remain genuine engine service edges in the audit
    // object; this staging file must not invent implementations for them.
    'extern bool __cdecl Sys_IsMainThread();\n'
    'extern void Hunk_CheckTempMemoryClear();\n'
    'extern void Hunk_CheckTempMemoryHighClear();\n'
    'extern void Hunk_ClearData();\n'
    'extern void *Z_Malloc(int size, const char *name, int type);\n'
    'extern void Z_Free(void *ptr, int type);\n'
    'extern void Z_VirtualCommit(void *ptr, int size);\n'
    'extern void Z_VirtualDecommit(void *ptr, int size);\n'
)
FORBIDDEN = (
    "(uint32_t)&s_hunkData", "(uint32_t)beginBuf", "(uint8_t)bufa",
    "(uint32_t)buf", "(uint32_t)pos", "0xFFFFF000", "(_BYTE)s_hunkData",
    "(int)pos", "user[114].name", "0xFE0u",
)

def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path, state_path, header_path = engine / SOURCE, engine / STATE, engine / STATE_HEADER
    output = output.resolve()
    if output in {source_path.resolve(), state_path.resolve(), header_path.resolve()}:
        raise ValueError("Refusing to overwrite authentic KisakCOD Hunk source/state")
    source_bytes, state_bytes, header_bytes = source_path.read_bytes(), state_path.read_bytes(), header_path.read_bytes()
    source, state, state_header = source_bytes.decode("utf-8"), state_bytes.decode("utf-8"), header_bytes.decode("utf-8")
    for marker in ("hunkUsed_t hunk_high{};", "hunkUsed_t hunk_low{};",
                   "unsigned char *s_hunkData = nullptr;", "int32_t s_hunkTotal = 0;"):
        if marker not in state:
            raise ValueError("Shared Hunk state missing: " + marker)
    for marker in ("static_assert(sizeof(hunkHeader_t) == 16", "Hunk_PageBase(const void *address)"):
        if marker not in state_header:
            raise ValueError("LP64 Hunk ABI guard missing: " + marker)
    if "static hunkUsed_t hunk_high;" in source or "static hunkUsed_t hunk_low;" in source:
        raise ValueError("com_memory.cpp still owns private Hunk counters")
    if "unsigned char* s_hunkData;" in source or "int32_t s_hunkTotal;" in source:
        raise ValueError("com_memory.cpp still owns private Hunk base state")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    rendered = HEADER + "\n\n".join(bodies) + "\n"
    for marker in FORBIDDEN:
        if marker in rendered:
            raise ValueError("32-bit pointer arithmetic remains in Hunk temp allocator: " + marker)
    for marker in ("Hunk_PageBase(&s_hunkData[hunk_low.temp + 4095])",
                   "reinterpret_cast<uintptr_t>(bufa)", "Hunk_FreeTempMemory: bad magic",
                   "Z_Malloc(size, name, 10)", "Z_Free(buf, 10)"):
        if marker not in rendered:
            raise ValueError("Original Hunk allocator contract missing: " + marker)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != source_bytes or state_path.read_bytes() != state_bytes or header_path.read_bytes() != header_bytes:
        raise RuntimeError("Vendored Hunk source/state changed during staging")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "shared_state_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "shared_state_header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_sha256": {signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
                            for signature, body in zip(FUNCTIONS, bodies)},
        "original_hunk_temp_allocator_bodies_extracted_from_vendored_engine": True,
        "original_core_hunk_allocator_bodies_extracted_from_vendored_engine": True,
        "pointer_page_alignment_uses_uintptr_t": True,
        "high_temp_allocator_returns_native_pointer": True,
        "core_allocator_page_math_uses_native_pointer_width": True,
        "temporary_header_fixed_at_16_bytes_on_32_and_64_bit": True,
        "single_engine_owned_hunk_state": True,
        "hunk_allocator_archive_compiled_for_aarch64_audit": True,
        "runtime_hunk_allocator_invoked": False,
        "fs_startup_runtime_invoked": False,
        "real_game_data_mounted": False,
        "map_loading_proven": False,
        "renderer_or_gameplay_proven": False,
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
    print("IW3_ORIGINAL_HUNK_TEMP_ALLOCATOR_STAGED", json.dumps(evidence, sort_keys=True))
if __name__ == "__main__":
    main()
