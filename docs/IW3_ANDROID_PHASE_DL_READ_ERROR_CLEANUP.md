# Phase DL — clean up FastFile reader errors before ERR_DROP (NOT GAME)

Date: 2026-10-30 UTC

## Baseline inspected

The Android branch of the original `DB_ReadXFileStage()` called
`Com_Error(ERR_DROP, ...)` immediately when `DB_ReadData()` returned false
with a nonzero `g_load.posixReadError`. Unlike the corrupt-inflater and
truncated-EOF paths, this branch did not first invoke the original
`DB_CancelLoadXFile()`. A POSIX read failure could therefore unwind the zone
load while leaving the inflater and file descriptor active.

## Change

The Android read-error branch now snapshots `g_load.posixReadError` into a
local `readError`, invokes the original `DB_CancelLoadXFile()`, and only
then dispatches `Com_Error(ERR_DROP, ...)`. Snapshotting preserves the errno
reported to the log even if cleanup changes loader state. The original Win32
`GetLastError()/Com_Error` branch is unchanged.

No stub, replacement loader, or alternate simulation was added.

## Regression

`tests/test_iw3_android_fastfile_posix_io.py` now extracts the original
`DB_ReadXFileStage()` source region and verifies that the Android read-error
branch snapshots the error, calls `DB_CancelLoadXFile()` before `Com_Error`,
and reports the saved value. It also verifies that the original Windows branch
remains unchanged and does not inherit the Android cleanup edit.

The existing `iw3-fastfile-posix-read-arm64.yml` gate runs this regression
along with the original-body read harness and NDK ELF64/AArch64 compile checks.

## Validation limits

This is a cleanup-path correction in the authentic original loader source.
The source regression checks ordering; the existing harness executes the
original `DB_ReadData()` and `DB_WaitXFileStage()` bodies against a real
temporary file, but does not execute the complete `DB_ReadXFileStage()`
inside the engine runtime.

This does **not** integrate the full `db_file_load.cpp` or
`db_registry.cpp` translation units into the Android game runtime. It does
not prove FastFile deserialization, BSP/map loading, renderer presentation,
touch consumption by the active client, or gameplay on a physical ARM64
device. Any JNI APK remains diagnostic, not playable.

## Next gate

Compile and link the original database registry/loader service graph in the
Android runtime without no-op stubs, then demonstrate loading an authentic
FastFile and BSP/map before claiming rendering or gameplay. Keep PR #4 open
and unmerged.


## Phase DM — close the Android descriptor on malformed FastFile metadata

A second review of the original `DB_LoadXFileInternal()` found early exits that
preceded inflater initialization or failed before zone deserialization. The
Android opener had already acquired a POSIX descriptor, but the empty-file,
truncated/invalid magic, truncated/unsupported version, unexpected-header-status,
and progress-size-query failure paths could dispatch an assertion/error without
calling the original cancellation routine first.

The Android-only branches now call `DB_CancelLoadXFile()` before their failure
dispatch. The original Win32 branches and their error handling are retained.
For header failures this deliberately reuses the engine's existing cancellation
path rather than adding a second descriptor-close mechanism.

The existing FastFile regression workflow now checks each affected branch and
requires the cleanup call to be inside the Android guard and before the first
`Com_Error()` or `MyAssertHandler()` dispatch. The test is source-order
verification; it does not claim to execute all malformed-header cases inside
the complete Android runtime.

**Scope remains limited:** this closes descriptor/inflater state on these
additional loader failure paths. It does not link the full database registry
and loader into the JNI runtime, authenticate/decompress proprietary FastFiles,
load a BSP, present a renderer frame, or prove touch-driven gameplay. Any JNI
APK remains diagnostic; keep PR #4 open and unmerged.
