#!/usr/bin/env python3
"""Stage the original KisakCOD command tokenizer core for the Android ARM64 audit.

Only the original tokenization/end-tokenization functions and the original
cmd_argsPrivate state declaration are extracted. The command dispatcher,
registration, Cmd_Init, and runtime invocation are intentionally not included.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ImportError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/qcommon/cmd.cpp")
STATE_DECLARATION = "CmdArgsPrivate cmd_argsPrivate;"
FUNCTIONS = (
    "void __cdecl Cmd_TokenizeStringWithLimit(char *text_in, int32_t  max_tokens)",
    "void __cdecl Cmd_TokenizeStringKernel(char *text_in, int32_t  max_tokens, CmdArgs *args, CmdArgsPrivate *argsPriv)",
    "int32_t  __cdecl Cmd_TokenizeStringInternal(char *text_in, int32_t  max_tokens, const char **argv, CmdArgsPrivate *argsPriv)",
    "bool __cdecl Cmd_IsWhiteSpaceChar(uint8_t letter)",
    "void __cdecl AssertCmdArgsConsistency(const CmdArgs *args, const CmdArgsPrivate *argsPriv)",
    "void __cdecl Cmd_TokenizeString(char *text_in)",
    "void __cdecl Cmd_EndTokenizedString()",
    "void __cdecl Cmd_EndTokenizedStringKernel(CmdArgs *args, CmdArgsPrivate *argsPriv)",
)
REQUIRED = (
    "Cmd_TokenizeStringWithLimit(text_in, 512 - cmd_argsPrivate.totalUsedArgvPool);",
    "Cmd_TokenizeStringKernel(text_in, max_tokens, &cmd_args, &cmd_argsPrivate);",
    "Cmd_TokenizeStringInternal(text_in, max_tokens, args->argv[args->nesting], argsPriv);",
    "argsPriv->totalUsedArgvPool -= args->argc[args->nesting];",
    "argsPriv->totalUsedTextPool -= argsPriv->usedTextPool[args->nesting--];",
    "return letter != 20 && letter != 21 && letter != 22 && letter <= 0x20u;",
)
FORBIDDEN = (
    "CmdArgsPrivate cmd_argsPrivate{};",
    "CmdArgs cmd_args{};",
    "Cmd_Init(",
    "Cmd_AddCommandInternal(",
    "fake Cmd_TokenizeString",
    "stub Cmd_TokenizeString",
    "Godot",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    state_matches = re.findall(r"(?m)^CmdArgsPrivate cmd_argsPrivate;$", source)
    if len(state_matches) != 1:
        raise ValueError("Expected exactly one original CmdArgsPrivate cmd_argsPrivate state declaration")
    state = state_matches[0]
    bodies = [function_source(source, signature) for signature in FUNCTIONS]

    generated = (
        "// Generated from original KisakCOD src/qcommon/cmd.cpp; do not edit.\n"
        "#include <universal/q_shared.h>\n"
        "#include <universal/assertive.h>\n"
        "#include <qcommon/cmd.h>\n"
        "#include <qcommon/qcommon.h>\n"
        "#include <cstdint>\n\n"
        + state + "\n\n"
        + "\n\n".join(bodies)
        + "\n"
    )
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original command tokenizer contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in generated:
            raise ValueError("Command initialization/dispatcher substitute or forbidden marker found: " + marker)

    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD cmd.cpp")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD cmd.cpp changed during extraction")
    if generated.count(STATE_DECLARATION) != 1:
        raise ValueError("Generated tokenizer source must define cmd_argsPrivate exactly once")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "state_declaration": STATE_DECLARATION,
        "state_declaration_sha256": hashlib.sha256(state.encode("utf-8")).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_cmd_argsPrivate_state_preserved": True,
        "original_tokenizer_and_end_functions_preserved_verbatim": True,
        "command_dispatcher_not_extracted": True,
        "command_registration_not_extracted": True,
        "Cmd_Init_not_extracted": True,
        "cmd_args_nesting_initialized_by_original_Cmd_Init": False,
        "archive_linked_to_jni": False,
        "filesystem_startup_invoked": False,
        "gameplay_verified": False,
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
    print("IW3_ORIGINAL_CMD_TOKENIZER_STAGED_FOR_ARM64_AUDIT", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
