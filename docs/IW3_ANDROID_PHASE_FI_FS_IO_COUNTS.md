# IW3 Android ARM64 — Phase FI: original filesystem I/O count integrity

Date: 2026-10-31. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Source and blocking failure

The original KisakCOD `src/universal/com_files.cpp` functions `FS_Read` and
`FS_Write` are used by the genuine filesystem/IWD path. `FS_Read` accepted
the signed return value of `unzReadCurrentFile` into an unsigned return type.
On disk errors, it called `Com_Error` and then (if the error handler returned)
subtracted a negative `read` from an unsigned remaining byte count, moving
the destination pointer backward. A broken platform adapter could also report
more bytes than requested. `FS_Write` had the analogous unchecked count.

These are **portability and data-integrity** problems on the path toward
mounting genuine IW3 assets. This pass does **not** make `FS_Startup` run in
Android or prove map loading.

## Original-engine changes

- Preserve the original engine I/O functions, handle table and IWD reader.
- Explicitly convert negative ZIP read results into the existing unsigned
  failure sentinel (`UINT32_MAX`) and reject overreported counts.
- On disk read error, return the failure sentinel even if `Com_Error`
  unexpectedly returns. Preserve the original special handle range 49–61.
- Retry one zero-byte read/write without pointer arithmetic; return partial
  read counts on repeated EOF and zero on repeated zero-byte writes.
- Reject counts larger than the remaining buffer before advancing a pointer.
- Keep `FS_Write` failure result at zero for negative/invalid writes.
- Update the exact-source staging audit to require the new original-body
  error-handling markers, rather than the former one-line ZIP return.

## Verification and limits

`tests/test_iw3_android_fs_io_counts.py` extracts both **actual source
function bodies** and builds a host C++ executable with ASAN/UBSAN.
Its test-only I/O providers exercise short reads/writes, zero retries,
negative ZIP/disk results, overreported counts, zero lengths and null
handles. This is an executable original-body regression, **not** a JNI
diagnostic game and not evidence of ARM64 device gameplay.

The native Android source workflow also runs the Python test discovery and
stages the original `FS_Read` body. Record the precise Actions run status
in the PR after CI finishes; do not call a queued run green.

## Unmet release gates

No demonstrated ARM64 process executing the complete `Com_Init`,
`Cmd_Init`, `Dvar_Init` and `FS_Startup` chain; no real game IWD/FF
map loaded, original renderer output, touch-to-original-client gameplay,
or weapons/actors running on an ARM64 device. The diagnostic JNI APK is
not playable. `IW3_PLAYABLE_APK=false`; PR #4 stays open and unmerged.
