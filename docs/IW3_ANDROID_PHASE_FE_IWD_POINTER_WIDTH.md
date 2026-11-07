# Phase FE — original IW3 64-bit IWD reference pointers and FF capacity

Date: 2026-10-31 UTC (2026-10-30 Puerto Rico). PR #4 on `feature/iw3-native-android-arm64-20261025`.

**Not a game / no playable ARM64 APK.** No Godot, renderer substitute, mock engine runtime, or merge to `main`.

## Baseline inspected

Before edits, the original-source ARM64 CI at head `8eb5ca8a300761b8bf72fa1ab8e066c5613e083a` had completed SUCCESS ([run 41143545828](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41143545828)). The job log reported 437 Python tests and 26/26 CTest tests. This is source/host coverage, **not** Android runtime or gameplay.

## Actual original-engine defects

`third_party/KisakCOD/src/qcommon/files.cpp` contains the authentic `FS_PureServerSetLoadedIwds`. Its decompiled Win32 implementation used `Com_Memcpy(fs_serverIwdNames, s0, 4 * fs_numServerIwds)`. `fs_serverIwdNames` is an array of pointers. On Android ARM64 each pointer occupies 8 bytes; the Win32 byte count copied only half the pointer array, leaving later entries null/stale and making the pure-IWD list invalid. The original `fs_serverIwds` checksums remain 32-bit integers.

The same translation unit declared `fs_serverReferencedFFCheckSums[32]` and `fs_serverReferencedFFNames[32]` but called `FS_ServerSetReferencedFiles(..., 1024, ...)` from `FS_ServerSetReferencedFFs`. That permitted writes beyond the real FF arrays when more than 32 references were supplied.

## Corrections and tests

- [333b72e1](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/333b72e1eaeda3bbdf5a1766fdfd5a9adac5d4b5): use `sizeof(fs_serverIwdNames[0]) * fs_numServerIwds` for name pointers, and element-size arithmetic for checksum copy. Cap FF reference parsing to the actual 32-entry checksum array. Both changes are in **original KisakCOD functions**, not a substitute engine.
- [2ba0d7d0](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/2ba0d7d032d7def2e0d1fb67b6955c900b2b1a51): `tests/test_iw3_android_iwd_pointer_width.py` extracts both authentic function bodies, compiles them as a 64-bit host C++ executable with ASan/UBSan, verifies three IWD pointers and checksums, unchanged-list ownership, list replacement, and the FF 32-entry limit. Host-only command/audio/string stubs are **not** linked into Android JNI.
- [0ac84bdc](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/0ac84bdcd49c3482957c856a00b5bda731c496f6): focused sanitizer CI workflow.

## Evidence

Focused [run 41150951207](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41150951207) completed **SUCCESS**. Inspected job `124387070974`: `test_original_iwd_pointers_and_ff_capacity ... ok`, 1/1 test in 2.541 seconds. This proves the corrected authentic function bodies execute on a 64-bit **host**, with sanitizers; it does not prove an Android process has called them.

The updated full original-source ARM64 workflow [run 41150951143](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41150951143) was still pending at the time of this report. Do not call that run green until its final logs confirm it. The focused host sanitizer success is a separate, narrower result.

## Remaining release gates

`IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`
`IW3_FS_STARTUP_RUNTIME_INVOKED=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

Next priority: **link and invoke** authentic `Com_Init` / `Cmd_Init` / `Dvar_Init` / `FS_Startup` in a native Android ARM64 process with legally supplied IWD files. Verify actual filesystem mount/read, then genuine map/BSP/FastFile loading, renderer frame, original client touch consumption, and weapons/actors gameplay. Do not promote diagnostic JNI output as a playable game. Keep PR #4 open and unmerged.
