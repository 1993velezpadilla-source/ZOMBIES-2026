#!/usr/bin/env python3
"""Stage ACTUAL KisakCOD Pool_Init/Alloc/Free/FreeCount for Android/host.

Only includes are replaced in the disposable generated copy. The real
freenode pointer-width fix is committed in third_party/KisakCOD original
source, and used identically in this Android compilation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ENGINE_POOL = Path("src/universal/pool_allocator.cpp")
POOL_DECLARATIONS = Path("src/universal/pool_allocator.h")
PROLOGUE = (
    '#include <universal/q_shared.h>\n'
    '#include "pool_allocator.h"\n'
    '#include "assertive.h"\n'
)
REQUIRED = (
    "void __cdecl Pool_Init(",
    "freenode *__cdecl Pool_Alloc(",
    "void __cdecl Pool_Free(",
    "uint32_t __cdecl Pool_FreeCount(",
)
NOT_ALLOWED = (
    "*(uint32_t *)&pool[itemSize * itemIndex]",
    "(uint32_t)&pool[itemSize * (itemIndex + 1)]",
)
PORTABLE = (
    "sizeof(freenode)",
    "alignof(freenode)",
    "reinterpret_cast<std::uintptr_t>(pool)",
    "node->next = itemIndex + 1 < itemCount",
)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    origin = engine / ENGINE_POOL
    header = engine / POOL_DECLARATIONS
    destination = output.resolve()
    if destination == origin:
        raise ValueError("Cannot overwrite original KisakCOD pool allocator")
    if not origin.is_file() or not header.is_file():
        raise ValueError("Original KisakCOD pool source/header missing")
    raw = origin.read_bytes()
    body = raw.decode("utf-8")
    if not body.startswith(PROLOGUE):
        raise ValueError("Unexpected original IW3 pool includes; review dependencies")
    if not all(body.count(fn) == 1 for fn in REQUIRED):
        raise ValueError("Original IW3 pool allocator functions changed")
    if any(unsafe in body for unsafe in NOT_ALLOWED):
        raise ValueError("Win32 32-bit freelist pointer truncation not corrected")
    if not all(marker in body for marker in PORTABLE):
        raise ValueError("Expected native pointer-width fix is not in real engine")
    # Entire KisakCOD function/data body remains unmodified after includes.
    rewritten = (
        '#include "iw3_android_pool_compat.h"\n'
        '#include "pool_allocator.h"\n'
        + body[len(PROLOGUE):]
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rewritten, encoding="utf-8")
    if origin.read_bytes() != raw:
        raise RuntimeError("Unexpected mutation of original source")
    return {
        "origin": str(ENGINE_POOL),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "portable_header_only": True,
        "all_original_function_bodies_present": True,
        "pointer_truncation_removed_from_actual_iw3_engine": True,
        "android_arm64_runtime_executed": False,
        "sp_gameplay_frame_operational": False,
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    evidence = prepare(args.engine, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(evidence, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print("IW3_REAL_POOL_ALLOCATOR_SOURCE_STAGED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
