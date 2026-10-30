# IW3 Android ARM64 pass DY — actor-corpse pointer-width safety

Date: 2026-10-30

## Starting point

The current PR head had the complete original SP frame and the original
`ClientEndFrame(gentity_s*)` provider compiled as ELF64/AArch64. The
relocatable frame link still reported `G_UpdateActorCorpses()` as an
unresolved service.

While tracing that exact frame edge into
`third_party/KisakCOD/src/game/actor_corpse.cpp`, two loops were found to
compare pointers after narrowing them to `int`:

- `G_GetActorCorpseIndex()` compared `(int)p_entnum` with
  `(int)&g_scr_data.actorBackup`;
- `G_PruneLoadedCorpses()` used the same 32-bit pointer-bound comparison.

That is invalid for the Android LP64 ABI and can truncate a 64-bit address.

## Source correction

Both loops now use the actual fixed array bound
`ARRAY_COUNT(g_scr_data.actorCorpseInfo)` and index the original 16-entry
`actorCorpseInfo` array directly. No entity data, corpse capacity, ordering,
sort behavior, removal behavior, or actor-corpse implementation was replaced.
The original `G_UpdateActorCorpses()` still reads the engine's
`ai_corpseCount` dvar and calls the original `G_RemoveActorCorpses()`.

The original source is still the provider. No stub or copied gameplay
implementation was introduced.

## ARM64 compile/link gate

Added the CMake OBJECT target
`iw3_sp_actor_corpse_full_compile` for the complete original
`game/actor_corpse.cpp` translation unit. The native Android workflow:

1. checks the resulting object is ELF64/AArch64;
2. verifies the real `G_UpdateActorCorpses()` and
   `G_RemoveActorCorpses(unsigned int)` definitions;
3. performs a relocatable link with the previously audited original
   `G_RunFrame` + mover/team + `ClientEndFrame` objects;
4. requires the `G_UpdateActorCorpses()` edge to disappear from the undefined
   symbol list while preserving unresolved script, actor-event and path
   services as visible integration work;
5. uploads the object and symbol reports as a clearly labelled NOT-APK
   artifact.

The Python regression checks both pointer-bound loops and the original
16-entry declaration. It is discovered by the existing
`test_iw3_android_*.py` preflight command.

## Verification boundary

This pass is a pointer-width correctness fix plus full-TU compile and
relocatable-link audit. It does not execute the corpse service, link the full
Android SP runtime, load a BSP/FastFile, render a frame, or prove touch-driven
weapon/actor gameplay. The JNI APK remains diagnostic. PR #4 must remain open
and unmerged until real ARM64 gameplay evidence exists.
