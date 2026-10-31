# IW3 Android Phase FT — original weapon asset I/O integrity (2026-10-31)

**Status: NOT A GAME. IW3_PLAYABLE_APK=false.** All modifications are to the authentic KisakCOD IW3 source in `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp`. No Godot or substitute engine was used.

## Blocker and changes

The genuine `BG_LoadWeaponDefInternal` file loader trusted the file length returned by `FS_FOpenFileByMode`, did not check either `FS_Read` return value, and could subtract the magic-header length from a shorter file. This could cause a negative read length or an out-of-bounds body terminator, or pass partially initialized weapon configuration data to `Info_Validate`. It also used a fixed-size path formatting call without rejecting truncated weapon paths.

The function now (1) rejects path formatting failures/truncation before opening a file; (2) rejects files shorter than the `WEAPONFILE` magic header and requires the entire header to be read; (3) requires the entire bounded body to be read; and (4) closes the opened file on each early error path. The existing `0x2800` body-size limit and original config parser are preserved.

## Executable regression evidence

`tests/test_iw3_android_weapon_file_io.py` extracts the **actual function body** using the repository's `function_source` helper, compiles it with `g++ -fsanitize=address,undefined` and runs host LP64 cases with test-only filesystem and asset service providers. The regression covers a valid weapon header/body, too-short reported file, short header read, short body read, incorrect magic, oversized reported body, truncated path, invalid info, parser rejection, and parser success. Every opened handle is checked for proper closure.

Workflow: [IW3 original weapon accuracy graph host sanitizers, run 41212309738](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41212309738), **success**, inspected 2026-10-31. The log reports 2/2 previous accuracy tests and 1/1 new weapon-file test passing, including `IW3_ORIGINAL_WEAPON_FILE_IO_PASS`. The test is wired to the workflow for subsequent changes.

Commits:
- `82cb6ecb36722884db1c47a3e4d937c938a6006a` — authentic weapon loader correction.
- `f313a2e236a7f68f7693936b83bf7b2035d60774` — extracted-function sanitizer regression.
- `f99bf7777ace54b1f6b87cdd5871fc91b4bae8b6` — CI wiring.

## Remaining critical gates

The 502-entry `weaponDefFields` table still contains Windows x86/32-bit byte offsets. On ARM64, native `WeaponDef` pointers and alignment change the layout; **this test does not validate any of those offsets or demonstrate a real weapon file load**. The generic config parser's 32-bit pointer conversions also remain unsafe. Do not claim safe Android weapon parsing until a complete verified native offset map and pointer-width-aware assignments exist, followed by genuine weapon-asset loading tests.

No proof yet of Android `Com_Init` runtime integration, genuine map/asset loading, renderer frame, original client-loop touch processing, or gameplay/actors/weapons. Diagnostic JNI and isolated host functions do not satisfy the playable-APK requirement. Keep PR #4 open and unmerged.
