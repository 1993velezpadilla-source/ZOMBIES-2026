# IW3 Android phase CI — guard IWD entry-counter overflow

Date: 2026-10-28

## Inspected baseline

Code baseline tested by CI: `0f9ace089505b36a59a04213fe27ecfac64500ae` on `feature/iw3-native-android-arm64-20261025`, PR #4. The preceding implementation already staged the original KisakCOD `FS_LoadZipFile` body and exercised it against a synthetic two-entry IWD archive in Android JNI smoke.

## Concrete engine correction

In `third_party/KisakCOD/src/universal/com_files.cpp`, the original `FS_LoadZipFile` now checks the signed global `fs_iwdFileCount` immediately after reading ZIP central-directory metadata and before any index allocation:

- Reject a negative global counter as invalid state.
- Reject when `gi.number_entry > INT_MAX - fs_iwdFileCount`.
- Close the ZIP handle and return failure before allocations or `fs_iwdFileCount += gi.number_entry`.

This prevents signed overflow in the shared IWD entry counter and rejects the archive before it can publish an inconsistent index. The extracted-source generator `prepare_real_engine_iwd_mount.py` now requires this guard and reports `iwd_entry_count_overflow_rejected_before_allocation=true`; it still extracts the original function body verbatim.

## Regression and execution evidence

The native fixture now:
1. Creates a synthetic IWD with two valid entries under a temporary app-private root.
2. Sets the global counter to `INT_MAX` and calls the original `FS_LoadZipFile` with that archive.
3. Requires rejection with the counter unchanged.
4. Restores the original state and runs the normal original-indexer validation, which must still index both entries.
5. Cleans up the fixture and restores the data root.

The current source-preflight/native workflow reports 217 Python tests passing, CTest Release 22/22, and CTest ASan/UBSan 22/22. The ARM64 audit succeeded and produced the non-game audit artifact: [run #1386, artifact 12858481264](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665908/artifacts/12858481264).

The JNI Android build succeeded: [run #1302](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665869). The emulator executed the new regression and logged `IW3_JNI_IMPORTED_IWD_INDEX_FIXTURE_PASS`, along with the existing IWD parser/searchpath/read smoke markers: [run #1159, artifact 12858826354](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665919/artifacts/12858826354).

## Limits (not a playable-game claim)

The emulator is x86_64. The test exercises the original IWD loader and synthetic archive only. It does not prove that `FS_Startup()/FS_InitFilesystem()` ran in Android, that real user game data/FastFiles or a map mounted, that an original renderer drew a scene, or that weapons/actors ran in a real session. The native audit still reports `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_GAME_DATA_MOUNTED=false`, and `IW3_PLAYABLE_APK=false`.

Keep PR #4 open and unmerged. Do not describe the JNI diagnostic APK as the game.
