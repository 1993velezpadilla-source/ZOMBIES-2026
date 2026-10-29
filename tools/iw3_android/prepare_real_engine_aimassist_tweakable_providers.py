#!/usr/bin/env python3
"""Stage authentic IW3 aim-assist tweakable providers for an ARM64 edge audit.

Only the original AimAssist_UpdateTweakables/AimAssist_UpdateAdsLerp bodies
and their original dvar pointer globals are staged. This closes two real
client-input dependency edges; it does not initialize CGame/aim-assist state
or link a live Android client runtime.
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
        "void __cdecl AimAssist_UpdateTweakables(const AimInput *input)",
        (
            "scrPlaceView[localClientNum].scaleVirtualToReal[0]",
            "aim_slowdown_region_width->current.value",
            "aaGlob->tweakables.lockOnRegionHeight",
        ),
    ),
    (
        "void __cdecl AimAssist_UpdateAdsLerp(const AimInput *input)",
        (
            "aaGlob->adsLerp = input->ps->fWeaponPosFrac;",
            "(input->buttons & BUTTON_ADS) != 0",
        ),
    ),
)
DVAR_NAMES = (
    "aim_slowdown_region_width",
    "aim_slowdown_region_height",
    "aim_autoaim_region_width",
    "aim_autoaim_region_height",
    "aim_automelee_region_width",
    "aim_automelee_region_height",
    "aim_lockon_region_width",
    "aim_lockon_region_height",
)
HEADER = (
    "#include <universal/q_shared.h>\n"
    '#include "aim_assist/aim_assist.h"\n'
    '#include "client/client.h"\n'
    '#include "cgame/cg_main.h"\n'
    '#include "cgame/cg_local.h"\n'
    "#include <universal/assertive.h>\n"
    '#include "qcommon/qcommon.h"\n'
)


def prepare(engine: Path, output: Path, report_path: Path | None = None) -> dict:
    engine = engine.resolve()
    source_path = engine / SOURCE
    output = output.resolve()
    if output == source_path.resolve():
        raise ValueError("Refusing to overwrite authentic KisakCOD source")

    source_bytes = source_path.read_bytes()
    source = source_bytes.decode("utf-8")
    bodies = []
    for signature, markers in FUNCTIONS:
        body = function_source(source, signature)
        for marker in markers:
            if marker not in body:
                raise ValueError(f"Original helper marker missing in {signature}: {marker}")
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
    if source_path.read_bytes() != source_bytes:
        raise RuntimeError("Vendored aim-assist source changed during staging")

    evidence = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "generated_source_sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        "original_helper_bodies_preserved_verbatim": [
            signature.split("(")[0].split()[-1] for signature, _ in bodies
        ],
        "original_dvar_pointer_lines_preserved_verbatim": DVAR_NAMES,
        "source_unchanged": True,
        "resolved_original_client_edges": [
            "AimAssist_UpdateTweakables",
            "AimAssist_UpdateAdsLerp",
        ],
        "still_unresolved_authentic_services": [
            "AimAssist_ApplyAutoMelee",
            "AimAssist_ApplyMeleeCharge",
            "MyAssertHandler",
            "scrPlaceView",
        ],
        "aimassist_dvars_registered_at_runtime": False,
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
    print("IW3_ORIGINAL_AIMASSIST_TWEAKABLE_PROVIDERS_STAGED", json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
