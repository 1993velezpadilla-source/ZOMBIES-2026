# IW3 Android ARM64 — phase DB: original mover-team physics chain

Date: 2026-10-29

## Baseline and previous verified work

Phase DA corrected 32-bit actor record assumptions in the original SP code. The NDK workflow passed at code commit `f19afcb774a3dbf6cb596d02e4ce3c388f345d0e`: 284 Python tests passed, and the extracted `SentientInfo_Clear` and `Actor_IsKnownEnemyInRegion` functions compiled as ELF64/AArch64. See [run 40941538057](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941538057).

The first mover-team pass corrected the hard-coded `pushed[1024]` tracking size and proved the `G_RunMover -> G_MoverTeam` edge. The initial compile exposed the missing narrow `entityHandlers` declaration; adding the exact upstream `extern` from `g_main.h` fixed that compile issue without defining a stub.

## This iteration: actual mover-push body

The next genuine dependency was `G_MoverPush`, called by `G_MoverTeam`. The audit generator now extracts these original bodies from `g_mover.cpp` verbatim:

- `G_TestEntityPosition`
- `G_CreateRotationMatrix`
- `G_TransposeMatrix`
- `G_RotatePoint`
- `G_TryPushingEntity`
- `G_MoverPush`
- `G_MoverTeam`

The extracted `pushed_t` structure, `pushed[1024]` array, and `pushed_p` cursor remain the original definitions, with a compile-time size assertion for 0x2C on 32-bit and 0x30 on 64-bit. `TRACK_g_mover` uses `sizeof(pushed)` instead of a Win32-only constant.

The ARM64 step recompiles this complete mover physics slice and links it with the prior relocatable frame object. It requires `G_MoverTeam` and `G_MoverPush` to be defined and absent from the undefined-symbol table. Collision/world services are deliberately left external; no gameplay stubs are introduced.

## Validation status for this iteration

The new step must emit `IW3_ORIGINAL_G_MOVER_TEAM_PHYSICS_CHAIN_AARCH64_FRAME_EDGE_RESOLVED_GREEN`. Until the run completes, do not count the expanded physics chain as validated. The source audit and generated object are not runtime integration.

## Still pending

`G_TraceCapsule`, `Trace_GetEntityHitId`, `G_Damage`, `CM_AreaEntities`, `G_RunMissile`, `G_RunItem`, `ClientEndFrame`, scripting, renderer, authentic FastFile/map loading, and live touch-to-client simulation remain incomplete. Emulator JNI logs are not evidence of a playable ARM64 game. Keep PR #4 open and unmerged.
