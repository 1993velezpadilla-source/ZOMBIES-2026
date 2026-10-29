# IW3 Android ARM64 — phase DC: close the mover trace helper edge

Date: 2026-10-29

## Baseline

Phase DB expanded the authentic SP mover physics slice to include \`G_TestEntityPosition\`, rotation helpers, \`G_TryPushingEntity\`, \`G_MoverPush\`, and \`G_MoverTeam\`. The verified audit resolved \`G_RunMover -> G_MoverTeam\` and \`G_MoverTeam -> G_MoverPush\`, while leaving world collision services unresolved. See [run 40943454198](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40943454198).

## This pass

The next direct dependency from the original \`G_TestEntityPosition\` body was the collision-query wrapper \`G_TraceCapsule\` and the hit-ID utility \`Trace_GetEntityHitId\`.

Added \`tools/iw3_android/prepare_real_engine_mover_trace_services.py\`. It extracts these original bodies verbatim from:

- \`third_party/KisakCOD/src/game/g_main.cpp\`: \`G_TraceCapsule\`
- \`third_party/KisakCOD/src/qcommon/cm_trace.cpp\`: \`Trace_GetEntityHitId\`

The generator hashes both upstream files and both extracted function bodies, verifies the original \`SV_SetupIgnoreEntParams\` / \`SV_Trace\` declarations in \`server/sv_world.h\` and the trace ABI in \`qcommon/qcommon.h\`, and refuses to overwrite upstream files.

The new \`iw3-mover-trace-services-arm64\` workflow compiles the authentic mover physics slice and the two original trace functions with the Android NDK, then performs a relocatable AArch64 link. The gate requires \`G_TestEntityPosition -> G_TraceCapsule\` and \`G_TestEntityPosition -> Trace_GetEntityHitId\` to resolve. It also checks that the real \`SV_SetupIgnoreEntParams\` and \`SV_Trace\` services remain visible as unresolved dependencies; it adds no no-op callbacks or replacement collision logic.

## Evidence boundary

This is an ELF64/AArch64 compile/link audit, not a live runtime component. \`SV_Trace\` is not linked, the Android Activity does not invoke the original SP frame, no authentic map is loaded by this path, and no gameplay or playable APK is claimed.

Expected success marker for this narrow gate:

\`IW3_ORIGINAL_MOVER_TRACE_EDGE_AARCH64_RESOLVED_GREEN\`

The workflow explicitly reports:

- \`IW3_MOVER_TRACE_RUNTIME_EXECUTED=false\`
- \`IW3_REAL_MAP_LOADED=false\`
- \`IW3_GAMEPLAY_PROVEN=false\`
- \`IW3_PLAYABLE_APK=false\`

## Remaining work

The next runtime blockers include the actual \`SV_Trace\`/collision-world graph, \`G_Damage\`, \`CM_AreaEntities\`, missile/item frame handlers, \`ClientEndFrame\`, script and actor services, authentic FastFile/map loading, the original renderer, and live touch-to-client simulation. Physical ARM64 gameplay remains unproven. Keep PR #4 open and unmerged.
