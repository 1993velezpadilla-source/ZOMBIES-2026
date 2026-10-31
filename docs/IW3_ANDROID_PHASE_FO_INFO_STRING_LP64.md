# Phase FO — original IW3 info-string pointer-width regression (NOT GAME)

Date: 2026-10-31 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`. No Godot or substitute engine.

## Baseline and verified blocker

At branch head `b45cec871ca449d7e619f85834d2c893a21a682d`, all 12 commit-associated CI workflows reported success. The authentic `universal/q_shared.cpp` ARM64 compile still emitted pointer-to-int narrowing warnings at lines in `Info_Validate`, `Info_SetValueForKey` and `ParseConfigStringToStructCustomSize`. Original source `Info_Validate` and `Info_SetValueForKey` cast the pointer returned by `strchr` to 32-bit `int` merely to test for existence. This is not LP64-safe, even if it usually appears to work.

The separate config parser problem is **more serious**: `weaponDefFields[502]` in authentic `bgame/bg_weapons_load_obj.cpp` has hard-coded 32-bit offsets (e.g. gunModel=12, gunModel2=16) and `ParseConfigStringToStructCustomSize` stores FX/XModel/Material/Sound pointers as `uint32_t`. Blindly replacing the writes with 8-byte stores would overwrite adjacent fields; it is **not** a valid fix without converting and verifying the full destination layout and the string-pointer fields. This pass does **not** claim that problem solved.

## Original-engine change

Changed only the five `strchr` existence checks in authentic `q_shared.cpp` to keep `const char *` results at their native width. The original branching, validation, sanitization and info-string serialization remain unchanged. No 32-bit ABI struct offsets were modified.

New regression `tests/test_iw3_android_cmd_info_lp64.py` extracts the two **verbatim original function bodies**, compiles them on a 64-bit host with UBSan and pointer-int-cast errors, and tests normal validation, rejected quotes/semicolons, value delimiter stripping, replacement, empty value, rejected invalid keys and oversize input. The helper stubs are test-only and are not linked into the engine or Android JNI.

The original `q_shared.cpp` full translation unit continues to be compiled as Android AArch64 ELF in `.github/workflows/iw3-command-full-arm64.yml`. The workflow now triggers for the new regression and emits `IW3_ORIGINAL_INFO_STRING_LP64_HOST_PASS` after the host tests.

## Evidence and unproven gates

Verified on code commit `1ac6125c20950b788728e3f1db4b1b5115ebbe35`: [GitHub Actions 41191504749](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41191504749) completed successfully on 2026-10-31. Inspected job `124509057411`: **29/29 host Python tests passed**, including two new LP64 tests, and the original full `q_shared.cpp` compiled/linked as Android AArch64 ELF with `Com_InitThreadData` resolved. The five `strchr` pointer-to-int warnings disappeared; four warnings in the **separate** `ParseConfigStringToStructCustomSize` remain at FX/XModel/Material/Sound pointer stores. This CI is a portability/relocatable-link audit, **not** engine runtime execution. Prior baseline: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41187285419 (success). No ARM64 engine execution, real map load, renderer frame, live touch gameplay or genuine playable APK is established by this pass.

`IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.

## Next critical work

1. Map the entire `WeaponDef` LP64 field layout and `weaponDefFields[502]` offsets, including all string pointers and special field callbacks, then add ABI-aware offsets with regression tests; do **not** apply pointer-size writes at 32-bit offsets.
2. Integrate authentic Android MAIN/profile/thread initialization and execute original `Com_Init` with real OS providers; `CL_InitRenderer()` remains unresolved.
3. Demonstrate real FastFile/map load, original renderer, original touch-to-usercmd and actual weapon/actor gameplay on ARM64 before declaring an APK playable.

PR must remain open and unmerged.
