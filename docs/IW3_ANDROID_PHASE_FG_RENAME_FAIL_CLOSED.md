# Phase FG — original IW3 Android rename path safety (2026-10-31 UTC)

## Scope and baseline

PR #4, branch `feature/iw3-native-android-arm64-20261025`.
Baseline head `e2d05b3ffae04ff209d97476fc2c86b12d4d01de`.
The preceding native-source workflow [41154571482](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41154571482) completed **SUCCESS**, as did the other eleven workflow runs associated with that baseline commit. Those were source/host/emulator-diagnostic checks, **not original-engine ARM64 gameplay**.

## Real original-engine defect

`third_party/KisakCOD/src/universal/com_files.cpp` retained an unsafe path operation in `FS_SV_Rename`: it unconditionally performed `from_ospath[strlen(from_ospath) - 1] = 0` and the same operation for the destination. `FS_BuildOSPath` deliberately returns an empty string for an overlong Android app-private path if the engine fatal handler returns. The original rename then wrote at index -1, and could proceed with invalid paths.

`FS_Rename` also passed paths from `FS_BuildOSPath` to the Android rooted rename adapter without checking for empty names, an empty root, or an overlong rejected result. Both are relevant to saving/renaming original game files.

## Implemented in the authentic engine

- [676cddd](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/676cddd048ba41e578a0e6b3554e41d7e3774885): `FS_SV_Rename` now uses the existing authentic `FS_SV_BuildOSPath` guard on both paths and exits without I/O if either fails. `FS_Rename` rejects null/empty filenames and empty data roots, then checks each built path before the rooted rename call. The host-only `IW3_FS_POSIX_PATHS_TEST` definition uses the same rooted adapter branch as Android; the Windows branch remains intact.
- [951707a](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/951707ae99fbddccd9c6c6dd5df0e153c9f5e7f5): the existing original filesystem-startup extraction now stages both **verbatim authentic function bodies** into its AArch64 dependency archive and host harness. No replacement game logic is introduced.
- [ad8c5c9](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/ad8c5c918f1e6ac3f3b977f9255fd9def71a1399): host C++ harness invokes both original rename functions against an observable rooted-platform spy, checking valid paths, empty root/name, overlong name and overlong root with a returning fatal handler. Marker: `IW3_ORIGINAL_FS_RENAME_PATH_GUARD_PASS`.
- [8969039](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/896903974a51bce0afafc131e8face6b28402ec3): Python regression verifies the authentic source guards and that the extracted bodies are identical to the original source.

## CI status at initial documentation

New head `896903974a51bce0afafc131e8face6b28402ec3` triggered [native-source workflow 41157412762](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41157412762), **queued at first inspection**. The host test and Python regression are part of this workflow. Do **not** count them as passing until its completed logs confirm. The baseline success does not validate these new edits.

## Unmet genuine-game gates

`IW3_CLIENT_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.

No playable ARM64 APK exists. The JNI diagnostic APK and host tests are not substitutes for real `Com_Init`/`FS_InitFilesystem`, licensed IWD/FF/map loading, original renderer, live client touch and observed actor/weapon gameplay. PR #4 must remain open and unmerged.
