# Phase CY — resolve the original SP mover dispatch edge for Android ARM64

Baseline reviewed: PR #4, branch `feature/iw3-native-android-arm64-20261025`, code head `141f613a8518163e1fdf247b9dbd1c16f9080bce` (29 Oct 2026).

## What the last CI actually proved

The source ARM64 audit, JNI diagnostic build, emulator probe, and Windows SP Killhouse smoke all completed successfully at the baseline. Their evidence is deliberately scoped: the Android emulator is x86_64, the JNI package is diagnostic, and no Android map/render/gameplay or physical ARM64 execution was proven.

The original `G_RunFrameForEntity` body dispatches missile, item, and mover entities. The combined AArch64 relocatable object still reported all three engine handlers as undefined. This pass takes the next small source-level step for the mover path only.

## Change in this pass

- Added `tools/iw3_android/prepare_real_engine_g_run_mover.py`, which extracts the original `G_RunMover(gentity_s*)` body verbatim from `third_party/KisakCOD/src/game/g_mover.cpp`.
- The generator hashes the source and extracted body, verifies the original `G_MoverTeam` definition exists, and refuses to overwrite the vendored source.
- Extended `.github/workflows/iw3-original-native-android.yml` to compile the extracted mover body with the Android NDK, inspect its ELF64/AArch64 header, and relocatably link it with the existing original frame/player/trigger/entity objects.
- The gate must show `G_RunMover(gentity_s*)` defined and absent from the combined undefined-symbol list. `G_MoverTeam` and other genuine engine services remain visible as unresolved; no no-op gameplay providers are introduced.
- Added `tests/test_iw3_android_g_run_mover.py` for provenance, required original call sites, no-stub policy, and workflow contract.

## Evidence boundary

This closes only the **compile/link edge for the original mover handler** if the new CI gate passes. It does not invoke the handler or close its internal service graph. Missile and item dispatch, script/client/actor services, filesystem startup, licensed FastFile/map loading, the original renderer, touch-to-live-client-frame integration, and physical ARM64 gameplay remain open. The generated object/report is not an APK. Keep PR #4 open and unmerged; `IW3_PLAYABLE_APK=false`.


## Follow-up — fix the actual ARM64 compile failure

The first NDK attempt at the new mover edge failed before compilation of the function body. The generated translation unit included broad `sv_game.h`, `sv_public.h`, `g_main.h` and actor headers, which pulled in Win32-only declarations from `server.h`: `__declspec(align(4))` and `_iobuf`. The failure was not a gameplay symbol-link failure.

The generator now uses the narrower original `game_public.h` and `g_local.h` type surface and explicitly declares only the external services needed by the preserved body (`G_MoverTeam` and `SV_LinkEntity`). This avoids altering vendored KisakCOD headers or erasing layout semantics with a blanket `__declspec` macro. A regression test rejects reintroduction of those broad headers.

The fix is **pending CI validation**. The previous ARM64 run `40919978630` failed at step 23 with the header errors above; do not treat that run as proof that the mover edge compiles. Runtime, map loading, rendering, and gameplay remain unproven; `IW3_PLAYABLE_APK=false`.
