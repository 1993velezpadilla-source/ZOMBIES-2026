# IW3 Android phase FH — authentic FS_ReadFile integrity (2026-10-30)

## Scope and reason

Reviewed PR #4 head `f53c8261d1b3a5432d469081e5a3a1c570906414` and its 12 completed successful workflow runs,
including original ARM64 source/ABI compilation. These checks do not establish
Android `Com_Init`, map loading, rendering, touch-driven gameplay, or a playable APK.

The authentic `third_party/KisakCOD/src/universal/com_files.cpp`
`FS_ReadFile` previously ignored the return from `FS_Read`. A truncated
IWD/config/map entry could be returned as a full-length successful read with an
uninitialized tail, then fed to game parsers. The original function also passed
`len + 1` to the Hunk allocator without rejecting negative/INT_MAX lengths
and dereferenced allocation failure. The fix remains in the authentic engine
source; no JNI diagnostic shim or replacement engine is involved.

## Implementation

- Initialize the output buffer and file handle to safe defaults.
- Reject negative and INT_MAX lengths, closing the original FS handle.
- Check Hunk allocation and require an exact `FS_Read` byte count.
- On short/failed reads, free the original Hunk buffer, restore
  `fs_loadStack`, close the FS handle and return -1.
- Return immediately after fatal empty-name error if a test/platform
  handler unexpectedly returns.

`tests/test_iw3_android_fs_readfile_integrity.py` extracts the *original*
function body and executes it under host ASan/UBSan with isolated
test-only external FS/Hunk services. Cases include exact read, size-only
query, truncated read, read error, negative/INT_MAX length, missing
handle, allocation failure, zero-length file and empty-name error.

## Evidence / limitations

This source-level regression is not a gameplay demonstration. Inspect the
post-commit Actions run for `IW3_ORIGINAL_FS_READFILE_INTEGRITY_PASS`,
Python test count and ARM64 full-TU/ABI link results; no CI result is
claimed before it completes.

**Still required for playable ARM64:** link and execute original
`Com_Init` / `Cmd_Init` / `Dvar_Init` / `FS_InitFilesystem` in Android;
mount licensed genuine game IWD/fastfile assets; load a real map; integrate
the authentic renderer with an Android graphics backend; consume touch
input through original client/game loops; and capture on-device gameplay
with weapons and actors. Diagnostic JNI APK is NOT a playable game.
Do not merge PR #4 into main until those gates have evidence.
