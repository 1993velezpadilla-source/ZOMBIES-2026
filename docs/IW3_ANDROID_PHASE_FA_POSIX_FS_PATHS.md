# Phase FA — authentic IW3 Android filesystem POSIX path boundary

Date: 2026-10-30 UTC. PR #4, `feature/iw3-native-android-arm64-20261025`.

**NOT A GAME: no playable original-engine Android ARM64 APK. Keep PR open; do not merge main.**

## Baseline inspected

The PR head at the beginning of this pass was `995d6f5a078576f5ec6bef61bec4b0915f83873d`.
All nine PR-triggered CI runs for that head had completed SUCCESS, including
[full source ARM64 audit 41115451654](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41115451654),
[focused command/filesystem/Dvar link audit 41115451657](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41115451657),
and [JNI diagnostic 41115451846](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41115451846).
These are compilation/diagnostic results, **not** original engine runtime evidence.

## Actual portability blocker

The full original `third_party/KisakCOD/src/universal/com_files.cpp`
compiled on ARM64 but `FS_ReplaceSeparators()` unconditionally wrote Win32
backslashes (`92`). `FS_BuildOSPathForThread()` always calls this function.
Consequently a genuine Android root such as `/data/user/0/.../files` was
transformed into `\\data\\user\\0\\...\\files`, which cannot match
the POSIX rooted path checks in `Sys_DirectoryHasContents()` or be opened
as an absolute POSIX file path. The existing localized-path host regression
even expected backslashes, so it failed to detect this Android mismatch.
`FS_CreatePath()` likewise scanned only Win32 separators, preventing
intermediate directory creation for POSIX paths.

## Code changes

- [bf9d33b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/bf9d33b53444fbf48219450b387919d34cb3bf18):
  preserve Win32 separator behavior on Windows, select `/` for Android in
  the authentic `FS_ReplaceSeparators` and `FS_CreatePath` bodies. The
  `IW3_FS_POSIX_PATHS_TEST` macro is restricted to a host regression
  build to exercise the exact Android branch without fabricating an FS
  implementation.
- [0253e43](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/0253e437f37b3abad562a635f039681095d9d23b):
  update the native host test to require `/private/iw3/main/english`
  and normalized mixed-separator map paths.
- [3b8c561](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/3b8c561b97a6d7214c10f948020b0fc347151900):
  compile that test with the POSIX branch enabled.
- [f1e52d4](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f1e52d4ca98a77519b007b9e1aa405ce966bef7f)
  and [d5af3ec](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/d5af3ec846d3494c61123416276729c1d4857b04):
  add source and test-wiring regression assertions.

## Evidence and remaining gates

The prior head's nine CI results are green; **the new POSIX patch has not yet
been declared validated** until its own GitHub Actions tests complete. The
focused host test exercises original extracted `FS_BuildOSPath` and
`FS_Startup` bodies with platform service spies. It is **not** an Android
process, and does not prove actual IWD/map loading.

Release gates remain false:
`IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`;
`IW3_FS_STARTUP_RUNTIME_INVOKED=false`;
`IW3_REAL_MAP_LOADED=false`;
`IW3_RENDERER_FRAME_PROVEN=false`;
`IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`;
`IW3_GAMEPLAY_PROVEN=false`;
`IW3_PLAYABLE_APK=false`.

**Next concrete integration step:** run original `Cmd_Init`, `Dvar_Init`
and `FS_Startup` in a real ARM64 Android process using the app-private
root and actual engine searchpaths; verify genuine IWD reads before attempting
FastFile/BSP map loading, original rendering and live touch-driven
`CL_CreateCmd`/weapon/actor simulation. Do not substitute the JNI diagnostic.
