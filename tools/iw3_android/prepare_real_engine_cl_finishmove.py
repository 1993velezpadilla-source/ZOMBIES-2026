#!/usr/bin/env python3
"""Stage the authentic CL_FinishMove body for the next ARM64 client-link audit.

This resolves one real call edge from the original CL_CreateCmd object. It does
not link or invoke the live client runtime and cannot make the diagnostic APK
playable by itself.
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
SIGNATURE = "void __cdecl CL_FinishMove(usercmd_s *cmd)"
HEADER = (
    '#include "client.h"\n'
    '#include "cl_input.h"\n'
    '#include <cstring>\n'
    '#ifndef KEY_FORWARD\n'
    '#define KEY_FORWARD 2\n'
    '#endif\n'
)
REQUIRED = (
    "cmd->weapon = clients[0].cgameUserCmdWeapon;",
    "cmd->offHandIndex = clients[0].cgameUserCmdOffHandIndex;",
    "cmd->serverTime = clients[0].serverTime;",
    "cmd->angles[0] =",
    "cmd->angles[1] =",
    "cmd->angles[KEY_FORWARD] =",
    "cmd->buttons = buttons | clients[0].cgameExtraButtons;",
    "clients[0].cgameExtraButtons = 0;",
    "if (clients[0].bCmdForceValues)",
    "cmd->buttons = clients[0].iForceButtons;",
    "cmd->weapon = clients[0].iForceWeapon;",
    "cmd->offHandIndex = clients[0].forceOffhand;",
    "clients[0].bCmdForceValues = 0;",
)
FORBIDDEN = (
    "fake CL_FinishMove",
    "diagnostic CL_FinishMove stub",
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
            raise ValueError("Original CL_FinishMove contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in body:
            raise ValueError("Substitute client command finalizer detected: " + marker)
    if source.count("#define KEY_FORWARD 2") != 1:
        raise ValueError("Expected the original KEY_FORWARD index definition exactly once")

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
        "original_CL_FinishMove_body_preserved_verbatim": True,
        "weapon_offhand_server_time_and_viewangles_copied": True,
        "extra_buttons_cleared_after_merge": True,
        "forced_command_values_cleared_after_use": True,
        "key_forward_constant_preserved_from_original_source": True,
        "android_arm64_object_compiled": False,
        "cl_createcmd_finishmove_edge_resolved": False,
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
    print("IW3_ORIGINAL_CL_FINISHMOVE_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
