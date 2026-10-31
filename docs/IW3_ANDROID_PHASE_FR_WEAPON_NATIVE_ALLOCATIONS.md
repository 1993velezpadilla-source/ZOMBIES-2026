# Phase FR — original IW3 weapon allocation sizes on LP64 (2026-10-31)

## Scope and observed blocker
The authentic KisakCOD `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp` still contained 32-bit allocation sizes in the weapon-loading path. On Android ARM64, each `snd_alias_list_t*` is eight bytes, but `BG_RegisterSurfaceTypeSounds` allocated `0x74` (116) bytes for 29 entries and then wrote all 29 pointers (232 bytes). This is a concrete heap/hunk write overflow on LP64. `BG_LoadWeaponDefInternal` also allocated a fixed `0x878` bytes for a native `WeaponDef`, even though the structure contains pointers whose size changes with the target ABI.

## Implemented in the original engine
- Replace `Hunk_AllocLow(0x74u, ...)` with `Hunk_AllocLow(sizeof(*result) * 29, ...)` for the 29 native sound pointers.
- Replace `Hunk_AllocLow(0x878u, ...)` with `Hunk_AllocLow(sizeof(WeaponDef), ...)` for the native weapon structure.
- Preserve the existing sound-alias lookup, fallback behavior, cache, and maximum-16 list limit. No engine substitution, JNI diagnostic promotion, or main merge.

## Verification
- New `tests/test_iw3_android_weapon_native_allocations.py` extracts the **actual** `BG_RegisterSurfaceTypeSounds` body and runs it on an LP64 host with AddressSanitizer and UndefinedBehaviorSanitizer. The fixture checks all 29 slots, fallback for a missing surface alias, cache reuse, distinct surfaces, and the 16-list limit. It also asserts the source's `sizeof(WeaponDef)` allocation.
- Dedicated workflow `.github/workflows/iw3-weapon-native-allocations-host.yml` is named **NOT GAME** and prints explicit negative gameplay gates.
- [GitHub Actions run 41203304225](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41203304225) completed **success** on 2026-10-31 at 12:56 UTC. Inspected job 124543262280: `Ran 1 test in 2.805s`, `OK`, `IW3_ORIGINAL_SURFACE_SOUND_LP64_ALLOC_PASS`.
- Other workflows on the same head were still running or queued at inspection time; no full Android ARM64/gameplay claim is made from this host test.

## Still blocking actual gameplay
The **502** `weaponDefFields` entries still use original 32-bit structure offsets. `InitWeaponDef` and `ParseConfigStringToStructCustomSize` must be migrated against verified LP64 `WeaponDef` member offsets and pointer writes before loading actual weapon assets can be considered safe. This allocation correction **does not** validate the field layout. The native Android `Com_Init` boot path, map/fastfile loading, real renderer, touch-to-client loop, and gameplay/actors are still unproven. The JNI APK is diagnostic only.

`IW3_WEAPONDEF_FIELD_OFFSETS_LP64_VALIDATED=false`  
`IW3_REAL_WEAPON_ASSET_LOADED=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

Keep PR #4 open and unmerged.
