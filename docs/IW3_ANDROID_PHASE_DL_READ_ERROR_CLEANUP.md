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
