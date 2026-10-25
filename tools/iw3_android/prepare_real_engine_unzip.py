#!/usr/bin/env python3
"""Stage the authentic KisakCOD ZIP32/IWD parser with an Android-safe include shim.

Only the two Windows-heavy include lines are replaced in the disposable copy.
The parser implementation remains the original engine source; ZIP32 numeric
fields and public buffer/offset parameters are fixed-width in the vendored
header/source so LP64 Android does not silently widen Windows DWORDs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

SOURCE = Path("src/qcommon/unzip.cpp")
HEADER = Path("src/qcommon/unzip.h")
PROLOGUE = (
    "#include <universal/q_shared.h>\n"
    "#include <universal/com_memory.h>\n"
)
REQUIRED_SOURCE = (
    "extern unzFile unzOpen (const char* path)",
    "extern int unzGetGlobalInfo",
    "extern int unzGoToFirstFile",
    "extern int unzGoToNextFile",
    "extern int unzOpenCurrentFile",
    "extern int unzReadCurrentFile",
    "extern int unzCloseCurrentFile",
)
REQUIRED_FIXED_FIELDS = (
    "uint32_t number_entry;",
    "uint32_t size_comment;",
    "uint32_t compressed_size;",
    "uint32_t uncompressed_size;",
    "uint32_t offset_curfile;",
    "uint32_t pos_in_zipfile;",
    "uint32_t central_pos;",
    "uint32_t offset_central_dir;",
)

def prepare(engine: Path, output: Path) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    header_path = engine / HEADER
    out = output.resolve()
    if out == source_path:
        raise ValueError("Cannot overwrite the original IW3 unzip.cpp")
    if not source_path.is_file() or not header_path.is_file():
        raise ValueError("Original KisakCOD ZIP/IWD parser source/header missing")
    source_bytes = source_path.read_bytes()
    header_bytes = header_path.read_bytes()
    source = source_bytes.decode("utf-8")
    header = header_bytes.decode("utf-8")
    if not source.startswith(PROLOGUE):
        raise ValueError("Unexpected original unzip.cpp include prologue")
    if not all(source.count(marker) == 1 for marker in REQUIRED_SOURCE):
        raise ValueError("Authentic original ZIP/IWD parser entry points changed")
    if not all(marker in header for marker in REQUIRED_FIXED_FIELDS):
        raise ValueError("ZIP32 field widths are not fixed in original IW3 header")
    # All active format fields must not depend on LP64's 64-bit unsigned long.
    for line in header.splitlines():
        if line.lstrip().startswith("//"):
            continue
        if re.search(r"\\bunsigned long\\s+\\w+\\s*;", line):
            raise ValueError("LP64-width unsigned long remains in active ZIP32 header: " + line.strip())
    if "uint32_t fileNameBufferSize" not in source or "uint32_t *pos" not in source:
        raise ValueError("Original ZIP32 public entry-point widths are not portable")
    staged = '#include "iw3_android_unzip_compat.h"\n' + source[len(PROLOGUE):]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(staged, encoding="utf-8")
    if source_path.read_bytes() != source_bytes or header_path.read_bytes() != header_bytes:
        raise RuntimeError("Unexpected mutation of original source while staging")
    return {
        "original_parser": str(SOURCE),
        "original_header": str(HEADER),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "parser_body_preserved_after_include_adapter": staged.split("\\n", 1)[1] == source[len(PROLOGUE):],
        "zip32_numeric_fields_fixed_width": True,
        "android_arm64_parser_execution": False,
        "archive_searchpath_integration": False,
        "map_loading_verified": False,
        "gameplay_verified": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.engine, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
    print("IW3_ORIGINAL_ZIP32_SOURCE_STAGED", json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()
