# Phase FN — authentic q_shared thread initialization linked to Android ARM64 (NOT GAME)

Date: 2026-10-31 UTC. PR #4, `feature/iw3-native-android-arm64-20261025`. No Godot or substitute engine.

## Baseline and actual portability failure

Previous Phase FM linked complete original `qcommon/common.cpp`, `qcommon/cmd.cpp`, `universal/dvar.cpp` and `universal/com_files.cpp` to an Android ARM64 `Sys_GetValue` provider. But `Com_InitThreadData(int)`, required by original Windows `Sys_InitMainThread`, was not yet present. The genuine definition lives in `third_party/KisakCOD/src/universal/q_shared.cpp`, and sets original thread slots 1 (`va_info`), 2 (`g_com_error`/`jmp_buf`) and 3 (`g_traceThreadInfo`).

The first new full-TU compile attempt **failed**, correctly, in GitHub Actions [41186828150](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41186828150) because Android Bionic does not declare MSVC `_vsnprintf` at three original call sites (lines near 144, 523, 540). It also exposed existing pointer-narrowing warnings in the original configuration parser.

## Changes made on original code and Android platform boundary

- In the **authentic** `universal/q_shared.cpp`, added an Android-only `_vsnprintf` → C99 `vsnprintf` compatibility mapping. Since C99 returns the required length on truncation, changed `Com_sprintfPos`'s Android-only truncation handling to reject every result `len >= destModSize`, not merely equality; Windows keeps its previous branch.
- Extended `.github/workflows/iw3-command-full-arm64.yml` to compile the **entire original** `universal/q_shared.cpp` as an AArch64 ELF object, link it relocatably with the four complete original bootstrap units and the Android thread-value provider, and require original `Com_InitThreadData(int)`, `va_info`, and `g_com_error` symbols.
- Added `android/iw3-native/iw3_android_main_thread_shared.cpp` with `IW3_AndroidBindMainThreadSharedData()`, which binds original `THREAD_CONTEXT_MAIN`, **calls original** `Com_InitThreadData(THREAD_CONTEXT_MAIN)`, and checks the error-jump slot. This narrow OS adapter is not `Sys_InitMainThread`: it does not initialize slot 0/profile state, launch threads, or invoke `Com_Init`. It must not be used as a fake bootstrap.
- Added `tests/test_iw3_android_cmd_main_shared.py`: host-executes the verbatim original `Com_InitThreadData` body and original type declarations against the actual Android thread-value provider, validates slots 1/2/3, checks slot 0 remains unset, and executes `setjmp`/`longjmp` under UBSan.
- Added `tests/test_iw3_android_cmd_qshared_formatter.py`: extracts and host-executes the original `Com_sprintfPos` body with C99 formatter semantics under UBSan, checking truncation, exact-fit and append behavior.
- Retained `IW3_PLAYABLE_APK=false` and uploaded the ELF objects and defined/undefined symbol reports as **NOT-APK** evidence.

## Verified results

Latest complete gate: [GitHub Actions 41187119558](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41187119558), job **124496186361**, code commit **be4aba3a**, completed successfully on 2026-10-31. Inspected logs show **27 Python tests passed**, including the two executable host regressions, and the complete `q_shared.cpp` AArch64 object plus main-thread adapter linked relocatably with original `Com_Init`, command, dvar and filesystem units. Verified log markers: `IW3_ANDROID_MAIN_SHARED_DATA_ORIGINAL_OWNER_LINK_PASS`, `IW3_ORIGINAL_COM_INITTHREADDATA_AARCH64_PROVIDER_RESOLVED`, `IW3_ORIGINAL_RENDERER_RUNTIME_PROVIDER_MISSING`, and `IW3_PLAYABLE_APK=false`.

Artifact **13036664203** (`iw3-original-command-full-aarch64-NOT-APK`) includes the combined AArch64 ELF and symbol reports. This is **not** an installable or playable Android package.

## Exact remaining blockers

1. The original `Com_Init` has **not** run in an Android process. The Android MAIN binding is a narrow platform service; original profile/thread startup, OS services and other dependencies are not linked as a runnable engine.
2. `CL_InitRenderer()` remains an unresolved original renderer dependency. No real GPU frame has been shown.
3. The full `q_shared.cpp` compile exposed additional genuine LP64 hazards in `ParseConfigStringToStructCustomSize`: pointer values for `FX_Register`, `R_RegisterModel`, `Material_RegisterHandle` and `Com_FindSoundAlias` are written through 32-bit integer slots. Before changing those sites, verify the destination `cspField_t::iOffset` against the target pointer-bearing struct layouts and add host/ARM64 regression tests. Do not silence warnings or treat pointer truncation as solved.
4. Genuine FastFile/map loading, touch input delivered into the original client, actor/weapon gameplay, and ARM64 runtime evidence remain unproven.

Hard gates: `IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`. Keep PR #4 open and unmerged.
