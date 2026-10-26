#!/usr/bin/env python3
"""Extract original IW3 filtered-file search bodies for native ABI compilation.

Both FS_ListFilteredFiles and FS_ListFilteredFilesInLocation are preserved
verbatim from vendored KisakCOD. The static audit archive keeps real Hunk and
filesystem services unresolved and is not linked into the JNI diagnostic.
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
SIGNATURE = "const char **__cdecl FS_ListFilteredFilesInLocation("
LIST_SIGNATURE = (
    "const char **__cdecl FS_ListFilteredFiles(\n"
    "    searchpath_s *searchPath,\n"
    "    const char *path,\n"
    "    const char *extension,\n"
    "    const char *filter,\n"
    "    FsListBehavior_e behavior,\n"
    "    int *numfiles)"
)
HEADER = '#include "iw3_android_filtered_files_compat.h"\n'
ALLOCATION = (
    "Hunk_UserAlloc(user, sizeof(searchpath_s), "
    "static_cast<int>(alignof(searchpath_s)))"
)
LIST_ALLOCATION = (
    "Hunk_UserAlloc(user, (0x1FFFu + 2u) * sizeof(*list), "
    "static_cast<int>(alignof(const char *)))"
)
REQUIRED = (
    'user = Hunk_UserCreate(0x20000, "FS_ListFilteredFilesInLocation", 0, 0, 3);',
    "if (FS_CheckLocation(pathDir, lookInFlags))",
    ALLOCATION,
    "result = FS_ListFilteredFiles(locationSearchPath, path, extension, filter, behavior, numfiles);",
    "Hunk_UserDestroy(user);",
)
LIST_REQUIRED = (
    LIST_ALLOCATION,
    "if (nfiles == 0x1FFF)",
    "*list++ = (const char *)user;",
    "list[nfiles] = 0;",
)
FORBIDDEN = (
    "Hunk_UserAlloc(user, 0x1Cu, 4)",
    "Hunk_UserAlloc(user, 0x1C, 4)",
    "Hunk_UserAlloc(user, 0x8004u, 4)",
    "Hunk_UserAlloc(user, 0x8004, 4)",
)


def definition_source(source: str, signature: str) -> str:
    """Extract exactly one function definition, ignoring a matching prototype."""
    positions = []
    cursor = 0
    while True:
        position = source.find(signature, cursor)
        if position < 0:
            break
        positions.append(position)
        cursor = position + len(signature)
    definitions = []
    prototypes = []
    for position in positions:
        after = position + len(signature)
        while after < len(source) and source[after].isspace():
            after += 1
        if after < len(source) and source[after] == "{":
            definitions.append(position)
        elif after < len(source) and source[after] == ";":
            prototypes.append(position)
    if len(definitions) != 1:
        raise ValueError("Expected one original definition for " + signature)
    filtered = source
    for position in reversed(prototypes):
        filtered = filtered[:position] + filtered[position + len(signature):]
    return function_source(filtered, signature)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD com_files.cpp")

    original = source_path.read_bytes()
    source_text = original.decode("utf-8")
    location_body = function_source(source_text, SIGNATURE)
    list_body = definition_source(source_text, LIST_SIGNATURE)
    for marker in REQUIRED:
        if marker not in location_body:
            raise ValueError("Original location-filter contract missing: " + marker)
    for marker in LIST_REQUIRED:
        if marker not in list_body:
            raise ValueError("Original filtered-file list contract missing: " + marker)
    combined_body = list_body + "\n\n" + location_body
    for marker in FORBIDDEN:
        if marker in combined_body:
            raise ValueError("Win32-sized allocation remains in original bodies: " + marker)
    if location_body.count(ALLOCATION) != 2:
        raise ValueError("Expected both native-width searchpath allocations")
    if list_body.count(LIST_ALLOCATION) != 1:
        raise ValueError("Expected one native-width filtered-file pointer-array allocation")

    rendered = HEADER + combined_body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored original changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "original_function_sha256": hashlib.sha256(location_body.encode("utf-8")).hexdigest(),
        "original_list_function_sha256": hashlib.sha256(list_body.encode("utf-8")).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_function_body_preserved_verbatim": True,
        "original_list_function_body_preserved_verbatim": True,
        "native_size_and_alignment_allocations": 2,
        "native_pointer_array_allocations": 1,
        "native_pointer_array_slots": 8193,
        "native_pointer_array_allocation_expression": LIST_ALLOCATION,
        "win32_fixed_size_allocations": 0,
        "source_staged_for_host_and_arm64_compile": True,
        "runtime_execution_proven": False,
        "full_filesystem_runtime_linked": False,
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
    print("IW3_ORIGINAL_FILTERED_FILE_LIST_AND_LOCATION_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
