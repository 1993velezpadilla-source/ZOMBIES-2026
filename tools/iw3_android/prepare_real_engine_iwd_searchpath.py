#!/usr/bin/env python3
"""Stage authentic KisakCOD FS_AddSearchPath for the Android diagnostic target."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/com_files.cpp")
SIGNATURE = "void __cdecl FS_AddSearchPath(searchpath_s *search)"
HEADER = '#include "iw3_android_iwd_mount_compat.h"\n'
GLOBAL = "searchpath_s *fs_searchpaths = nullptr;"
REQUIRED = (
    "pSearch = &fs_searchpaths;",
    "if (search->bLocalized)",
    "while (*pSearch && !(*pSearch)->bLocalized)",
    "pSearch = &(*pSearch)->next;",
    "search->next = *pSearch;",
    "*pSearch = search;",
)
FORBIDDEN = ("pSearch = (searchpath_s **)*pSearch;",)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")
    original = source_path.read_bytes()
    body = function_source(original.decode("utf-8"), SIGNATURE)
    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original FS_AddSearchPath contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Unsafe pointer traversal remains: " + marker)
    rendered = HEADER + GLOBAL + "\n\n" + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored source changed during staging")
    return {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "function_body_preserved_verbatim_from_vendored_source": True,
        "pointer_traversal_uses_next_member_address": True,
        "original_localized_insertion_order_preserved": True,
        "source_staged_for_android_diagnostic_runtime": True,
        "searchpath_runtime_execution_proven": False,
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
    print("IW3_ORIGINAL_IWD_SEARCHPATH_STAGED", json.dumps(evidence, sort_keys=True))

if __name__ == "__main__":
    main()
