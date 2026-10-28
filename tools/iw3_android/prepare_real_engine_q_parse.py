#!/usr/bin/env python3
"""Extract authentic KisakCOD parser/session bodies for the Android ARM64 audit.

This stages the original parser implementation with a narrow include surface.
It does not provide command, thread, error, filesystem, renderer, or gameplay
stubs. Those dependencies remain visible in the archive/link report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ImportError:  # direct script execution from tools/iw3_android
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/universal/q_parse.cpp")
FUNCTIONS = (
    "void __cdecl Com_InitParse()",
    "void __cdecl Com_InitParseInfo(parseInfo_t *pi)",
    "void __cdecl Com_BeginParseSession(const char *filename)",
    "ParseThreadInfo *__cdecl Com_GetParseThreadInfo()",
    "void __cdecl Com_EndParseSession()",
    "void __cdecl Com_SetCSV(int csv)",
    "int __cdecl Com_GetCurrentParseLine()",
    "void __cdecl Com_UngetToken()",
    "void __cdecl Com_ParseSetMark(const char **text, com_parse_mark_t *mark)",
    "void __cdecl Com_ParseReturnToMark(const char **text, com_parse_mark_t *mark)",
    "const char *__cdecl Com_GetLastTokenPos()",
    "parseInfo_t *__cdecl Com_Parse(const char **data_p)",
    "parseInfo_t *__cdecl Com_ParseExt(const char **data_p, int allowLineBreaks)",
    "const char *__cdecl SkipWhitespace(const char *data, int *hasNewLines)",
    "parseInfo_t *__cdecl Com_ParseCSV(const char **data_p, int allowLineBreaks)",
    "parseInfo_t *__cdecl Com_ParseOnLine(const char **data_p)",
)
PUNCTUATION_MARKER = "const char *punctuation[15]"


def punctuation_source(source: str) -> str:
    if source.count(PUNCTUATION_MARKER) != 1:
        raise ValueError("Expected exactly one original IW3 punctuation table")
    start = source.index(PUNCTUATION_MARKER)
    opening = source.find("{", start)
    if opening < 0:
        raise ValueError("Original IW3 punctuation table initializer missing")
    closing = source.find("};", opening)
    if closing < 0:
        raise ValueError("Original IW3 punctuation table terminator missing")
    return source[start:closing + 2]


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    source_path = engine / SOURCE
    original_bytes = source_path.read_bytes()
    source = original_bytes.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    punctuation = punctuation_source(source)
    global_match = re.search(r"(?m)^ParseThreadInfo g_parse\[4\];[^\n]*$", source)
    if not global_match:
        raise ValueError("Original q_parse.cpp thread-state definition not found")
    parse_global = global_match.group(0)
    generated = (
        "// Generated from the vendored original KisakCOD q_parse.cpp. Do not edit.\n"
        "#include <universal/q_shared.h>\n"
        "#include <universal/q_parse.h>\n"
        "#include <universal/assertive.h>\n"
        "#include <qcommon/qcommon.h>\n"
        "#include <qcommon/threads.h>\n"
        "#include <cstring>\n"
        "#include <string.h>\n\n"
        + parse_global + "\n\n"
        + punctuation + "\n\n"
        + "\n\n".join(bodies) + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original_bytes:
        raise RuntimeError("Vendored KisakCOD q_parse.cpp changed during extraction")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "parse_global_sha256": hashlib.sha256(parse_global.encode("utf-8")).hexdigest(),
        "punctuation_table_sha256": hashlib.sha256(punctuation.encode("utf-8")).hexdigest(),
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_parser_bodies_preserved": True,
        "original_parse_thread_state_preserved": True,
        "original_punctuation_table_preserved": True,
        "command_thread_error_services_are_stubs": False,
        "parser_runtime_linked": False,
        "filesystem_startup_invoked": False,
        "real_game_data_mounted": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_Q_PARSE_STAGED_FOR_ARM64_AUDIT", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
