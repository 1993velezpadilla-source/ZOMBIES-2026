# IW3 Android phase CH — validate imported IWDs with the original indexer

Date: 2026-10-28

## Inspected baseline

PR #4 is open and unmerged on `feature/iw3-native-android-arm64-20261025`, baseline HEAD `799952b6a8a5ebe1133f273235294721ef77b492`. The existing importer stages user-owned `.iwd` and `.ff` files under the app-private `filesDir/main` and `filesDir/zone` paths. It did not ask the native engine code to inspect those imported IWD archives. The existing JNI smoke creates a synthetic ZIP32 fixture, so its PASS must not be described as validation of the user's files.

## Concrete change

- Added a bounded validator that enumerates root-level IWDs in `main/` and `zone/` through the rooted Android directory adapter.
- Each listed archive is passed to the original `FS_LoadZipFile` implementation. The validator checks the indexed entry count, original index/hash-table state, checksum fields, and entry-name pointers, then closes the original ZIP handle and releases the original engine allocations while restoring `fs_iwdFileCount` and `fs_checksumFeed`.
- The JNI bridge exposes `nativeValidateImportedIwds`; the importer calls it after staging and reports the actual archive/entry counts or the failing relative path.
- Added an isolated synthetic fixture under a temporary app-private root so the Android emulator CI executes the same original `FS_LoadZipFile` index path without requiring proprietary game data. The fixture and directories are removed and the previous root is restored.
- Added a regression gate for the native source, Java flow, JNI symbol, workflow symbol audit, and emulator evidence marker.

## Scope and limits

This validates IWD central-directory indexing only. It does not mount the complete original `fs_searchpaths` graph, run `FS_Startup()/FS_InitFilesystem()`, parse FastFiles, load a map, render a scene, or run player/weapon/actor gameplay. The synthetic CI fixture is not user game data. The JNI package remains diagnostic only; no playable APK is claimed.

## Validation status

CI is triggered by the branch update. Do not mark this pass green until native ARM64/source tests, JNI build/symbol checks, and the emulator fixture run finish. Keep PR #4 open and unmerged.
