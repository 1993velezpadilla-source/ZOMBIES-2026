# IW3 Android phase CG — harden user-owned data staging

Date: 2026-10-28

## Current code and CI inspected first

PR #4 remains open and unmerged on `feature/iw3-native-android-arm64-20261025`, head `1f328812a6994e02dd6921a6271d82b37cc92458`. The current native ARM64 audit, JNI diagnostic build, x86_64 emulator probe, Windows SP build and Killhouse diagnostic all completed successfully on the prior head `1f328812`. Those are component/audit results; the JNI APK is not a playable game.

The current app compiles with Android minSdk 26. The SAF importer was the immediate data-staging prerequisite, but its previous fixed temporary filename and delete-then-rename sequence could discard an already imported asset if finalization failed. Its recursive walk also had no explicit depth/node/file bounds and could merge case-variant directories after lowercasing.

## Change in this pass

`GameDataImporter` now:

- creates an exclusive, unique temporary file in the destination directory;
- syncs the complete file before publishing it;
- uses Android's POSIX `Os.rename` for same-filesystem atomic replacement, preserving the old target if the rename fails;
- checks both canonical parent and target remain beneath app-private `filesDir`;
- bounds the SAF walk to 16 directory levels, 32,768 document nodes and 16,384 IWD/FastFile entries;
- rejects duplicate destination paths caused by case-normalized directory collisions;
- removes failed temporary files without deleting the previously imported target.

The importer still accepts only user-selected `main/` and `zone/` content and does not bundle or decrypt assets. The Python regression now guards the atomic replacement and traversal bounds. Android Gradle/NDK CI must compile this revision before the change is considered validated.

## Runtime boundary

This is a data-staging reliability fix, not an engine startup implementation. `FS_Startup()` and `FS_InitFilesystem()` remain audit archives with unresolved original services; they are not called by the Android activity. No authentic FastFile or map has been loaded in-app, no original 3D scene has been rendered, and no touch-driven frame/weapon/actor gameplay has been observed on a physical ARM64 device.

Keep PR #4 open and do not merge to `main`. Required next milestone is to close the original filesystem bootstrap dependency graph and invoke it in the Android runtime, then prove a real map load before pursuing renderer and gameplay evidence.
