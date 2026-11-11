#!/usr/bin/env python3
"""Stage KisakCOD's original Com_PrintWarning with a narrow Android printf adaptation.

Only this function is extracted from src/qcommon/common.cpp. The full common.cpp
translation unit is not linked because it depends on the original client,
renderer, script and platform subsystems. Com_PrintMessage is supplied by a
small Android logcat/host-stderr platform sink, not by a gameplay stub.
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
SIGNATURE = "void Com_PrintWarning(int channel, const char *fmt, ...)"
REQUIRED_SOURCE = (
    'I_strncpyz(dest, "^3", 4096);',
    "v3 = &dest[strlen(dest) + 1] - &dest[1];",
    "_vsnprintf(&dest[v3], 4096 - v3, fmt, va);",
    "Com_PrintMessage(channel, dest, 2);",
)
FORBIDDEN = (
    "_vsnprintf(",
    'I_strncpyz(dest, "^3", 4096);',
    "Godot",
    "fake Com_PrintWarning",
    "diagnostic Com_PrintWarning stub",
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
            raise ValueError("Original Com_PrintWarning contract missing: " + marker)

    # The original initializes "^3", then appends the formatted warning at byte
    # offset 2. Spell that out to avoid importing the unrelated I_strncpyz
    # service into this isolated audit, and use the C99 bounded formatter on
    # Android instead of the MSVC _vsnprintf spelling.
    adapted = body.replace(
        'I_strncpyz(dest, "^3", 4096);',
        "dest[0] = '^';\n    dest[1] = '3';\n    dest[2] = '\\0';",
    )
    adapted = adapted.replace(
        "v3 = &dest[strlen(dest) + 1] - &dest[1];",
        "v3 = 2;",
    )
    adapted = adapted.replace(
        "_vsnprintf(&dest[v3], 4096 - v3, fmt, va);",
        "std::vsnprintf(&dest[v3], sizeof(dest) - static_cast<std::size_t>(v3), fmt, va);\n    va_end(va);",
    )
    if adapted == body:
        raise ValueError("No Android portability adaptation was applied")
    for marker in FORBIDDEN:
        if marker in adapted:
            raise ValueError("Forbidden original/platform pattern remains: " + marker)
    if "Com_PrintMessage(channel, dest, 2);" not in adapted:
        raise ValueError("Original warning severity/output contract was lost")

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
        "original_com_print_warning_body_staged": True,
        "android_vsnprintf_portability_adaptation_only": True,
        "warning_color_prefix_and_type_2_preserved": True,
        "com_print_message_platform_sink": "Android logcat; host stderr for regression",
        "full_common_translation_unit_linked": False,
        "filesystem_startup_invoked": False,
        "fastfile_or_map_loaded": False,
        "renderer_or_gameplay_proven": False,
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_COM_PRINT_WARNING_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
