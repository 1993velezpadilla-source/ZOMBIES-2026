# Phase FJ — original FastFile geometry-offset arithmetic on Android ARM64

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4 stays open and **must not merge** until genuine gameplay is proven.

## Real engine defect

The authentic KisakCOD `src/database/db_registry.cpp` implemented `DB_GetIndexBufferAndBase` by narrowing two pointers to `uint32_t` before subtracting them. A genuine offset >= 4 GiB silently wrapped on LP64, potentially addressing the wrong index data. The adjacent `DB_GetVertexBufferAndOffset` subtracted pointers from independently managed allocations, invoking undefined C++ pointer-subtraction behavior and narrowing to signed 32-bit without bounds checks.

## Implementation

- Commit `1318ecff5a4c5ab51425a8df63e3f071d2de001f` changes the **original** `third_party/KisakCOD/src/database/db_registry.cpp`, not an Android mock.
- Both functions now compute byte offsets using `uintptr_t`, validate zone indices, non-null pointers, forward offsets, and signed 32-bit representability. The index helper also enforces 16-bit index alignment.
- The original output contract remains `void` with GPU buffer pointer and `int32_t` offset. Invalid input clears both outputs and calls the original `Com_Error(ERR_DROP, ...)` service, returning safely if that handler returns.
- Commit `7f150307061664220114f3cd5e4f9da35ea86b1a` adds `tests/test_iw3_android_db_geometry_offsets.py`, which extracts **both original function bodies verbatim** and compiles them with AddressSanitizer/UndefinedBehaviorSanitizer against isolated zone-state test providers. The test covers valid 64-bit offsets, 4 GiB boundary crossing, 4 GiB wraparound, misalignment, reversed addresses, invalid zones, null inputs, and 32-bit overflow.

## Verification and hard limits

The branch's `IW3 ORIGINAL SOURCE Android ARM64 math port (NOT APK)` workflow runs `python3 -m unittest discover -s tests -p 'test_iw3_android_*.py' -v` and compiles the complete authentic `db_registry.cpp` for Android ARM64 as an **OBJECT-only** gate. The source and test changes triggered run [41171540191](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41171540191). **CI outcome was pending when this document was first written; no success is asserted until logs confirm the test and full translation-unit compile.**

This does **not** integrate the registry, database, renderer, `Com_Init` or `FS_Startup` into an executable Android game process. No licensed map has been loaded or rendered; touch-driven weapon/actor gameplay has not been demonstrated. The JNI APK remains diagnostic only. `IW3_PLAYABLE_APK=false`.

Next critical integration: link and execute the authentic `Com_Init` / `Cmd_Init` / `Dvar_Init` / `FS_Startup` graph on Android, followed by real FastFile/map loading, rendering and original gameplay. Do not use Godot or a substitute engine.
