#!/usr/bin/env python3
"""Stage original BGame melee dvar storage and registration blocks for ARM64 audit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SOURCE = Path("src/bgame/bg_misc.cpp")
FUNCTION = "void __cdecl BG_RegisterDvars()"
DVARS = (
    ("mincw", "player_meleeRange"),
    ("mincx", "player_meleeWidth"),
    ("mincy", "player_meleeHeight"),
    ("mincz", "player_meleeChargeFriction"),
)


def unique_global_line(source: str, name: str) -> str:
    expected = f"const dvar_t *{name};"
    matches = [line.strip() for line in source.splitlines() if line.strip() == expected]
    if len(matches) != 1:
        raise ValueError(f"expected one original global definition for {name}, found {len(matches)}")
    return matches[0]


def registration_block(source: str, function_start: int, limit_name: str, dvar_name: str) -> str:
    assignment = f"{dvar_name} = Dvar_RegisterFloat("
    assignment_pos = source.find(assignment, function_start)
    if assignment_pos < 0 or source.find(assignment, assignment_pos + 1) >= 0:
        raise ValueError(f"expected one original registration assignment for {dvar_name}")
    prefix = f"    {limit_name}.value.max = "
    block_start = source.rfind(prefix, function_start, assignment_pos)
    if block_start < 0:
        raise ValueError(f"original DvarLimits setup missing for {dvar_name}")
    statement_end = source.find(";", assignment_pos)
    if statement_end < 0:
        raise ValueError(f"original registration statement is unterminated for {dvar_name}")
    return source[block_start:statement_end + 1]


def prepare(engine: Path, output: Path, report_path: Path) -> dict:
    source_path = engine / SOURCE
    original = source_path.read_bytes()
    source = original.decode("utf-8")
    if source.count(FUNCTION) != 1:
        raise ValueError("expected exactly one original BG_RegisterDvars definition")
    function_start = source.index(FUNCTION)
    globals_ = [unique_global_line(source, name) for _, name in DVARS]
    blocks = [registration_block(source, function_start, limit, name) for limit, name in DVARS]
    rendered = (
        "#include <universal/q_shared.h>\n"
        "#include <bgame/bg_public.h>\n"
        "#include <bgame/bg_local.h>\n\n"
        + "\n".join(globals_)
        + "\n\nvoid z2026_android_register_original_melee_dvars()\n{\n"
        + "    DvarLimits mincw;\n"
        + "    DvarLimits mincx;\n"
        + "    DvarLimits mincy;\n"
        + "    DvarLimits mincz;\n"
        + "\n\n".join(blocks)
        + "\n}\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_function_signature": FUNCTION,
        "original_dvar_definitions": [name for _, name in DVARS],
        "original_registration_blocks_preserved_verbatim": [name for _, name in DVARS],
        "registration_entrypoint": "z2026_android_register_original_melee_dvars",
        "source_unchanged": True,
        "runtime_invoked": False,
        "dvars_registered_at_runtime": False,
        "client_runtime_linked": False,
        "gameplay_proven": False,
        "playable_apk": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.engine, args.output, args.report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
