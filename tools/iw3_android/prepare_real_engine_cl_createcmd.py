#!/usr/bin/env python3
"""Stage the authentic CL_CreateCmd body for Android ARM64 ABI compilation.

This does not link or invoke the client runtime. It verifies that the upstream
Android-only touch hook remains inside the real CL_CreateCmd, after mouse input
and before CL_FinishMove encodes the command/view angles.
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

SOURCE = Path("src/client/cl_input.cpp")
SIGNATURE = "void __cdecl CL_CreateCmd(usercmd_s *result)"
HEADER = (
    '#include "client.h"\n'
    '#include "cl_input.h"\n'
    '#include "iw3_android_platform.h"\n'
    '#include <cstring>\n'
)
REQUIRED = (
    "oldAngles = clients[0].viewangles[0];",
    "CL_AdjustAngles();",
    "memset(result, 0, sizeof(usercmd_s));",
    "CL_CmdButtons(result);",
    "CL_KeyMove(result);",
    "CL_MouseMove(result);",
    "#if defined(__ANDROID__)",
    "z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);",
    "#endif",
    "CL_FinishMove(result);",
)
FORBIDDEN = (
    "fake CL_CreateCmd",
    "diagnostic CL_CreateCmd stub",
    "Godot",
    "return; // touch-only replacement",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD cl_input.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    body = function_source(source, SIGNATURE)

    for marker in REQUIRED:
        if marker not in body:
            raise ValueError("Original CL_CreateCmd touch contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Substitute client input code detected: " + marker)

    touch_at = body.index("z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);")
    mouse_at = body.index("CL_MouseMove(result);")
    finish_at = body.index("CL_FinishMove(result);")
    if not mouse_at < touch_at < finish_at:
        raise ValueError("Touch hook must run after original mouse input and before CL_FinishMove")
    if body.count("z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles);") != 1:
        raise ValueError("Expected exactly one touch-to-usercmd call in original CL_CreateCmd")

    rendered = HEADER + "\n" + body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD cl_input.cpp changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "function_signature": SIGNATURE,
        "function_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "original_CL_CreateCmd_body_preserved_verbatim": True,
        "touch_hook_after_CL_MouseMove": True,
        "touch_hook_before_CL_FinishMove": True,
        "touch_hook_count": 1,
        "actual_client_state_headers_used": True,
        "android_arm64_object_compiled": False,
        "client_runtime_linked": False,
        "client_runtime_invoked": False,
        "real_map_loaded": False,
        "gameplay_proven": False,
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
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_CL_CREATECMD_TOUCH_HOOK_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
