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

CI result for this revision: pending at the time this document was added. The
workflow log is the authoritative record; do not infer a pass from the CMake
target's presence alone.

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
