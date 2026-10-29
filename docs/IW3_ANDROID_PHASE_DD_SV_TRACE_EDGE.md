# IW3 Android ARM64 — phase DD: original server trace edge

Date: 2026-10-29

## Baseline

Phase DC verified the original mover collision helper edge in AArch64 objects: `G_TestEntityPosition -> G_TraceCapsule` and `G_TestEntityPosition -> Trace_GetEntityHitId`. The real `SV_Trace` and `SV_SetupIgnoreEntParams` calls were still unresolved. See [run 40945866308](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40945866308).

## This pass

Extended `tools/iw3_android/prepare_real_engine_mover_trace_services.py` to extract the original `SV_SetupIgnoreEntParams` and `SV_Trace` bodies from `third_party/KisakCOD/src/server/sv_world.cpp`, preserving them verbatim and recording source/body SHA-256 values.

The generator verifies the upstream declaration of `SV_GentityNum(int)` in `server/sv_game.h`, but deliberately does not include Windows-heavy `server/server.h`. The declaration remains an external dependency; no implementation or stub is supplied.

The ARM64 audit now requires the relocatable object to define `SV_SetupIgnoreEntParams` and `SV_Trace`, resolving the corresponding direct calls from `G_TraceCapsule`. It also requires genuine collision-world dependencies to remain visible and unresolved: `SV_GentityNum`, `CM_BoxTrace`, `CM_PointTraceToEntities`, and `CM_ClipMoveToEntities`. This is intentional evidence of the next boundary, not a claim of a complete server runtime.

Focused Python regressions compare extracted function bodies against the original source, verify hashes, preserve source files byte-for-byte, and check the original collision call sequence.

## Validation status and correction

The first ARM64 attempt exposed seven compile errors: the extracted `SV_Trace` body uses `Vec3Sub`, `Vec3Scale`, and `Vec3Add`, which were not declared by the narrower audit include set. The source body itself was not changed. Added the authentic `universal/com_math.h` header to the generated translation unit and a regression that protects that include.

The gate is triggered by changes to the extractor, focused regression, workflow, and original server-world declarations/source. The retry passed on code commit `969b73274638da59496f25e07cfd49960d82ade5`: [run 40947714537](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40947714537). The focused suite reported 14 tests, OK; the Android NDK compiled both original objects as ELF64/AArch64 and the relocatable link passed. The artifact is [12928804510](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40947714537/artifacts/12928804510), containing generated source, SHA-256 reports, objects and symbol listings — not an APK.

Verified marker from run 40947714537:

`IW3_ORIGINAL_SV_TRACE_AARCH64_EDGE_RESOLVED_GREEN`

The final symbol report confirms the expected world boundary remains unresolved: `SV_GentityNum(int)`, `CM_BoxTrace(...)`, `CM_PointTraceToEntities(...)`, and `CM_ClipMoveToEntities(...)`. This is the correct result for this narrow audit; those are not hidden by stubs.

The report must continue to state:

- `IW3_SV_TRACE_RUNTIME_EXECUTED=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

## Remaining work

The extracted `SV_Trace` is not linked into the Android runtime. Its collision-world graph still needs the authentic `SV_GentityNum`/server entity state and Collision Map (CM) implementations, including map-backed trace data. After that, the original server/client bootstrap, authentic IWD/FastFile/map loading, portable original renderer, touch-to-live-client command path, and observed physical ARM64 gameplay remain required. PR #4 must stay open and unmerged.
