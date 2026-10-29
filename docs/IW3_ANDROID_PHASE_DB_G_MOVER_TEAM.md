# IW3 Android ARM64 — phase DB: original mover-team edge

Date: 2026-10-29

## Baseline and previous verified work

Phase DA corrected 32-bit actor record assumptions in the original SP code. The NDK workflow passed at code commit `f19afcb774a3dbf6cb596d02e4ce3c388f345d0e`: 284 Python tests passed, and the extracted `SentientInfo_Clear` and `Actor_IsKnownEnemyInRegion` functions compiled as ELF64/AArch64. See [run 40941538057](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941538057). The JNI and preflight checks passed, but the JNI artifact is diagnostic-only.

## Next blocker and source correction

The previous frame audit showed `G_RunMover(gentity_s*)` defined while `G_MoverTeam(gentity_s*)` remained an unresolved original dependency. The authentic `g_mover.cpp` also passed a hard-coded 45,056-byte size to the static allocation tracker for `pushed[1024]`; that is the 32-bit size (1024 × 44 bytes) and undercounts the native 64-bit array (1024 × 48 bytes).

This phase:
- Changes `TRACK_g_mover` to use `sizeof(pushed)`, preserving the exact 45,056-byte result on 32-bit while reporting the native 64-bit size correctly.
- Extracts the original `pushed_t` struct, its single `pushed[1024]` array and cursor, and the original `G_MoverTeam` body.
- Adds a compile-time layout assertion for `pushed_t`: 0x2C on 32-bit and 0x30 on 64-bit.
- Compiles the provider with the SP actor/sentient invalidation paths enabled, then links it with the existing relocatable frame object to verify that the `G_RunMover -> G_MoverTeam` edge resolves.

No `G_MoverPush` stub is added. Its original body and other world/simulation services remain unresolved and visible in the audit. The provider is not added to the Android runtime.

## Required evidence

The new CI step must emit `IW3_ORIGINAL_G_MOVER_TEAM_AARCH64_FRAME_EDGE_RESOLVED_GREEN`, verify ELF64/AArch64, and show `G_MoverTeam` defined but not undefined in the combined object. It must continue to report `IW3_G_MOVER_TEAM_RUNTIME_EXECUTED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, and `IW3_PLAYABLE_APK=false`.

## Remaining blockers

`G_MoverPush`, `G_RunMissile`, `G_RunItem`, `ClientEndFrame`, scripting, actor/client integration, renderer, authentic FastFile/map loading, and live touch-to-client simulation remain incomplete. Emulator JNI logs are not evidence of a playable ARM64 game. Keep PR #4 open and unmerged.
