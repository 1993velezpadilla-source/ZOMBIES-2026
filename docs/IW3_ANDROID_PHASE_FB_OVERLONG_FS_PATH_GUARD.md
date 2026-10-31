# Phase FB — authentic KisakCOD IWD/localized path underflow guard

Date: 2026-10-30 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

**NOT A GAME. No original IW3 Android ARM64 playable APK, renderer, map or live gameplay has been demonstrated. PR remains open and must not merge to main.**

## Baseline inspected before editing

Head `fc748c93b37174002fef45eaae5b9b2ce1cb5300` completed native original-source [run 41120045130](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41120045130) SUCCESS: 430 Python regressions, 26 native host CTests, AArch64 compilation/link audit. This is source/host evidence only. Emulator diagnostic [run 41120045141](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41120045141) failed installing an Intel x86_64 SDK image before engine execution.

## Next original-engine portability blocker

The original `universal/com_files.cpp` has two decompiler-era expressions equivalent to `ospath[strlen(ospath) - 1] = 0` in the real `FS_AddIwdFilesForGameDirectory` and `FS_AddGameDirectory` localized path. `FS_BuildOSPath` now fails closed by clearing `ospath` when the absolute Android app-private root exceeds the engine's 256-byte boundary. If a platform error handler returns, the old expression writes to `ospath[-1]` before `Sys_ListFiles` / `Sys_DirectoryHasContents` can reject the invalid directory. That is a concrete native memory-corruption boundary, not a rendering or gameplay fix.

## Changes

- [5daac625](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/5daac625339f628e7ab21660def29c1dd805e473): update the two authentic KisakCOD function bodies to require at least two path characters and a final slash/backslash before removing the trailing separator. Empty, malformed and overlong paths now return before directory enumeration, probing or invalid writes. No substitute FS implementation.
- [75e1bf53](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/75e1bf53b3107d54daf13e9322066b1060ddd2d3): native host test executes the original `FS_AddGameDirectory` with a 301-character absolute root; its error handler intentionally returns and verifies no directory probe, IWD scan or searchpath registration occurs.
- [caa445f9](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/caa445f96b57d6b7a6ae6bb8f24c65ae1603f976) and [c0d8cfcb](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c0d8cfcb1d2bab816e9bb31a67eda0f18bae7a92): Python regression verifies guards in both authentic bodies and the host test's fail-closed assertions.

## CI and evidence boundary

New source CI on head `c0d8cfcb1d2bab816e9bb31a67eda0f18bae7a92` started at the time of this report; [native original-source run 41128994154](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41128994154) is **PENDING**. The new source change is **not** declared green until the CI job completes and the native host regression passes. Other queued jobs are diagnostic or source-only, never gameplay.

The IWD directory guard is source-asserted, not yet executed as the real Android `FS_AddIwdFilesForGameDirectory` with actual archives. The native host test executes the original localized-directory body with platform spies; it is not a device test. Two other decompiler-era trailing-separator expressions remain in `FS_SV_FOpenFileRead` and related server-file paths; audit these separately before treating the full FS TU as runtime-safe.

Release gates remain false: `IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.

## Next

Inspect the native source CI and correct failures. Then integrate the real `Cmd_Init`, `Dvar_Init` and `FS_Startup` into a live Android ARM64 process with an app-private root, verify real IWD reads, and only then proceed to real FastFile/BSP, renderer, client touch and game simulation.
