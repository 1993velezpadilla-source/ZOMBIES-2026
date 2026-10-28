#!/usr/bin/env python3
"""Stage original KisakCOD string/format helpers needed by filesystem startup.

The function bodies come from src/universal/q_shared.cpp. Only Com_sprintf's
MSVC _vsnprintf call is adapted to bounded C99 vsnprintf while preserving the
engine's -1-on-truncation contract. This source is an audit provider, not a
complete runtime or gameplay implementation.
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

SOURCE = Path("src/universal/q_shared.cpp")
FUNCTIONS = (
    "void I_strncat(char* dest, int size, const char* src)",
    "void I_strncpyz(char* dest, const char* src, int destsize)",
    "int I_stricmp(const char* s0, const char* s1)",
    "int Com_sprintf(char *dest, uint32_t size, const char *fmt, ...)",
)
REQUIRED_SOURCE = (
    "void I_strncat(char* dest, int size, const char* src)",
    "Com_Error(ERR_FATAL, \"I_strncat: already overflowed\");",
    "void I_strncpyz(char* dest, const char* src, int destsize)",
    "return I_strnicmp(s0, s1, 0x7FFFFFFF);",
    "result = _vsnprintf(dest, size, fmt, va);",
    "dest[size - 1] = 0;",
)
FORBIDDEN = (
    "_vsnprintf(",
    "fake I_strncpyz",
    "diagnostic Com_sprintf stub",
    "Godot",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD q_shared.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")

    bodies = {signature: function_source(source, signature) for signature in FUNCTIONS}
    for marker in REQUIRED_SOURCE:
        if marker not in source:
            raise ValueError("Original q_shared service contract missing: " + marker)

    # MSVC _vsnprintf returns -1 when truncated. POSIX/C99 vsnprintf returns
    # the required length, so translate truncation back to the engine contract.
    # A zero-sized destination is rejected before indexing size - 1.
    fmt_signature = FUNCTIONS[-1]
    fmt_body = bodies[fmt_signature]
    adapted_fmt = fmt_body.replace(
        "result = _vsnprintf(dest, size, fmt, va);",
        "if (size == 0) { va_end(va); return -1; }\n"
        "    result = std::vsnprintf(dest, static_cast<std::size_t>(size), fmt, va);\n"
        "    va_end(va);\n"
        "    if (result >= 0 && static_cast<uint32_t>(result) >= size) result = -1;",
    )
    if adapted_fmt == fmt_body:
        raise ValueError("Could not apply the bounded Com_sprintf portability adaptation")
    bodies[fmt_signature] = adapted_fmt

    rendered_bodies = "\n\n".join(bodies[signature] for signature in FUNCTIONS)
    for marker in FORBIDDEN:
        if marker in rendered_bodies:
            raise ValueError("Forbidden platform/fake-provider pattern remains: " + marker)
    for signature in FUNCTIONS[:-1]:
        if bodies[signature] != function_source(source, signature):
            raise ValueError("Original string helper changed unexpectedly: " + signature)
    if "std::vsnprintf(dest, static_cast<std::size_t>(size), fmt, va);" not in adapted_fmt:
        raise ValueError("Com_sprintf is not using bounded portable formatting")
    if "va_end(va);" not in adapted_fmt:
        raise ValueError("Com_sprintf varargs lifecycle is incomplete")

    rendered = (
        '#include "iw3_android_fs_startup_compat.h"\n'
        "#include <cstddef>\n"
        "#include <cstdarg>\n"
        "#include <cstdio>\n"
        "#include <cstring>\n\n"
        + rendered_bodies
        + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD q_shared.cpp changed during extraction")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "original_function_body_sha256": {
            signature: hashlib.sha256(function_source(source, signature).encode("utf-8")).hexdigest()
            for signature in FUNCTIONS
        },
        "original_I_strncat_I_strncpyz_I_stricmp_bodies_staged_verbatim": True,
        "original_Com_sprintf_body_staged_with_bounded_vsnprintf_adaptation": True,
        "com_sprintf_minus_one_on_truncation_preserved": True,
        "com_sprintf_zero_size_rejected_before_buffer_indexing": True,
        "filesystem_startup_invoked": False,
        "fastfile_or_map_loaded": False,
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
    print("IW3_ORIGINAL_Q_SHARED_STRING_SERVICES_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
