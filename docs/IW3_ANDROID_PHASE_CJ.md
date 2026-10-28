# Phase CJ — malformed IWD fail-closed regression

**Baseline inspected:** PR #4 head `7f85567bdb95d95d5f3a45b024985e5980b98593`, with the latest successful CI set attached to that head. The Android app remains a JNI diagnostic, not a playable game.

## Concrete change

Extended the native fixture that already calls the authentic KisakCOD `FS_LoadZipFile` body. In addition to the signed global-counter overflow case and a valid two-entry archive, it now writes a ZIP32 fixture whose central-directory filename contains an embedded NUL byte. The original loader must reject the archive during its sizing pass, before index allocation/publication, and leave `fs_iwdFileCount` and `fs_checksumFeed` unchanged.

On Android, a dedicated log marker `IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS` is emitted only when this negative-path check and the existing valid-index/cleanup checks all pass. The emulator script requires that marker, so a successful job cannot rely solely on APK compilation or the older generic fixture marker.

Files:
- `android/iw3-native/iw3_unzip_native_smoke.cpp`
- `tools/iw3_android/run_emulator_probe.sh`
- `tests/test_iw3_android_iwd_fail_closed.py`

Code commits:
- `5a3f36354b5e4b023af5b208143a139945434726` — malformed IWD fixture and Android marker.
- `39656e269bc5a8e924ee34cda8bef0c60a861ab9` — correct the C++ embedded-NUL fixture literal.
- `d99a63e1fec643d316e58445febbb628c86da7b8` — require the marker in emulator evidence.
- `36fa30a9790f8b1ed8b5454bee0cdd8d9ef3c3d9` — source and CI regression tests.

## Validation status

The source preflight run for code commit `36fa30a9790f8b1ed8b5454bee0cdd8d9ef3c3d9` passed. The native ARM64, JNI, emulator and SP workflows were triggered and were still pending at the time of this note; do not count them as passed until their final conclusions are inspected.

## Scope boundary / next blocker

This pass strengthens the real IWD indexer's failure-path evidence; it does **not** invoke `FS_Startup()` or `FS_InitFilesystem()` in the app. The full startup/command graph, authentic FastFile/map load, original renderer, live frame/input loop and physical ARM64 gameplay remain unproven. The JNI package remains diagnostic. Keep PR #4 open and unmerged; `IW3_PLAYABLE_APK=false`.
