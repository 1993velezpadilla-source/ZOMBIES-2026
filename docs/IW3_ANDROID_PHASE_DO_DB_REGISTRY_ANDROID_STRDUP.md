# IW3 Android ARM64 pass DO — original database registry POSIX compatibility

Date: 2026-10-30

## Scope

This pass fixes the Android compile blocker in the authentic
`third_party/KisakCOD/src/database/db_registry.cpp` translation unit and
makes its object-only ARM64 audit deterministic. It does not link the database
registry into the JNI library and does not claim a playable game.

## Findings and changes

1. The first current-head NDK build failed at two original `_strdup` calls in
   `DB_RegisterReorderAsset` (source lines 2589 and 2593). Android's Bionic
   headers declare POSIX `strdup`, not MSVC's `_strdup`.
2. The Android-only `db_registry_android_compat.h` now explicitly includes
   `<string.h>` and maps `_strdup` to `::strdup`. The original call sites and
   their allocation/free semantics remain unchanged; Windows does not include
   this Android-only compatibility header.
3. The next run compiled the complete registry object, but its audit did not
   retain the file-local `DB_TryLoadXFileInternal` symbol under Release
   optimization because it was inlined into its caller. The object-only CMake
   target now uses `-fno-inline` so the symbol audit can verify the actual
   static entry point. This option applies only to the compile-audit object;
   the object is not linked into the application.
4. Added source regression coverage for the Android `_strdup` mapping and
   the compile-audit flag.

## Verification

Validated code revision: `61e61eacec73b2343b50a89e598d6dbd419a9b96`.

- [Original-source Android ARM64 audit, run 41015697678](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697678) — PASS.
  - All 348 Python source/preflight tests passed.
  - The full original `db_file_load.cpp` object compiled as ELF64/AArch64.
  - The full original `db_registry.cpp` object compiled as ELF64/AArch64.
  - `llvm-nm` confirmed definitions for
    `DB_TryLoadXFileInternal(char*, int)` and
    `DB_FileSize(char const*, int)`.
  - The loader object retains the expected unresolved renderer calls:
    `R_DelayLoadImage`, `R_FinishStaticVertexBuffer`, and
    `R_FinishStaticIndexBuffer`.
  - The registry object still has unresolved database, filesystem, thread,
    renderer, and engine services. This is an object audit, not a runtime link.
  - The log explicitly retains `IW3_DB_REGISTRY_RUNTIME_LINKED=false`,
    `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, and
    `IW3_PLAYABLE_APK=false`.
  - [Artifact 12959826387 — ARM64 objects and reports, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697678/artifacts/12959826387).
  - [Artifact 12958999240 — original FastFile loader object, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697678/artifacts/12958999240).
- [FastFile POSIX reader gate, run 41015697671](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697671) — PASS.
  - 9 reader regressions, 6 opener/size regressions, 14 native POSIX checks,
    and 12 checks against the extracted original read/wait bodies.
  - [Artifact 12959865673 — ELF objects/report, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697671/artifacts/12959865673).
- [JNI Android ARM64 integration, run 41015697656](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697656) — PASS, diagnostic package only.
  - [Artifact 12959062693 — JNI diagnostic, NOT GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41015697656/artifacts/12959062693).

## Remaining blocker

The complete database registry and FastFile loader translation units are
still not linked into the Android runtime. The undefined-symbol report shows
that the registry depends on original database entry points, filesystem
services, database-thread synchronization, memory/zone services, and renderer
operations. The loader also requires real geometry-buffer and delayed-image
finalization.

Next work must connect those real services in the application runtime and
exercise an authentic FastFile through the original loader. Only after that
can the engine load a BSP/map and present a frame through the original
renderer. Touch must then be consumed by the live client command loop and
gameplay verified on ARM64 hardware.

No FastFile was deserialized by this pass; no BSP/map, renderer frame, touch-
driven gameplay, weapon fire, damage, or actor AI was demonstrated on Android.
The JNI artifact remains diagnostic. PR #4 must remain open and unmerged.
