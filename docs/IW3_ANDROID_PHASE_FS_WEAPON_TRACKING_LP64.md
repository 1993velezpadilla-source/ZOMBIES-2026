# Phase FS — original IW3 weapon static tracking sizes on LP64 (2026-10-31)

## Observed portability defect

In `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp`, `TRACK_bg_weapons_load_obj` recorded nine original 32-bit byte counts. These counts are incorrect for native pointer arrays, `cspField_t weaponDefFields[502]`, and `WeaponDef` on Android ARM64. For example, the 502-field table was recorded as 6024 bytes (502 × 12) even though each `cspField_t` has an eight-byte name pointer on LP64; the 64-element animation-name pointer array was recorded as 256 bytes rather than 512. Incorrect memory-tracker accounting can hide the size of native data structures during porting.

## Implementation

Replaced the nine fixed-size `track_static_alloc_internal` calls with the authentic `TRACK_STATIC_ARR` / `TRACK_STATIC_DAT` macros from `qcommon/mem_track.h`. These macros pass `sizeof` the actual object, preserving original Win32 sizes while reporting native LP64 sizes. No renderer, gameplay, data format, engine, or JNI substitution was introduced.

The test `test_original_weapon_static_tracking_uses_native_object_sizes` in `tests/test_iw3_android_weapon_native_allocations.py` extracts the actual original `TRACK_bg_weapons_load_obj` function and compiles/runs it on an LP64 host with AddressSanitizer and UndefinedBehaviorSanitizer. It verifies all nine tracked addresses, names, types, and native object sizes. The existing workflow `iw3-weapon-native-allocations-host.yml` runs this test together with the original surface-sound allocation regression.

## CI evidence and scope

- Original code change: `3286ac12`.
- Test commits: `67dcf105`, `22ae62c4` (corrects the fixture's C++ macro continuation after an initial CI compilation failure).
- Dedicated workflow on `22ae62c4`: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41209764119 **completed success** on 2026-10-31 at 14:21 UTC. Inspected job `124562092879`: both original-source LP64 sanitizer regressions passed (`Ran 2 tests in 0.845s`, `OK`). This is host execution, not Android gameplay.
- Workflow marker update: `ae3b6436`, adds `IW3_ORIGINAL_WEAPON_STATIC_TRACKING_LP64_PASS` after both tests pass.
- Previous original code-only run: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41209666781 succeeded, but predates the new regression test.

## Remaining blockers — no playable APK

**The 502 entries still store original Win32 `WeaponDef` offsets.** Updating tracker sizes does not repair those offsets or the four pointer-to-`uint32_t` writes in the weapon parser. The next major porting task must establish a verified native `WeaponDef` field mapping and preserve the original asset parsing semantics, with executable tests on ARM64. Android `Com_Init` runtime integration, real map asset loading, renderer frames, touch consumption by the original client, and gameplay with weapons and actors remain unproven.

`IW3_PLAYABLE_APK=false`. This is an LP64 host regression on authentic source, **not** an Android game, an ARM64 gameplay test, or a reason to merge PR #4.
