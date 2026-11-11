#!/usr/bin/env python3
"""Stage authentic CL_GetMouseMovement and CL_MouseMove for ARM64 link auditing.

The original client functions are extracted verbatim. The combined object can
resolve the CL_CreateCmd -> CL_MouseMove edge and the CL_MouseMove ->
CL_GetMouseMovement edge, while leaving the real aim-assist/client-state
services visible. This is not a live client runtime.
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
MOUSE_HELPER_SIGNATURE = "void __cdecl CL_GetMouseMovement(clientActive_t *cl, float *mx, float *my)"
MOUSE_SIGNATURE = "void __cdecl CL_MouseMove(usercmd_s *cmd)"
HEADER = (
    '#include "client.h"\n'
    '#include "cl_input.h"\n'
    '#include <universal/q_shared.h>\n'
    '#include <universal/com_math.h>\n'
    '#include <aim_assist/aim_assist.h>\n'
    '#include <qcommon/snap_float.h>\n'
    '#include <gfx_d3d/r_dvars.h>\n'
    '#include <cmath>\n'
    'extern unsigned int frame_msec;\n'
    'extern kbutton_t kb[29];\n'
    'struct playerState_s;\n'
    'const playerState_s *__cdecl CG_GetPredictedPlayerState(int localClientNum);\n'
    '#ifndef KEY_STRAFE\n'
    '#define KEY_STRAFE 8\n'
    '#endif\n'
    '#ifndef KEY_MLOOK\n'
    '#define KEY_MLOOK 13\n'
    '#endif\n'
)
MOUSE_REQUIRED = (
    "CL_GetMouseMovement(clients, &mx, &my);",
    "AimAssist_UpdateMouseInput(&aimInput, &aimOutput);",
    "CG_GetPredictedPlayerState(0)",
    "clients[0].viewangles[1] = clients[0].viewangles[1] - delta;",
    "clients[0].viewangles[0] = clients[0].viewangles[0] + deltaa;",
    "cmd->meleeChargeYaw = aimOutput.meleeChargeYaw;",
    "cmd->meleeChargeDist = aimOutput.meleeChargeDist;",
)
HELPER_REQUIRED = (
    "if (m_filter->current.enabled)",
    "cl->mouseIndex ^= 1u;",
    "cl->mouseDx[cl->mouseIndex] = 0;",
    "cl->mouseDy[cl->mouseIndex] = 0;",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD cl_input.cpp")
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    helper_body = function_source(source, MOUSE_HELPER_SIGNATURE)
    mouse_body = function_source(source, MOUSE_SIGNATURE)

    for marker in HELPER_REQUIRED:
        if marker not in helper_body:
            raise ValueError("Original CL_GetMouseMovement contract missing: " + marker)
    for marker in MOUSE_REQUIRED:
        if marker not in mouse_body:
            raise ValueError("Original CL_MouseMove contract missing: " + marker)
    for macro, value in (("KEY_STRAFE", 8), ("KEY_MLOOK", 13)):
        definition = f"#define {macro} {value}"
        if source.count(definition) != 1:
            raise ValueError("Expected original key constant exactly once: " + definition)
    for declaration in ("unsigned int frame_msec;", "kbutton_t kb[29];"):
        if source.count(declaration) != 1:
            raise ValueError("Expected original client input state declaration exactly once: " + declaration)
    forbidden_headers = ("win32/win_local.h", "cgame/cg_main.h", "game/g_local.h", "server/sv_public.h")
    if any(header in HEADER for header in forbidden_headers):
        raise ValueError("Android client input slice must not import Win32 or renderer-heavy headers")

    rendered = HEADER + "\n" + helper_body + "\n\n" + mouse_body + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD cl_input.cpp changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "helper_signature": MOUSE_HELPER_SIGNATURE,
        "helper_body_sha256": hashlib.sha256(helper_body.encode("utf-8")).hexdigest(),
        "mouse_signature": MOUSE_SIGNATURE,
        "mouse_body_sha256": hashlib.sha256(mouse_body.encode("utf-8")).hexdigest(),
        "original_CL_GetMouseMovement_body_preserved_verbatim": True,
        "original_CL_MouseMove_body_preserved_verbatim": True,
        "original_key_constants_preserved": {"KEY_STRAFE": 8, "KEY_MLOOK": 13},
        "win32_input_header_excluded": True,
        "android_arm64_object_compiled": False,
        "cl_createcmd_mousemove_edge_resolved": False,
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
    print("IW3_ORIGINAL_CL_MOUSEMOVE_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
