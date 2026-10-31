# Phase CR — original client aim-assist and predicted-state edges for ARM64

## Baseline inspected (2026-10-29)

The current branch head was `523e99935e04de21da40d61da7d22d4c8a566829`. CI had passed the source preflight, original-source ARM64 audit, JNI diagnostic build, x86_64 Android emulator diagnostic, and Windows SP smoke. The logs still explicitly showed `AimAssist_UpdateMouseInput` and `CG_GetPredictedPlayerState` as unresolved in the original client input object. The diagnostic APK does not link or execute the live client command loop.

## Concrete change

Added `tools/iw3_android/prepare_real_engine_client_state_providers.py`. It extracts the exact original function bodies from:

- `third_party/KisakCOD/src/aim_assist/aim_assist.cpp`: `AimAssist_UpdateMouseInput`
- `third_party/KisakCOD/src/cgame/cg_main.cpp`: `CG_GetPredictedPlayerState`

It also stages the exact original state definitions `aaGlobArray[1]` and `cgArray[1]` required by those functions. The generator hashes both source files and both function bodies, checks the required call/return markers, and refuses to overwrite the vendored source. No function stubs are generated.

The ARM64 workflow compiles the generated source with the Android NDK and relocatably combines it with the existing original client input/touch/keyboard object. The gate requires the two original provider symbols to be defined and absent from the combined undefined-symbol list. It deliberately leaves the real downstream aim-assist helpers and assertion handler visible as unresolved dependencies.

## Evidence boundary

This is a native object-level dependency-edge audit, not runtime integration. It does not initialize the original CGame or aim-assist state, invoke `CL_CreateCmd` in the Android app, mount real FastFiles, load a map, render a scene, or prove weapon/actor gameplay. The generated artifact is explicitly **NOT APK**. The workflow emits:

- `IW3_ORIGINAL_CLIENT_AIMASSIST_AND_PREDICTED_STATE_EDGE_RESOLVED_AARCH64_GREEN`
- `IW3_CLIENT_STATE_RUNTIME_INITIALIZED=false`
- `IW3_CLIENT_RUNTIME_LINKED=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

Keep PR #4 open and unmerged until the actual engine runtime, map, renderer, touch-driven client frames, combat, and physical ARM64 execution are demonstrated.


## Follow-up correction after the first ARM64 compile

The first run for this phase failed before the provider object could be built. Including the real CGame state headers exposed eight legacy assertions that hard-coded Win32 sizes for pointer-bearing renderer structures: `FxEffectDef`, `FxImpactTable`, `GfxImage`, `GfxWorldDpvsStatic`, `GfxPixelShaderLoadDef`, `MaterialPixelShaderProgram`, `MaterialTechniqueSet`, and `Material`. The compiler reported the corresponding native LP64 sizes as 40, 16, 48, 168, 16, 24, 296, and 104 bytes.

Changed those assertions to validate both the original 32-bit layout and the observed native 64-bit layout. This does not port the D3D renderer or establish FastFile serialization compatibility; it allows the authentic CGame headers to be compiled on LP64 while preserving a strict size assertion for each ABI. Added regression tests for all eight dual-width assertions. The follow-up ARM64 compile must still pass before this phase is considered validated.
