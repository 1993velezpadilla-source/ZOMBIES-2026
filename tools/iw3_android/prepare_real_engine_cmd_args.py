#!/usr/bin/env python3
"""Extract original KisakCOD command argument state/accessors for ARM64 auditing.

The original CmdArgs cmd_args storage declaration and two upstream accessor
bodies are staged verbatim. The tokenizer/dispatcher are not extracted and this
archive is not linked into the JNI diagnostic APK or a playable runtime.
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
FUNCTIONS = (
    "int32_t \tCmd_Argc(void)",
    "const char* Cmd_Argv(int32_t  arg)",
)
REQUIRED = (
    "return cmd_args.argc[cmd_args.nesting];",
    "return (char*)(cmd_args.argv[cmd_args.nesting][arg]);",
    "if ((unsigned)arg >= cmd_args.argc[cmd_args.nesting])",
)
FORBIDDEN = (
    "CmdArgs cmd_args{};",
    "cmd_args.nesting = 0;",
    "fake Cmd_Argc",
    "fake Cmd_Argv",
    "Godot",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = [function_source(source, signature) for signature in FUNCTIONS]
    state_matches = re.findall(r"(?m)^CmdArgs cmd_args;$", source)
    if len(state_matches) != 1:
        raise ValueError(
            "Expected exactly one original CmdArgs cmd_args storage declaration"
        )
    state_declaration = state_matches[0]
    generated = (
        "// Generated from original KisakCOD src/qcommon/cmd.cpp; do not edit.\n"
        "#include <universal/q_shared.h>\n"
        "#include <universal/assertive.h>\n"
        "#include <qcommon/cmd.h>\n"
        "#include <cstdint>\n\n"
        + state_declaration + "\n\n"
        + "\n\n".join(bodies)
        + "\n"
    )
    for marker in REQUIRED:
        if marker not in generated:
            raise ValueError("Original command accessor contract missing: " + marker)
    for marker in FORBIDDEN:
        if marker in generated:
            raise ValueError("Command-state substitute or forbidden marker found: " + marker)
    output = output.resolve()
    if output == source_path:
        raise ValueError("Refusing to overwrite authentic KisakCOD cmd.cpp")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8", newline="\n")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD cmd.cpp changed during extraction")
    if generated.count("CmdArgs cmd_args;") != 1:
        raise ValueError("Generated audit source must define original cmd_args storage exactly once")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "state_declaration_sha256": hashlib.sha256(state_declaration.encode("utf-8")).hexdigest(),
        "function_signatures": list(FUNCTIONS),
        "function_body_sha256": {
            signature: hashlib.sha256(body.encode("utf-8")).hexdigest()
            for signature, body in zip(FUNCTIONS, bodies)
        },
        "generated_sha256": hashlib.sha256(generated.encode("utf-8")).hexdigest(),
        "original_Cmd_Argc_body_preserved": True,
        "original_Cmd_Argv_body_preserved": True,
        "original_cmd_args_state_declaration_preserved": True,
        "cmd_args_state_definition_in_audit_archive": True,
        "command_tokenizer_not_reimplemented": True,
        "command_dispatcher_not_extracted": True,
        "archive_linked_to_jni": False,
        "filesystem_startup_invoked": False,
        "gameplay_verified": False,
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
    print("IW3_ORIGINAL_CMD_ARGS_ACCESSORS_STAGED_FOR_ARM64_AUDIT",
          json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
