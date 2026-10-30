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
