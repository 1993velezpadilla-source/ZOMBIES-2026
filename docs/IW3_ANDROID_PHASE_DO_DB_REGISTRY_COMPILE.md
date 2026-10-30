# IW3 Android ARM64 — Phase DO: compile the original database registry

## Why this pass exists

The current branch head (`cbe8187240b5ccaeb010107fa73c1f9abff58e8d`) already
compiles the complete original `db_file_load.cpp` translation unit for
ELF64/AArch64. The FastFile-specific POSIX reader gate also passes. However,
the original caller and asset-zone registry in
`third_party/KisakCOD/src/database/db_registry.cpp` had not been compiled as
a complete Android translation unit.

That leaves an important gap: helper-level checks do not prove that the real
`DB_TryLoadXFileInternal()` and `DB_FileSize()` definitions survive the
Android LP64 include graph.

## Concrete change

This pass adds the OBJECT-only CMake target
`iw3_sp_db_registry_full_compile`, sourcing the complete original
`database/db_registry.cpp` with the Android NDK and the same native headers.
The target is not linked into the JNI diagnostic library. No renderer, asset
pool, or database callback is stubbed.

The native workflow now inspects the resulting object for ELF64/AArch64 and
for the real definitions `DB_TryLoadXFileInternal` and `DB_FileSize`, then
preserves the object and undefined-symbol report as a **NOT APK** artifact.

A new source regression verifies that the Android branch still uses the
filesDir-confined POSIX FastFile opener while the original Windows branch
retains its Win32 path.

## First NDK result and measured blocker

The first full-registry compile attempt (workflow run
[41012437729](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41012437729))
reached the new object target and failed at the renderer declaration boundary,
not in the database function bodies. Clang reported:

- missing `_D3DCUBEMAP_FACES`;
- missing `D3DFMT_D24S8`, `D3DFMT_D24X8`, and `D3DFMT_D16`;
- an unconditional `Windows.h` include from the original `r_init.h`.

The Android shared-renderer headers already selected `r_d3d9_opaque.h`, but
that header only forward-declared `_D3DFORMAT` and a subset of D3D interfaces.
This iteration extends it with ABI-sized enum declarations, the 16-byte
`_D3DDISPLAYMODE` layout, and opaque interface/window declarations. It also
guards the Windows/D3D9 SDK includes in `r_init.h` so Android uses the existing
opaque ABI boundary. No D3D implementation or renderer stub is added.

The retry is required to discover the next include/platform edge. The initial
failure is preserved as evidence; it is not counted as an Android registry
compile pass.

## Second NDK result: Win32 local header

After the D3D9 declaration boundary was fixed, the next compile attempt
[41012946523](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41012946523)
advanced through the Android renderer headers and stopped at
`win32/win_local.h:16`: the NDK does not provide `dinput.h`. That header is
not needed for the database registry's Android branch; it was imported only
to obtain shared qcommon declarations alongside Windows DirectInput APIs.

The original `db_registry.cpp` now includes the shared qcommon, critical-section,
and SP net-channel headers on Android, while retaining `win_local.h` exclusively
for desktop builds. `IsConfigFile` now uses its actual boolean return semantics
instead of importing Win32's `BOOL` typedef. This does not replace any engine
service implementation. The next NDK attempt will reveal remaining Windows file
operations in the optional zone-reorder CSV path.
## Third NDK result: renderer backend still imported D3D9 directly

With the Win32 local header excluded, the next Android compile attempt
[41013294122](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41013294122)
passed the new qcommon include boundary and stopped at
`gfx_d3d/rb_backend.h:5`, which independently included `d3d9.h`. Its required
opaque interface types are already supplied through the original shared
`r_material.h`/`r_gfx.h` Android declaration path, so the backend header now
keeps the real SDK include on desktop only. This adds no renderer behavior.

The next NDK build is still needed to discover remaining D3D declarations
and the Windows-only zone-reorder CSV I/O. The complete registry is not yet
compiled or linked.
## Fourth NDK result: remove the last direct backend D3D9 include

The compile attempt at [41013488779](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41013488779)
passed the `r_init.h`/`win_local.h` guards and reached
`gfx_d3d/rb_backend.h`, whose direct `<d3d9.h>` include was the next fatal
error. The backend now keeps that SDK include desktop-only; its Android
translation unit receives the same opaque D3D9 declarations through the
original shared renderer data headers.

The same attempt also exposed the next genuine DB registry service gaps:
`_itoa`, `Sys_DefaultInstallPath`, Windows Interlocked increment/decrement
calls, and the SP `CRITSECT_MISSING_ASSET` constant. An Android-only
`db_registry_android_compat.h` now provides fixed-width atomic operations and
the exact SP critical-section index. `Sys_DefaultInstallPath()` is backed by
the configured filesDir via `z2026_platform_copy_data_root`; it does not
return the process cwd. The decimal `_itoa` use is implemented with bounded
`snprintf`.

The Windows-only zone-reorder CSV operations are still to be ported or
explicitly excluded from the Android runtime before the registry can link.
No full DB registry compile or runtime pass has been claimed yet.
## What this does not prove

This is a compile gate only. It does not link the database registry to the
Android process, invoke `DB_LoadXAssets()`, deserialize a FastFile, mount a
map, initialize renderer assets, or run gameplay. The unresolved symbols are
evidence of the remaining service graph, not successful runtime integration.

The current source shows a large platform surface in this translation unit:
Win32 network/localization/window headers, Direct3D renderer headers, reorder
CSV file I/O, asset finalizers, sound/image services, and zone synchronization.
The first NDK compile will identify the actual blocking declarations and
platform calls. Fixes must retain original engine behavior; declaration-only
boundaries may describe unresolved real services, but no-op implementations
must not be introduced.

## Required next gates

1. Compile the full registry translation unit for Android ARM64.
2. Guard or adapt only the genuine Win32-only include and file-I/O edges while
   preserving the desktop branch.
3. Keep renderer/asset-service references explicit and unresolved until the
   original renderer and database service graph is ported.
4. Link and execute the original database registry with the original loader,
   then prove a real FastFile and BSP/map load.
5. Continue to require an original-renderer frame, touch-driven client command,
   and observed ARM64 gameplay before producing a playable APK.

`IW3_DB_REGISTRY_RUNTIME_LINKED=false`,
`IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, and
`IW3_PLAYABLE_APK=false` remain the honest state until those gates are met.
