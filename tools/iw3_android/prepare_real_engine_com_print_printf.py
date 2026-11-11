#!/usr/bin/env python3
"""Stage the original KisakCOD Com_Printf body with a bounded Android formatter.

Only the original formatter body is staged; the full common.cpp translation
unit is not linked because it pulls in client, renderer, script and platform
services. The existing Com_PrintMessage sink is Android logcat / host stderr.
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

SOURCE = Path("src/qcommon/common.cpp")
SIGNATURE = "void QDECL Com_Printf(int channel, const char* fmt, ...)"
REQUIRED_SOURCE = (
    "_vsnprintf(string, 0x1000u, fmt, va);",
    "string[4095] = 0;",
    "Com_PrintMessage(channel, string, 0);",
)
FORBIDDEN = (
    "_vsnprintf(",
    "Godot",
    "fake Com_Printf",
    "diagnostic Com_Printf stub",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD common.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    body = function_source(source, SIGNATURE)
    for marker in REQUIRED_SOURCE:
        if marker not in body:
            raise ValueError("Original Com_Printf contract missing: " + marker)

    adapted = body.replace(
        "_vsnprintf(string, 0x1000u, fmt, va);",
        "std::vsnprintf(string, 0x1000u, fmt, va);\n\tva_end(va);",
    )
    if adapted == body:
        raise ValueError("No Android portability adaptation was applied")
    for marker in FORBIDDEN:
        if marker in adapted:
            raise ValueError("Forbidden original/platform pattern remains: " + marker)
    if "Com_PrintMessage(channel, string, 0);" not in adapted:
        raise ValueError("Original normal-message output contract was lost")

    rendered = (
        '#include "iw3_android_fs_startup_compat.h"\n'
        "#include <cstdarg>\n"
        "#include <cstddef>\n"
        "#include <cstdio>\n\n"
        + adapted
        + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD common.cpp changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signature": SIGNATURE,
        "original_function_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "original_com_printf_body_staged": True,
        "android_vsnprintf_adaptation_only": True,
        "normal_message_type_0_and_channel_preserved": True,
        "com_print_message_platform_sink": "existing Android logcat / host stderr",
        "full_common_translation_unit_linked": False,
        "filesystem_startup_invoked": False,
        "fastfile_or_map_loaded": False,
        "renderer_or_gameplay_proven": False,
        "playable_apk": False,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_COM_PRINTF_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
