# IW3 Android ARM64 — phase DA: native-width actor record fixes

Date: 2026-10-29

## Baseline inspected

Reviewed PR #4 at branch head `ab8fa0c5db7f9399ffbd3094e604574d1b52bf26`, the branch Actions runs, and the full native ARM64 job log. The preflight, JNI diagnostic, emulator diagnostic, Windows SP smoke, and source audit all passed on that head. The native ARM64 log confirms `G_RunMover` is defined in the relocatable SP-frame object, while `G_MoverTeam`, `G_RunMissile`, `G_RunItem`, `ClientEndFrame`, scripting, and renderer services remain unresolved. The run explicitly reports no runtime, no map, and no playable APK.

## Portability blocker found

The next SP actor dependency cannot be integrated safely while the original `actor.cpp` retains 32-bit record assumptions:

- `SentientInfo_Clear` clears ten 4-byte words (40 bytes), which is only the Win32 size of `sentient_info_t`; on ARM64 the record contains an 8-byte pathnode pointer and occupies 48 bytes.
- `Actor_IsKnownEnemyInRegion` walks the `sentientInfo` array with `i += 10` and reads the timestamp at a fixed word offset before the position vector. Both assume a 40-byte record.
- `SP_actor` copies `actor_goal_s` through seven 4-byte writes, truncating its two pointer-bearing fields on a 64-bit layout.
- The actor layout assertions in `actor.h` hard-code the 32-bit executable's actor size and `sentientInfo` offset.

## Changes to authentic KisakCOD source

- `SentientInfo_Clear` now clears `sizeof(*pInfo)` using the complete native-width record.
- `Actor_IsKnownEnemyInRegion` indexes `self->sentientInfo[v9]` and reads `lastKnownPosTime` and `vLastKnownPos` by typed fields rather than fixed byte strides.
- `SP_actor` assigns `codeGoal = scriptGoal`, copying all declared fields including full-width pointers.
- The CoD3SP fixed-size/offset assertions are conditional on a 32-bit pointer ABI. The `sentient_info_t` assertion now checks 40 bytes on 32-bit and 48 bytes on 64-bit.

These are source-level portability corrections, not a claim that every actor routine has been audited. The source-linked generator hashes and extracts the corrected original `SentientInfo_Clear` and `Actor_IsKnownEnemyInRegion` bodies for a genuine NDK ARM64 compile. No gameplay service stubs are added.

## Validation gates

The new workflow step must compile both extracted functions as ELF64/AArch64 and verify the expected symbols. The generated report keeps `runtime_executed=false`, `map_loaded=false`, `gameplay_proven=false`, and `playable_apk=false`. CI results for this revision must be inspected after the push; do not count a pending build as green.

## Still pending

The actor subsystem contains other legacy assumptions and requires a full native-width audit. `G_MoverTeam` is still a genuine unresolved provider for `G_RunMover`; the original `G_RunMissile`, `G_RunItem`, scripting, client, renderer, real IWD/FastFile/map loading, and touch-to-live-client integration are also not complete. No physical ARM64 gameplay has been demonstrated. Keep PR #4 open and unmerged.

## Follow-up from first ARM64 compile attempt

The first run on commit `0fa9130ca2f0537906535f3574de399ad7c44f8c` passed the Python source/regression gate and the preceding ARM64 frame checks, but the new actor compile step failed in the original `actor_physics.h`: Clang/NDK does not accept the MSVC-only `struct __declspec(align(4)) actor_physics_t` spelling. The failure was observed in Actions run [40941092623](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941092623), step 24.

This follow-up changes only that declaration to standard C++ `struct alignas(4) actor_physics_t`, which expresses the same four-byte alignment on MSVC and Clang. The generator and regression suite now require the portable declaration and reject reintroduction of the MSVC-only form.

## Validation outcome

On code commit `f19afcb774a3dbf6cb596d02e4ce3c388f345d0e`:
- The native ARM64 workflow passed in [run 40941538057](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941538057); the repeated PR-triggered run [40941545829](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941545829) also passed.
- The Python regression suite reported **284 tests, OK**.
- The new object is ELF64/AArch64 and defines `SentientInfo_Clear(sentient_info_t*)` and `Actor_IsKnownEnemyInRegion(actor_s const*, gentity_s const*, float const*, double)`; marker: `IW3_ORIGINAL_ACTOR_POINTER_WIDTH_AARCH64_COMPILE_GREEN`.
- Preflight passed in [run 40941545611](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941545611). JNI integration passed in [run 40941545904](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941545904), but that artifact remains diagnostic-only.
- The emulator runtime diagnostic and Windows SP/weapon checks were still running at the last inspection. None of those is evidence of a playable Android ARM64 game.

The original failure in [run 40941092623](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40941092623) is therefore resolved for the actor-pointer-width compile gate, not for the complete engine runtime.
