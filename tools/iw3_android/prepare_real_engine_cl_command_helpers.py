#!/usr/bin/env python3
"""Stage the authentic SP CL_KeyMove and CL_CmdButtons input functions for ARM64 edge auditing.

The bodies and key/button constants come from vendored KisakCOD cl_input.cpp.
This compiles the next real client-input providers; it does not link or invoke
the live client runtime and does not prove a playable APK.
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
SP_MARKER = "#elif KISAK_SP\n"
KEY_SIGNATURE = "void __cdecl CL_KeyMove(usercmd_s *cmd)"
BUTTON_HELPER_SIGNATURE = "void __cdecl CL_UpdateCmdButton(int *cmdButtons, int kbButton, int buttonFlag)"
BUTTONS_SIGNATURE = "void __cdecl CL_CmdButtons(usercmd_s *cmd)"
MACRO_BEGIN = "#define KEY_LEFT 0"
MACRO_END = "#define KEY_BIT_COUNT 21"
STATE_BEGIN = "static bool s_scriptWasNoProne;"

HEADER = (
    '#include "client.h"\n'
    '#include "cl_input.h"\n'
    '#include <qcommon/msg.h>\n'
    '#include <universal/q_shared.h>\n'
    'extern kbutton_t kb[29];\n'
)

KEY_REQUIRED = (
    "noProne = (clients[0].snap.ps.pm_flags & PMF_SCRIPT_NO_PRONE) != 0;",
    "noCrouch = (clients[0].snap.ps.pm_flags & PMF_SCRIPT_NO_CROUCH) != 0;",
    "CL_StanceButtonUpdate();",
    "CL_AddCurrentStanceToCmd(cmd);",
    "CL_KeyState(&kb[KEY_FORWARD])",
    "cmd->forwardmove = ClampChar(forward);",
    "cmd->rightmove   = ClampChar(side);",
    "cmd->upmove      = ClampChar(up);",
)
BUTTON_HELPER_REQUIRED = (
    "if (kb[kbButton].active || kb[kbButton].wasPressed)",
    "*cmdButtons |= buttonFlag;",
    "kb[kbButton].wasPressed = 0;",
)
BUTTONS_REQUIRED = (
    "CL_UpdateCmdButton(&cmd->buttons, 14, BUTTON_ATTACK);",
    "CL_UpdateCmdButton(&cmd->buttons, 19, BUTTON_USE);",
    "CL_UpdateCmdButton(&cmd->buttons, 20, BUTTON_RELOAD);",
    "clients[0].snap.ps.pm_type == PM_NOCLIP",
    "cmd->buttons < (1 << KEY_BIT_COUNT)",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD cl_input.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    if source.count(SP_MARKER) != 1:
        raise ValueError("Expected exactly one original KISAK_SP input branch")
    sp_source = source[source.index(SP_MARKER) + len(SP_MARKER):]

    key_body = function_source(sp_source, KEY_SIGNATURE)
    helper_body = function_source(sp_source, BUTTON_HELPER_SIGNATURE)
    buttons_body = function_source(sp_source, BUTTONS_SIGNATURE)

    macro_start = source.find(MACRO_BEGIN)
    macro_end_start = source.find(MACRO_END, macro_start)
    if macro_start < 0 or macro_end_start < 0:
        raise ValueError("Original key/button constant block is incomplete")
    macro_end = macro_end_start + len(MACRO_END)
    macros = source[macro_start:macro_end]
    if macros.count(MACRO_BEGIN) != 1 or macros.count(MACRO_END) != 1:
        raise ValueError("Original key/button constant block is ambiguous")

    state_start = sp_source.find(STATE_BEGIN)
    state_end = sp_source.find(KEY_SIGNATURE, state_start)
    if state_start < 0 or state_end < 0:
        raise ValueError("Original SP stance-suppression state was not found")
    state = sp_source[state_start:state_end]
    for declaration in (
        "static bool s_scriptWasNoProne;",
        "static bool s_scriptWasNoCrouch;",
        "static bool s_scriptSuppressProne;",
        "static bool s_scriptSuppressCrouch;",
    ):
        if state.count(declaration) != 1:
            raise ValueError("Missing or duplicate original SP stance state: " + declaration)
    if "{" in state or "}" in state:
        raise ValueError("Unexpected code in the original SP stance-state declaration block")

    for marker in KEY_REQUIRED:
        if marker not in key_body:
            raise ValueError("Original SP CL_KeyMove contract missing: " + marker)
    for marker in BUTTON_HELPER_REQUIRED:
        if marker not in helper_body:
            raise ValueError("Original CL_UpdateCmdButton contract missing: " + marker)
    for marker in BUTTONS_REQUIRED:
        if marker not in buttons_body:
            raise ValueError("Original SP CL_CmdButtons contract missing: " + marker)

    rendered = (
        HEADER + "\n" + macros + "\n\n" + state + "\n"
        + helper_body + "\n\n" + key_body + "\n\n" + buttons_body + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD cl_input.cpp changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "sp_branch_selected": True,
        "original_key_button_macros_preserved_verbatim": True,
        "original_sp_stance_state_preserved_verbatim": True,
        "key_move_signature": KEY_SIGNATURE,
        "key_move_body_sha256": hashlib.sha256(key_body.encode("utf-8")).hexdigest(),
        "cmd_button_helper_signature": BUTTON_HELPER_SIGNATURE,
        "cmd_button_helper_body_sha256": hashlib.sha256(helper_body.encode("utf-8")).hexdigest(),
        "cmd_buttons_signature": BUTTONS_SIGNATURE,
        "cmd_buttons_body_sha256": hashlib.sha256(buttons_body.encode("utf-8")).hexdigest(),
        "original_bodies_preserved_verbatim": True,
        "android_arm64_object_compiled": False,
        "key_move_and_cmd_buttons_linked_to_client_chain": False,
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
    print("IW3_ORIGINAL_CL_KEYMOVE_CMDBUTTONS_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
