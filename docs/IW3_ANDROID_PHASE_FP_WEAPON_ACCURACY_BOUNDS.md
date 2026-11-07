# Phase FP — original IW3 weapon accuracy graph bounds (NOT GAME)

Date: 2026-10-31 UTC. PR #4; branch `feature/iw3-native-android-arm64-20261025`. Original KisakCOD IW3 source only; no Godot or substitute engine.

## Baseline / blocker

The preceding branch head was `05760073d7b0a5c9a999d6d01bac40531e0989d1`. The original `bgame/bg_weapons_load_obj.cpp` function `G_ParseAIWeaponAccurayGraphFile` accepted an arbitrary declared knot count, indexed `(*knots)[2 * knotCountIndex]` as if the first 2-float row were a flat array, and checked the 16-knot capacity **after** writing the next pair. A declared zero count could reach `2 * knotCountIndex - 2`, and exactly sixteen valid pairs were incorrectly rejected by `>= 16` after the final write. This is a genuine original-engine weapon data safety/correctness issue, not evidence of Android gameplay.

## Original source change

Commit `79df5144beee83d68430ab8cdb12973f912fc414` updates the authentic function (no replacement implementation): reject counts <=0 or >16 before processing; check capacity before each pair; index the actual `float knots[16][2]` as `knots[index][0/1]`; and validate the last knot only after confirming a nonzero parsed count. It preserves the existing parsing/session and error reporting behavior. The valid 16-knot case is now accepted.

Test commit `f2675552fdf1f2f0f846de1d1b4cab55f088292a` adds `tests/test_iw3_android_weapon_accuracy_graph.py`, extracting the original function verbatim and executing it against minimal test-only parsing services under AddressSanitizer and UndefinedBehaviorSanitizer. Scenarios include two valid knots, sixteen valid knots, declared 0/-1/17/non-numeric, missing value, invalid last x coordinate, extra knots and a 17th pair. Canary values guard both sides of the actual 16x2 destination array. Workflow commit `d2e6b84a2fef4e64a490ce03cdfd64ef23f84328` adds `.github/workflows/iw3-weapon-accuracy-host.yml`.

## Verified evidence

[GitHub Actions run 41196604418](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41196604418), job `124523917495`: log at 2026-10-31T11:22:46Z reports `test_original_parser_accepts_16_and_rejects_invalid_knot_counts ... ok`, `Ran 1 test`, `OK`, `IW3_ORIGINAL_WEAPON_ACCURACY_GRAPH_BOUNDS_PASS` and `IW3_PLAYABLE_APK=false`. Host sanitizers exercise the original function body; this does **not** run the full original engine on Android. Other full CI workflows triggered by the source change must be assessed separately.

## Unresolved critical path

- `weaponDefFields[502]` still contains 32-bit structure offsets. The original config parser still writes FX/XModel/Material/Sound pointers through 32-bit slots; the complete `WeaponDef` LP64 layout must be mapped and validated before converting those stores.
- Authentic `Com_Init` has not been executed as an integrated Android engine process. The client renderer, real FastFile/map load, touch-to-usercmd and gameplay with original weapons/actors remain unproven.
- `IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`; `IW3_FS_STARTUP_RUNTIME_INVOKED=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_GAMEPLAY_PROVEN=false`; `IW3_PLAYABLE_APK=false`.

PR #4 must remain open and unmerged. A JNI diagnostic APK or host sanitizer pass is not a playable game.
