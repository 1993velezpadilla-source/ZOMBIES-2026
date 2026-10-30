# IW3 Android phase DI — connect the original FastFile opener to POSIX descriptors

Date: 2026-10-29.

## Baseline inspected

The branch head before this pass was `36646f8b7a6cc0c80317465f8a79dbe7c95e3cae`.
The preceding DH change added a POSIX `pread()` path to the authentic
`DB_ReadData()` body in `db_file_load.cpp`, and its generated harness now
executes the exact original `DB_ReadData()` and `DB_WaitXFileStage()`
definitions in Android mode.

The remaining caller was still Windows-only:
`DB_TryLoadXFileInternal()` in `db_registry.cpp` opened the FastFile with
`CreateFileA()`, measured it with `GetFileSize()`, and passed that HANDLE-shaped
value to `DB_LoadXFile()`. The POSIX reader could therefore not be reached by
the original zone-loading path. The old mod-directory condition also read the
string dvar through `current.integer`, which is not a valid 64-bit pointer ABI.

## Change

- Added `db_fastfile_posix_open.h`, a narrow bridge that calls the existing
  filesDir-rooted `z2026_platform_open_engine_path_fd()`, verifies the result
  with `fstat()`, rejects non-regular files and sizes above the signed
  `XZone::fileSize` range, and encodes the descriptor with the same
  `DBFastFilePosixOpaqueFromFd()` contract consumed by the original reader.
- Added an Android-only branch to the authentic
  `DB_TryLoadXFileInternal()`. It preserves mod-directory-first lookup and
  normal fallback lookup, passes the opaque descriptor into the original
  `DB_LoadXFile()`, and uses the verified stat size for `zone->fileSize`.
  The desktop branch retains its original `CreateFileA()`/`GetFileSize()`
  behavior. Android intentionally skips the Windows-only `update:\\`
  drive lookup and resolves `mp_patch` through the installed app-private
  FastFile path.
- Corrected the Android mod-directory presence check to use
  `fs_gameDirVar->current.string` rather than treating a pointer-bearing
  string dvar as an integer.
- Extended the existing rooted platform runtime test to create a tiny,
  deliberately incomplete FastFile-header fixture, open it through the exact
  helper, decode the opaque descriptor, read the bytes through the POSIX
  reader, and reject a symlink and a sibling-root escape.
- Extended the dedicated ARM64 workflow to compile the same platform test
  translation unit and added source regressions for the caller/helper contract.

## Validation boundary

The fixture is **not a complete FastFile** and is never passed to
`DB_LoadXFileInternal()`. This pass verifies the real app-root opener, file
metadata, opaque descriptor ABI and byte read. It does not initialize the
original DB registry, invoke `DB_TryLoadXFileInternal()` in the running
Android process, link the complete database translation units, or prove
FastFile deserialization.

The next blockers remain the full `db_registry.cpp`/database service graph,
the Windows/Direct3D geometry and delayed-image finalizers in
`db_file_load.cpp`, authenticated/compressed FastFile support, original
filesystem startup and actual licensed map loading. No renderer frame,
touch-driven live client frame, weapon/actor gameplay, physical ARM64 runtime,
or playable APK is claimed.

Keep PR #4 open and unmerged.
