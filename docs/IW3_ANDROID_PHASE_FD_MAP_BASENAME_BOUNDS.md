# Phase FD — original IW3 map basename bounds on Android ARM64

Date: 2026-10-30 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

**NOT A GAME.** This pass addresses a real original-engine map-name parsing defect; it does not execute a map, render a frame or produce a playable Android APK. Do not merge this PR into `main`.

## Baseline checked

The prior head was `29799794b640fce055ae35b430e60363f8dfd2c0`. All nine associated CI workflows completed SUCCESS, including native original-source run [41133494719](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41133494719). These are source/host/diagnostic checks, not Android gameplay proof.

## Authentic source defect and fix

In `third_party/KisakCOD/src/qcommon/files.cpp`, `FS_GetMapBaseName` indexed `mapname[length - 3]` without checking the input length and copied an unchecked map basename into the original static `char basename[64]`. A short `bsp`-ending name could underflow the length (the original code subtracts seven bytes), while an overlong map identifier could overflow the 64-byte buffer. Both are relevant when processing map names from external game data, particularly on a 64-bit Android target.

- Commit `59cdc3a1`: keep the original IW3 map-name behavior for valid `maps/mp/` and `.d3dbsp` paths, including percent-to-underscore conversion; add minimum-length checks before suffix indexing/subtraction, reject names that cannot fit in `basename`, and fail closed rather than silently truncating a map identifier. Preserve the original function, its signature and static result buffer.
- Commit `2760f943`: add `tests/test_iw3_android_map_base_name.py`. The host test extracts the **actual updated original function body** verbatim, compiles it with C++17 and AddressSanitizer/UndefinedBehaviorSanitizer, and exercises valid paths, short/empty names, `bsp`-suffix underflow cases, exact 63-byte capacity, oversized names and case-insensitive extension/prefix handling.

## Evidence and limitations

The preceding native-source CI was green before these changes. The new head is `2760f9439a8f9e51182793de9518b71271d5d646`; its CI result must be inspected separately. The new test is a host extraction with stubbed string services; it does **not** establish that `qcommon/files.cpp` is linked into a live Android engine or that real BSP/FastFile loading works.

Release gates remain false: `IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.

## Next real integration gate

Link and invoke authentic `Com_Init`, `Cmd_Init`, `Dvar_Init` and `FS_Startup` in a native ARM64 process with an app-private root and legally supplied IWD data. Only after observing the original filesystem and map load should renderer, touch-client and gameplay gates be considered. A JNI diagnostic APK is not an acceptable substitute.
