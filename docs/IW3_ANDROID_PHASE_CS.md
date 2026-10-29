# Phase CS — original aim-assist tweakable edges for Android ARM64

## Baseline

Inspected PR #4 at branch head `29f7d50ef93abf17e2d3bb0489ba0fc40c637ef9` on 2026-10-29. The native ARM64 audit and x86_64 emulator diagnostic were green, but the combined original client-input object still had five explicitly tracked unresolved dependencies from `AimAssist_UpdateMouseInput`: `AimAssist_UpdateTweakables`, `AimAssist_UpdateAdsLerp`, `AimAssist_ApplyAutoMelee`, `AimAssist_ApplyMeleeCharge`, and `MyAssertHandler`.

## Change

Added `tools/iw3_android/prepare_real_engine_aimassist_tweakable_providers.py`. It extracts the exact original bodies of `AimAssist_UpdateTweakables` and `AimAssist_UpdateAdsLerp` from `third_party/KisakCOD/src/aim_assist/aim_assist.cpp`, checks their required expressions, and stages the eight original null-initialized dvar pointer definitions used by the tweakable calculation. It hashes the upstream source, refuses to overwrite it, and writes a separate report.

The ARM64 workflow compiles the generated source with the Android NDK, combines it relocatably with the already-audited original input and CGame state objects, and requires both helper symbols to be defined and absent from the combined undefined-symbol list. It continues to require the original auto-melee, melee-charge, assertion, and screen-placement services to remain visible as unresolved. No stubs are introduced.

## Evidence boundary

This closes two original code dependency edges only. The extracted dvar pointers remain null-initialized and the original dvar registration and CGame initialization have not been invoked. The combined object is an audit artifact, not part of the JNI diagnostic APK. It does not load licensed FastFiles/maps, initialize the renderer, run a live client frame, or prove gameplay.

The workflow must emit `IW3_ORIGINAL_AIMASSIST_TWEAKABLES_EDGE_RESOLVED_AARCH64_GREEN` only after the new compile and symbol checks pass. `IW3_CLIENT_RUNTIME_LINKED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, and `IW3_PLAYABLE_APK=false` remain mandatory.

PR #4 must stay open and unmerged until the original runtime, map, renderer, touch-driven client frames, combat, and physical ARM64 execution are demonstrated. CI results will be appended after the new workflow completes.
