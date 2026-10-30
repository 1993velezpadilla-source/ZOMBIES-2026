# Phase FC — authentic IW3 server-file path guard on Android ARM64

Date: 2026-10-30 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

**NOT A GAME.** This is a concrete original-engine portability/safety correction. There is still no verified ARM64 KisakCOD APK that renders a real map and executes touch-driven gameplay. Do not merge this PR into main.

## Baseline inspected

Before editing, the PR head was `c92c069143dc0660b9e8ea3f5f8d5c87baa3111d`. All nine associated GitHub Actions workflows completed SUCCESS, including [native original-source run 41129061785](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41129061785). These are compilation/host/emulator diagnostic checks, **not** ARM64 gameplay proof.

## Concrete defect

In the authentic `third_party/KisakCOD/src/universal/com_files.cpp`, the original `FS_SV_FOpenFileRead`, `FS_SV_FOpenFileWrite` and `FS_SV_FileExists` functions stripped the final path separator with pointer arithmetic equivalent to `ospath[strlen(ospath) - 1] = 0` without checking for an empty buffer. The preceding `FS_BuildOSPath` intentionally clears the destination when a long Android app-private root exceeds the original 256-byte engine path limit. If the fatal error handler returns (as in focused tests), the old code writes to `ospath[-1]` and could proceed to filesystem I/O with an invalid path.

## Source changes

- `0e051a4e`: Add `FS_SV_BuildOSPath` to the original filesystem TU. It rejects null/empty roots or filenames, checks that the constructed path ends with a separator and has a valid length, removes exactly that separator, and fails closed on rejected/overlong paths. Route the three original server-file read/write/exists APIs through this helper. The read fallback skips invalid home/base/CD roots instead of opening an empty path; write and exists return failure without I/O.
- `b4d37f80`: Stage the helper verbatim in the existing original FS startup extraction for ARM64 and host verification.
- `21dafca6`, `bebbb218`: Execute the authentic helper from `fs_localized_path_native_test.cpp` for valid POSIX paths, backslash normalization, empty roots/names, and an overlong root with a returning error handler. Require `IW3_ORIGINAL_FS_SV_PATH_GUARD_PASS`.
- `e99c8903`, `8c532232`: Add Python source/host regression checks for all three real server-file call sites and the extraction.

## Verification

At documentation time the latest source/test head is `8c53223295067c26c226a202813a2da67d1e9bce`. Its [native source run 41133430736](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41133430736) is **pending**; do not count the new host tests as passed until its logs confirm. The previous baseline run passed, but did not contain this fix.

## Remaining runtime gates

`IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.

Next: inspect latest native CI and repair any regressions, then link and invoke original `Cmd_Init`, `Dvar_Init` and `FS_Startup` in a real Android ARM64 process using an app-private data root and genuine licensed IWD data. Map load, original renderer, client touch and gameplay remain separate release gates.
