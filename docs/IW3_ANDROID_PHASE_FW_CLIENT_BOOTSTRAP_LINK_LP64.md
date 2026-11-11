# IW3 Android Phase FW — authentic SP client LP64 and Com_Init/CL_InitRenderer link

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`.
PR: https://github.com/1993velezpadilla-source/ZOMBIES-2026/pull/4

## Baseline and actual failure

The preceding FV commit `923e33e0` passed all 17 commit-associated workflows, but only exercised client static memory tracking, not a full ARM64 client translation unit. The authentic `Com_Init` still had an unresolved `CL_InitRenderer` entry point in the partial bootstrap link. Full `client/cl_main.cpp` compilation was not yet proven.

The first new full-client Android NDK CI audit (run 41230295914) failed on the original `gfx_d3d/r_cinematic.h` inclusion of unavailable Windows `d3d9.h`. This is an actual platform header barrier, not evidence of a missing function implementation.

## Changes made to the real KisakCOD engine

* `third_party/KisakCOD/src/client/cl_main.cpp`: `CL_ResetSkeletonCache` now aligns the full `uintptr_t` skeleton-memory address instead of truncating it through `unsigned int`. `CL_ClearState` iterates the actual `MAX_CONFIGSTRINGS` array with native typed pointers rather than comparing two unrelated member addresses cast to 32-bit `int`. The 19-entry arcade-score registration loop likewise uses typed one-past-end pointer comparison.
* `android/iw3-native/common_compat/gfx_d3d/r_cinematic.h`: Android **compile-only declarations** of the three *original* cinematic entry points referenced by `cl_main.cpp`, with the upstream function signatures. There are **no definitions, no replacement renderer, and no fake cinematic runtime**; these symbols still require real backend implementations.
* `tests/test_iw3_android_client_pointer_width.py`: extracts and executes the verbatim original `CL_ResetSkeletonCache`, `CL_ClearState` and arcade registration loop in a 64-bit ASan/UBSan fixture with boundary entries, pointer alignment, wraparound, canaries, and complete 19-entry registration. The fixture uses test-only engine service callbacks, not gameplay.
* `.github/workflows/iw3-client-static-tracking-host.yml`: runs the new regression with existing client tests.
* `.github/workflows/iw3-client-full-arm64.yml`: compiles the **complete** original `client/cl_main.cpp` with pinned Android NDK 27.2.12479018, inspects ELF64/AArch64 symbols, compiles the complete original `qcommon/common.cpp`, and performs an AArch64 relocatable link between the two original objects. No symbol stubs are supplied.

## Verified CI evidence

* **Host regression GREEN**: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41230318342 — **19/19 Python tests**, including the new original-client LP64 ASan/UBSan fixture. Initial run 41230260620 exposed a test-fixture-only MSVC `__int16` alias omission; it was fixed before the passing run.
* **Full original client AArch64 object GREEN**: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41230390611 — `CL_InitRenderer()` and `CL_Init(int)` defined in the genuine AArch64 client object; `R_BeginRegistration(vidConfig_t*)` remains undefined.
* **Original Com_Init + client relocatable link GREEN**: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41230497981 — `Com_Init(char*)` and `CL_InitRenderer()` are both defined in the combined original AArch64 ELF object; `CL_InitRenderer()` no longer unresolved in this pair. `R_BeginRegistration(vidConfig_t*)` remains unresolved. This is a `ld.lld -r` object link, **not** an executable or runtime proof.

Source commits: `aeffc618` (real engine), `2ebf37f1` (test), `3697492a` (test CI), `b9b6aee7` (full client CI), `89c899ad` (fixture repair), `ae4dd6df` (declaration-only cinematic header), `08263a6f` (genuine bootstrap-client relocatable link).

## Hard gates still open

1. Link a real renderer backend providing `R_BeginRegistration`, genuine material/font registration, and a drawable Android surface; no Direct3D or cinematic stubs may count as runtime.
2. Integrate the other authentic engine services (`Cmd_Init`, `FS_InitFilesystem`, thread contexts, server/game and map asset loaders) into a loadable Android process and execute `Com_Init` on ARM64.
3. Load a real map, render a real frame, consume actual touch input in the engine's client command loop, and demonstrate weapon/actor gameplay on device, with logcat/video/test evidence.
4. Validate real map/weapon assets and the original engine's data/license requirements independently.

`IW3_PLAYABLE_APK=false`. The JNI APK is still diagnostic only. PR #4 must remain open and unmerged. No Godot or substitute engine was used.
