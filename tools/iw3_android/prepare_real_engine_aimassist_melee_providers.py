#!/usr/bin/env python3
"""Stage authentic SP auto-melee providers for the IW3 Android ARM64 edge audit.

Function bodies and the three aim-automelee dvar pointer definitions are
extracted verbatim from KisakCOD. This closes dependency edges only; it does
not register dvars, initialize CGame, or create a live Android client.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from tools.iw3_android.prepare_g_runframe_prereqs import function_source
except ModuleNotFoundError:
    from prepare_g_runframe_prereqs import function_source

SOURCE = Path("src/aim_assist/aim_assist.cpp")
FUNCTIONS = (
    (
        "static bool __cdecl AimAssist_DoBoundsIntersectCenterBox(\n"
        "    const float *clipMins,\n"
        "    const float *clipMaxs,\n"
        "    float clipHalfWidth,\n"
        "    float clipHalfHeight)",
        ("iassert(clipMins);", "iassert(clipMaxs);", "return (clipHalfWidth"),
    ),
    (
        "uint32_t __cdecl AimAssist_GetWeaponIndex(int32_t localClientNum, const playerState_s *ps)",
        ("BG_GetViewmodelWeaponIndex(ps)", "BG_GetNumWeapons()"),
    ),
    (
        "const AimScreenTarget *__cdecl AimAssist_GetBestTarget(\n"
        "    const AimAssistGlobals *aaGlob,\n"
        "    float range,\n"
        "    float regionWidth,\n"
        "    float regionHeight)",
        ("AimAssist_DoBoundsIntersectCenterBox(", "aaGlob->screenTargets[targetIndex].distSqr"),
    ),
    (
        "const AimScreenTarget *__cdecl AimAssist_GetTargetFromEntity(const AimAssistGlobals *aaGlob, int32_t entIndex)",
        ("if (entIndex == ENTITYNUM_NONE)", "aaGlob->screenTargets[targetIndex].entIndex == entIndex"),
    ),
    (
        "void __cdecl AimAssist_ClearAutoMeleeTarget(AimAssistGlobals *aaGlob)",
        ("aaGlob->autoMeleeTargetEnt = ENTITYNUM_NONE;", "aaGlob->autoMeleeActive = 0;"),
    ),
    (
        "char __cdecl AimAssist_UpdateAutoMeleeTarget(AimAssistGlobals *aaGlob)",
        ("AimAssist_GetTargetFromEntity(", "Vec3Sub(screenTarget->aimPos, aaGlob->viewOrigin, targetDir);"),
    ),
    (
        "void __cdecl AimAssist_SetAutoMeleeTarget(AimAssistGlobals *aaGlob, const AimScreenTarget *screenTarget)",
        ("AimAssist_ClearAutoMeleeTarget(aaGlob);", "AimAssist_UpdateAutoMeleeTarget(aaGlob);"),
    ),
    (
        "void __cdecl AimAssist_ApplyAutoMelee(const AimInput *input, AimOutput *output)",
        (
            "AimAssist_GetBestTarget(",
            "DiffTrackAngle(",
            "AimAssist_UpdateAutoMeleeTarget(aaGlob)",
            "AimAssist_ClearAutoMeleeTarget(aaGlob);",
        ),
    ),
    (
        "void __cdecl AimAssist_ApplyMeleeCharge(const AimInput *input, AimOutput *output)",
        (
            "output->meleeChargeYaw = 0.0;",
            "player_meleeRange->current.value",
            "output->meleeChargeYaw = vectoyaw(targetDir);",
        ),
    ),
)
DVAR_NAMES = (
    "aim_automelee_enabled",
    "aim_automelee_lerp",
    "aim_automelee_range",
)
HEADER = (
    "#include <cmath>\n"
    "#include <universal/q_shared.h>\n"
    '#include "aim_assist/aim_assist.h"\n'
    '#include "client/client.h"\n'
    '#include "cgame/cg_main.h"\n'
    '#include "cgame/cg_local.h"\n'
    '#include "universal/com_math.h"\n'
    '#include "universal/assertive.h"\n'
    '#include "qcommon/qcommon.h"\n'
    '#include "bgame/bg_public.h"\n'
    "extern const dvar_t *player_meleeRange;\n"
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD aim_assist.cpp")

    original = source_path.read_bytes()
    source = original.decode("utf-8")
    bodies = []
    for signature, markers in FUNCTIONS:
        body = function_source(source, signature)
        for marker in markers:
            if marker not in body:
                raise ValueError(f"Original auto-melee contract missing in {signature.splitlines()[0]}: {marker}")
        bodies.append((signature, body))

    source_lines = source.splitlines()
    dvar_lines = []
    for name in DVAR_NAMES:
        matches = [
            line for line in source_lines
            if re.fullmatch(
                rf"\s*const dvar_t\s*\*\s*{re.escape(name)}\s*=\s*nullptr;\s*",
                line,
            )
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one original null-initialized dvar pointer: {name}")
        dvar_lines.append(matches[0])

    rendered = (
        HEADER
        + "\n".join(dvar_lines)
        + "\n\n"
        + "\n\n".join(body for _, body in bodies)
        + "\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    if source_path.read_bytes() != original:
        raise RuntimeError("Vendored KisakCOD aim_assist.cpp changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_function_bodies_preserved_verbatim": [
            signature.split("(")[0].split()[-1] for signature, _ in bodies
        ],
        "original_dvar_pointer_lines_preserved_verbatim": list(DVAR_NAMES),
        "player_meleeRange_is_external_engine_dependency": True,
        "source_unchanged": True,
        "resolved_original_aimassist_edges": [
            "AimAssist_DoBoundsIntersectCenterBox",
            "AimAssist_GetWeaponIndex",
            "AimAssist_GetBestTarget",
            "AimAssist_GetTargetFromEntity",
            "AimAssist_ClearAutoMeleeTarget",
            "AimAssist_UpdateAutoMeleeTarget",
            "AimAssist_SetAutoMeleeTarget",
            "AimAssist_ApplyAutoMelee",
            "AimAssist_ApplyMeleeCharge",
        ],
        "dvars_registered_at_runtime": False,
        "cgame_state_initialized": False,
        "client_runtime_linked": False,
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
    evidence = prepare(args.engine, args.output, args.report)
    print("IW3_ORIGINAL_AIMASSIST_AUTO_MELEE_PROVIDERS_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
