#!/usr/bin/env python3
"""Extract the original IW3 Com_LogFileOpen query and its engine-owned state."""
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

SOURCE = Path("src/qcommon/common.cpp")
SIGNATURE = "bool __cdecl Com_LogFileOpen()"
HEADER = '#include "qcommon/qcommon.h"\n'


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD common.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    declarations = list(re.finditer(r"(?m)^[ \t]*int logfile;[ \t]*$", source))
    if len(declarations) != 1:
        raise ValueError(f"Expected exactly one original 'int logfile;' state declaration, found {len(declarations)}")
    state_declaration = declarations[0].group(0).strip()
    body = function_source(source, SIGNATURE)
    if body.count("return logfile != 0;") != 1:
        raise ValueError("Original Com_LogFileOpen behavior changed; refusing to synthesize a substitute")
    rendered = HEADER + "\n" + state_declaration + "\n\n" + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD source changed during extraction")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signature": SIGNATURE,
        "function_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "original_logfile_state_definition_preserved": True,
        "original_Com_LogFileOpen_body_preserved_verbatim": True,
        "logfile_open_query_has_no_synthetic_state": True,
        "startup_runtime_invoked": False,
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
    print("IW3_ORIGINAL_COM_LOGFILE_OPEN_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
