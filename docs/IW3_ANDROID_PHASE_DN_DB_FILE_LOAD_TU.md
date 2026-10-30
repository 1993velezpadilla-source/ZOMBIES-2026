# IW3 Android ARM64 — Phase DN: original FastFile loader translation unit

## Scope

This pass closes a gap between the extracted FastFile helper audits and the actual
KisakCOD source tree: the complete original
`third_party/KisakCOD/src/database/db_file_load.cpp` is now an Android NDK
compile target.

The Android source branch no longer imports the Win32-only `win_local.h`,
Direct3D image header, or Direct3D buffer header. The original Windows include
path remains unchanged. `database.h` similarly avoids importing
`win_local.h` on Android while retaining the original Win32 completion
callback declaration only on Windows.

A declaration-only header exposes the three renderer service signatures used
by the original loader:

- `R_DelayLoadImage`
- `R_FinishStaticVertexBuffer`
- `R_FinishStaticIndexBuffer`

There are no Android implementations or no-op substitutes for these calls.
The compile gate explicitly checks that they remain unresolved in the loader
object, which is expected until the original renderer backend is ported.

## Validation

The native Android workflow now builds the `iw3_sp_db_file_load_full_compile`
OBJECT target from the real source file, verifies the resulting object is
ELF64/AArch64, confirms `DB_LoadXFileInternal()` is defined, and checks that
the renderer service edges remain undefined.

The source-level regression is
`tests/test_iw3_android_db_file_load_compile_gate.py`.

The first ARM64 attempt, workflow run `41010107687`, reached the new
full-source object target but failed while parsing upstream `__declspec(align(...))`
declarations transitively included by `xanim.h` / `r_rendercmds.h`. The first
diagnostics were MS-extension syntax errors, followed by cascading missing
renderer-layout types. This was a compiler-mode issue, not evidence that the
renderer services had been implemented.

The target now enables Clang's `-fms-extensions`, matching the extension mode
already used by the existing original mover/trace source gate. A new source
regression requires this flag. The next attempt (`41010278394`) passed the
MS-extension parsing stage but exposed the next real LP64 issues in the
transitive original asset headers:

- Win32-only size assertions for `GfxWorld`, `LoadedSound`, `SndCurve`,
  `snd_alias_t`, and `snd_alias_list_t`.
- An opaque desktop `HWND` declaration not supplied on the Android include path.
- ODE's Windows-oriented `<vadefs.h>` include, unavailable in the NDK sysroot.

This pass now records the measured Android LP64 in-memory sizes with
Android-specific static assertions (the original Win32 assertions remain
unchanged), declares `HWND` as an opaque pointer only on Android, and uses
standard `<stdarg.h>` for ODE's `va_list` declaration on Android. These are
ABI/header portability changes, not fake renderer or physics implementations.
The next NDK retry is pending. No compile pass is claimed until the full object
and expected unresolved renderer symbols are verified.

The following attempt (`41010620368`) got past the renderer-header and ODE
include blockers but exposed the broader original asset ABI surface:

- LP64 sizes for `XModel`, `XModelPiece(s)`, `XModelSurfs`,
  `XModelPartsLoad`, `XAnimIndices`, `XAnimParts`, `WeaponDef`,
  `RawFile`, `XAsset`, `ScriptStringList`, `XAssetList`,
  `XRigidVertList`, `XSurfaceVertexInfo`, and `XSurface`.
- Duplicate `clientDebug*` declarations reached through the original
  renderer and client include graph.
- The original `BOOL` declaration required by the XAnim header surface.

The current pass records the measured LP64 runtime sizes in Android-only
assertions, adds a shared guard for the duplicate client debug declarations,
and supplies the opaque `BOOL` alias. This is **not** a claim that serialized
FastFile records have become LP64: the file format still carries 32-bit
serialized offsets/pointers, and the original loader must explicitly relocate
those into the larger runtime structures before a real FastFile can load.
That conversion remains a blocking runtime task.

## Strict limits

This is a **compile-only** original-source milestone. It does not link
`db_file_load.cpp` into the Android JNI APK, does not execute
`DB_LoadXFileInternal()`, does not deserialize a real FastFile, and does not
load a BSP/map or render a frame.

Still pending:

1. The original database registry and complete service graph.
2. Android implementations of the original renderer's geometry/image
   completion services.
3. Real FastFile deserialization and BSP/collision-world loading.
4. Original client/server bootstrap and active `CL_CreateCmd` input path.
5. Observed ARM64 device execution with gameplay, weapons, and actors.

The diagnostic APK remains diagnostic. `IW3_PLAYABLE_APK=false`; keep PR #4
unmerged until the full playable-game criteria are demonstrated.
