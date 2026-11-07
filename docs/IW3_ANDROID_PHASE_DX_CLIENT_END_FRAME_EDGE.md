# Android ARM64 pass DX — original ClientEndFrame frame edge

Date: 2026-10-30

## Starting point

The preceding native source workflow [41053424641](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41053424641) passed the original `common.cpp` ARM64 object, full `G_RunFrame` archive, player/trigger/entity/mover providers and weapon loader. Its dependency report still showed `ClientEndFrame(gentity_s*)` unresolved from the original `G_RunFrameForEntity` dispatcher.

## Implementation

Added `tools/iw3_android/prepare_real_engine_client_end_frame.py`.

The generator extracts the exact `ClientEndFrame(gentity_s *ent)` function body from vendored `third_party/KisakCOD/src/game/g_active.cpp` using the existing brace-aware original-source extractor. It verifies the body and all required declarations against the original headers:

- `g_local.h`: `ClientEndFrame`, `P_DamageFeedback`, `G_PlayerStateToEntityStateExtrapolate`, `G_UpdateGroundTilt`, `G_SetPlayerFixedLink`;
- `sentient.h`: `Sentient_UpdateActualChainPos`;
- `turret.h`: `turret_think_client`;
- `player_use.h`: `Player_UpdateCursorHints`, `Player_UpdateLookAtEntity`;
- `g_main.h`: the external `level_locals_t level` declaration.

The generated TU includes the original state and service headers. The `level` declaration is repeated only as an ABI declaration after being verified against `g_main.h`; no service body or gameplay stub is added. The generator refuses to overwrite the vendored source and records source/body/generated SHA-256 hashes.

The native workflow stages this source, compiles it with Android NDK for `arm64-v8a`, checks ELF64/AArch64, and performs a relocatable link with the previously audited original SP frame, player, trigger, entity, mover and mover-team objects. It requires the `G_RunFrameForEntity -> ClientEndFrame` symbol edge to resolve while keeping real script/actor/path services visible as unresolved.

## Regression tests

Added `tests/test_iw3_android_client_end_frame.py` for verbatim extraction, declaration verification, source immutability, output hashes, required original call sites, and refusal to overwrite/missing-source behavior.

## Verification boundary

This is a compile + relocatable-link milestone only. It does not execute `ClientEndFrame`, link the full Android SP runtime, load a BSP, present a renderer frame, or prove touch-driven gameplay. The Android renderer backend remains unported from the original D3D9 path. JNI artifacts remain diagnostic and are not game APKs.

The follow-up CI run on the resulting commit is the authority for the ARM64 compile/link result. PR #4 remains open and unmerged.
