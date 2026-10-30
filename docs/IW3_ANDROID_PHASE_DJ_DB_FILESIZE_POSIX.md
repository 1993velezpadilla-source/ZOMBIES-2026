# Phase DJ — portable DB_FileSize on Android (not gameplay)

Date: 2026-10-30 UTC

## Baseline and blocker

The original `DB_TryLoadXFileInternal()` path had an Android-only rooted POSIX opener, but the public `DB_FileSize()` helper still unconditionally used Win32 `CreateFileA/GetFileSize/CloseHandle`. Other database code can call `DB_FileSize()` independently of the immediate zone-open path, so this left a remaining Windows-only file-size path in the original registry source.

## Change

- Added `DBFastFilePosixFileSizeEnginePath()` beside the shared rooted opener. It reuses the same filesDir-confined open, regular-file validation, `fstat()`, 32-bit size bound and opaque-descriptor contract, then closes the descriptor before returning.
- Added an Android branch to the original `DB_FileSize()` in `third_party/KisakCOD/src/database/db_registry.cpp`. Android now uses the shared POSIX helper; the original Win32 implementation remains under `#else`.
- Extended `platform_native_test.cpp` to execute the same size helper against the existing valid FastFile fixture, a missing file, a symlink, and a sibling-root escape.
- Extended the Python source-contract regression to require the POSIX helper in the Android branch and preserve Win32 calls only in the Windows branch.

## Validation scope

The existing `iw3-fastfile-posix-read-arm64.yml` workflow already watches the modified registry, helper, platform test and regression test. It runs the host native test and compiles the platform test as an ELF64/AArch64 object. The source-contract test verifies the original caller's conditional branches.

This is still a portability increment, not a FastFile loader proof. The complete `db_registry.cpp` translation unit is not yet linked into the Android runtime by this gate. No real FastFile was deserialized, no BSP/map was loaded, no original renderer frame was observed, and no Android gameplay was proven. The diagnostic JNI APK is not a playable game.

## Remaining gate

Compile the exact original database caller in the actual Android runtime target, resolve the database service graph without no-op stubs, and then demonstrate authentic FastFile deserialization and BSP/map initialization before claiming renderer or gameplay progress. Keep PR #4 open and unmerged.
