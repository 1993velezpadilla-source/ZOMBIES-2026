# IW3 Android Phase FU — native weapon field offsets and full-width asset pointers

Date: 2026-10-31. PR #4, branch `feature/iw3-native-android-arm64-20261025`.
Baseline before this pass: `59c2dc994fe50fa9282efb8d2b1248f16b90b98c`.

## Original engine changes

- `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp`: all **502** `weaponDefFields` entries now use C++ `offsetof(WeaponDef, member)` (including indexed array members) instead of Windows 32-bit byte literals. Mapping was derived from all 363 declarations in the authentic `WeaponDef` and cross-checked against the canonical 502-name/type/legacy-offset fixture. The original structure measures 2,168 bytes under 32-bit and 2,832 bytes under Android LP64; those sizes agree with the source's `static_assert` contracts. `InitWeaponDef` now applies offsets to the object base.
- `third_party/KisakCOD/src/universal/q_shared.cpp`: `ParseConfigStringToStructCustomSize` writes native-size FX, XModel, Material, and sound alias pointers via `memcpy(..., &pointer, sizeof(pointer))`. This avoids the four original `(uint32_t)pointer` truncations. The original registration functions and parser remain in use.
- During full-translation-unit AArch64 compilation, an actual compile failure was exposed: `ARRAYSIZE(string)` was undefined in `G_ParseWeaponAccurayGraphInternal`. The original source now uses `sizeof(string)` and an explicit signed bound comparison, with its existing file-I/O regression updated.
- The source-only offline schema exporter now distinguishes legacy 32-bit offset metadata from native `offsetof` expressions. The SP source gate recognizes the new declarations. The canonical legacy field names, types, and offsets are retained in `tests/fixtures/iw3_weapon_fields_legacy_offsets.tsv`.

## Evidence, with strict scope

1. **Host execution under AddressSanitizer and UndefinedBehaviorSanitizer:** both `test_iw3_android_weapon_field_offsets.py` tests passed. One compiles the original 502-entry table and authentic `InitWeaponDef` against an LP64 mirror, checking all 502 native offsets, string initialization and non-string sentinels. The other executes the authentic config parser with four full-width, high-address asset pointers and adjacent canaries. Markers: `IW3_ORIGINAL_502_WEAPON_FIELDS_LP64_PASS` and `IW3_ORIGINAL_ASSET_POINTERS_LP64_PASS`. [GitHub Actions 41219126614](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41219126614).
2. **Complete authentic translation units compiled to Android AArch64 ELF objects:** `bgame/bg_weapons_load_obj.cpp` and `universal/q_shared.cpp`, compiled with Android NDK `27.2.12479018` targeting API 26. The resulting symbol tables contain `BG_LoadWeaponDefInternal(char const*, char const*)` and `ParseConfigStringToStructCustomSize(...)`. Markers: `IW3_ORIGINAL_WEAPON_LOADER_FULL_TU_AARCH64_PASS` and `IW3_ORIGINAL_CONFIG_PARSER_FULL_TU_AARCH64_PASS`. [GitHub Actions 41219116198](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41219116198); artifact ID `13049316754` contains ELF objects and symbol lists. **These objects are not an APK.**
3. The first full-source compile failed on the previously unnoticed undefined `ARRAYSIZE` macro. It was corrected and the next AArch64 compile succeeded. Host-only regressions never implied this compile gate had passed.
4. The independent weapon accuracy file-I/O host sanitizer workflow passed after the `sizeof(string)` change. The broader Windows SP build and other Android integration workflows are separate gates; their status must be read from the latest CI, not inferred from the tests above.

## Outstanding proof gates

`IW3_PLAYABLE_APK=false`. No real Android process has been shown to run the integrated `Com_Init`/filesystem/bootstrap path. No genuine weapon file has been loaded through the original complete asset registration graph on ARM64. No map data load, original renderer frame, live touch consumption by the real client loop, or original weapon/actor gameplay has been demonstrated. Diagnostic JNI APKs and host fixtures do not count.

Next priority: link and execute the genuine bootstrap and asset graph, retaining unresolved original renderer and platform dependencies visibly (not stubbing them into a fake game). Specifically investigate `CL_InitRenderer()` and map/asset registration, then prove real device rendering and gameplay. Do not merge PR #4 into `main` until every gameplay gate is supported by execution evidence.
