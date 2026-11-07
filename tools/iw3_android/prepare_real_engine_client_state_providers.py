#!/usr/bin/env python3
"""Stage two authentic KisakCOD client-state providers for an ARM64 edge audit.

The generated translation unit preserves the original AimAssist_UpdateMouseInput
and CG_GetPredictedPlayerState bodies and the exact original state globals they
read. It is an object-level dependency audit only; it does not initialize CGame
or aim-assist and is not linked into the JNI diagnostic APK.
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

AIM_SOURCE = Path("src/aim_assist/aim_assist.cpp")
CG_SOURCE = Path("src/cgame/cg_main.cpp")
AIM_SIGNATURE = "void __cdecl AimAssist_UpdateMouseInput(const AimInput *input, AimOutput *output)"
CG_SIGNATURE = "const playerState_s *__cdecl CG_GetPredictedPlayerState(int localClientNum)"
AIM_GLOBAL = "AimAssistGlobals aaGlobArray[1] = { 0 };"
CG_GLOBAL = "cg_s cgArray[1];"
HEADER = (
    "#include <universal/q_shared.h>\n"
    '#include "aim_assist/aim_assist.h"\n'
    "#include <universal/profile.h>\n"
    '#include "cgame/cg_main.h"\n'
    '#include "cgame/cg_local.h"\n'
)

AIM_REQUIRED = (
    'PROF_SCOPED("AimAssist_UpdateMouseInput");',
    "aaGlobArray[input->localClientNum].initialized",
    "AimAssist_UpdateTweakables(input);",
    "AimAssist_UpdateAdsLerp(input);",
    "AimAssist_ApplyAutoMelee(input, output);",
    "AimAssist_ApplyMeleeCharge(input, output);",
)
CG_REQUIRED = (
    "if (localClientNum)",
    "MyAssertHandler(",
    "return &cgArray[0].predictedPlayerState;",
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    aim_path = engine / AIM_SOURCE
    cg_path = engine / CG_SOURCE
    output = output.resolve()
    if output in (aim_path.resolve(), cg_path.resolve()):
        raise ValueError("Refusing to overwrite authentic KisakCOD source")

    aim_bytes = aim_path.read_bytes()
    cg_bytes = cg_path.read_bytes()
    aim_text = aim_bytes.decode("utf-8")
    cg_text = cg_bytes.decode("utf-8")
    aim_body = function_source(aim_text, AIM_SIGNATURE)
    cg_body = function_source(cg_text, CG_SIGNATURE)
    if aim_text.splitlines().count(AIM_GLOBAL) != 1:
        raise ValueError("Expected exactly one original aaGlobArray definition")
    if cg_text.splitlines().count(CG_GLOBAL) != 1:
        raise ValueError("Expected exactly one original cgArray definition")
    for marker in AIM_REQUIRED:
        if marker not in aim_body:
            raise ValueError("Original aim-assist body marker missing: " + marker)
    for marker in CG_REQUIRED:
        if marker not in cg_body:
            raise ValueError("Original predicted-state body marker missing: " + marker)

    rendered = (
        HEADER
        + AIM_GLOBAL + "\n"
        + CG_GLOBAL + "\n\n"
        + aim_body + "\n\n"
        + cg_body + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if aim_path.read_bytes() != aim_bytes or cg_path.read_bytes() != cg_bytes:
        raise RuntimeError("Vendored original engine source changed during staging")

    evidence = {
        "aim_source": str(AIM_SOURCE),
        "aim_source_sha256": hashlib.sha256(aim_bytes).hexdigest(),
        "aim_function_sha256": hashlib.sha256(aim_body.encode("utf-8")).hexdigest(),
        "cg_source": str(CG_SOURCE),
        "cg_source_sha256": hashlib.sha256(cg_bytes).hexdigest(),
        "cg_function_sha256": hashlib.sha256(cg_body.encode("utf-8")).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_AimAssist_UpdateMouseInput_body_preserved_verbatim": True,
        "original_CG_GetPredictedPlayerState_body_preserved_verbatim": True,
        "original_aaGlobArray_definition_preserved": True,
        "original_cgArray_definition_preserved": True,
        "source_files_unchanged": True,
        "aimassist_helper_services_still_unresolved": [
            "AimAssist_UpdateTweakables", "AimAssist_UpdateAdsLerp",
            "AimAssist_ApplyAutoMelee", "AimAssist_ApplyMeleeCharge",
        ],
        "client_state_runtime_initialized": False,
        "client_input_runtime_linked": False,
        "runtime_invoked": False,
        "real_map_loaded": False,
        "renderer_verified": False,
        "gameplay_proven": False,
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
    report = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_CLIENT_STATE_PROVIDERS_STAGED", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
