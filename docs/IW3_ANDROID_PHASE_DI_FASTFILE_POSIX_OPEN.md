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


## Follow-up — mod-directory string dvar ABI and mod probe

The opener path also calls the original `DB_BuildOSPath_Mod()`. A source
audit found that this helper, `DB_ModFileExists()`, and the referenced-zone
list still read `fs_gameDirVar` through the integer union member. Replaced
those pointer reads with the original string union member. The Android
`DB_ModFileExists()` path now probes through the same rooted POSIX opener and
closes the decoded descriptor; the Windows path remains unchanged.

The dedicated AArch64 compile initially stopped because the platform test
includes the authentic `qcommon/msg.h` through `iw3_android_usercmd_compat.h`.
Added the engine source root to the NDK include search path so the original
header resolves. This follow-up must pass the restarted ARM64 workflow before
being counted as validated.


## Observed CI results for this pass (2026-10-30 UTC)

- FastFile POSIX reader/opener ARM64 gate: [run 40984678623](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40984678623) **passed**. It ran 7 existing POSIX-reader Python regressions and 5 opener/caller regressions; the native reader test reported 14 checks; the generated exact-body `DB_ReadData`/`DB_WaitXFileStage` harness reported 12 checks; and the NDK emitted ELF64/AArch64 objects for the reader, exact-body harness and rooted platform opener test. Artifact 12946163729 contains objects/reports only, not an APK.
- Original engine ARM64 audit: [run 40984678658](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40984678658) **passed**. Host CTest passed 24/24 in both Release and ASan/UBSan configurations. The NDK compile/link gates passed for the complete original SP frame, original client command/touch/aim-assist edges, original player/trigger/mover/actor routines and the existing filesystem/IWD dependency archives. Artifacts 12946855588, 12945853656, 12945524638 and 12945509548 are native objects/archives/reports, not an APK.
- JNI integration: [run 40984678636](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40984678636) **passed** and produced artifact 12945874927. It is explicitly a signed ARM64 JNI diagnostic package, not a playable game.
- The source-level regression confirms the Android caller branch no longer uses Win32 open/size calls and that the mod-directory string dvar is read through its pointer member. The host platform test executes the exact shared opener helper against a real rooted fixture, including descriptor decoding/read, symlink rejection and sibling-root escape rejection.

## Remaining unverified boundary

Neither the full `db_registry.cpp` translation unit nor the Android branch of
`DB_TryLoadXFileInternal()` has yet been compiled and linked into the Android
runtime. The opener helper is host-executed and separately cross-compiled for
AArch64; the caller wiring is currently guarded by source-level regression.
The Android emulator JNI run is still a diagnostic (x86_64 emulator), and
there is no observed FastFile deserialization, real BSP/map load, original
renderer frame, touch-driven live simulation, weapon/actor gameplay on an
ARM64 device, or playable APK.

Next engineering gate: compile the exact Android `DB_TryLoadXFileInternal`
caller path with original database types, then resolve the remaining
`DB_LoadXFileInternal` platform services (notably geometry/delayed-image
finalization and authenticated/compressed FastFile services) before attempting
a real zone load. Keep PR #4 open and unmerged.
