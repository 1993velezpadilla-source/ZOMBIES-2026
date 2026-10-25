#!/usr/bin/env python3
"""Stage exact corrected KisakCOD SP g_combat.cpp G_HitLocStrcpy on ARM64.

Extract the actual function body. No gameplay or hit-location behavior is
reimplemented; only Windows-specific declarations are replaced for build.
This is NOT a complete IW3 damage system or a playable APK.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SOURCE = Path("src/game/g_combat.cpp")
SIGNATURE = "void __cdecl G_HitLocStrcpy(unsigned __int8 *pMember, const char *pszKeyValue)"
END = "\n}\n\nvoid __cdecl G_ParseHitLocDmgTable()"
REQUIRED = (
    "*pMember++ = value;",
    "value = static_cast<unsigned char>(*pszKeyValue++);",
    "} while (value);",
)
UNSAFE = (
    "v2 = pMember - (unsigned __int8 *)pszKeyValue;",
    "((char*)pszKeyValue++)[v2] = v3;",
)

def prepare(engine: Path, output: Path) -> dict:
    origin = (engine.resolve() / SOURCE)
    out = output.resolve()
    if out == origin:
        raise ValueError("Never overwrite authentic KisakCOD g_combat.cpp")
    if not origin.is_file():
        raise ValueError("Missing authentic IW3 single-player g_combat.cpp")
    raw = origin.read_bytes()
    text = raw.decode("utf-8")
    if text.count(SIGNATURE) != 1:
        raise ValueError("Original SP hit-location function signature changed")
    start = text.index(SIGNATURE)
    if text.count(END, start) < 1:
        raise ValueError("Original SP hit-location function boundary changed")
    stop = text.index(END, start) + 2
    func = text[start:stop]
    if not all(token in func for token in REQUIRED):
        raise ValueError("Native-width IW3 hit-location byte copy is missing")
    if any(token in func for token in UNSAFE):
        raise ValueError("32-bit pointer-difference truncation remains")
    rendered = (
        '#include "iw3_android_hitloc_compat.h"\n'
        + func + "\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    if origin.read_bytes() != raw:
        raise RuntimeError("Vendored KisakCOD SP source unexpectedly changed")
    return {
        "origin": str(SOURCE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "extracted_function_sha256": hashlib.sha256(func.encode("utf-8")).hexdigest(),
        "function_body_preserved": True,
        "win32_pointer_delta_removed_from_real_engine": True,
        "full_hitloc_damage_system_ported": False,
        "playable_apk": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.engine, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("IW3_REAL_SP_HITLOC_COPY_SOURCE_STAGED", json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()
