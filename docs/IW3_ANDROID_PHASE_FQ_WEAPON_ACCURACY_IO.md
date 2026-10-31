# IW3 Android Phase FQ — authentic weapon accuracy file I/O integrity (NOT GAME)

Date: 2026-10-31 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Real source and failure mode

Edited **only the authentic KisakCOD IW3** `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp`, function `G_ParseWeaponAccurayGraphInternal`. This path is used when loading weapon accuracy graph files through the original `FS_FOpenFileByMode` / `FS_Read` / `FS_FCloseFile` services. The original code treated the declared file length as proof that both reads succeeded. A short header read could cause a magic comparison against uninitialized stack data; a short body read could feed incomplete graph data to the original parser. A filename truncated by `snprintf` could select the wrong asset. Files shorter than the magic header were not rejected before reading.

## Concrete changes

* Reject negative/truncated `snprintf` paths **before opening** a weapon asset.
* Reject files shorter than the `WEAPONACCUFILE` magic header and require the **actual** header read count to match.
* Require the **actual** graph-body read count to match the declared remaining bytes.
* On all new failure paths, close any opened original filesystem handle and return failure without invoking the graph parser.
* Preserve existing original weapon-type handling, parser, 8192-byte graph limit and successful read behavior.

Source commit: `2d82e02196fe8bf226253ffac47b710c6919c0ee`. Test commit: `04cee5bce7d7701f6a628832343ff05483b351d5`. CI commit: `ffa894faa03b7eff44c1b7627d6ccd849e8abb61`.

## Verification

[Original weapon accuracy host sanitizer CI run 41198589494](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41198589494) succeeded, job `124529679548`, on the PR merge ref containing the above commits. **2/2 Python unittest cases passed**. The new test extracts the **verbatim original** `G_ParseWeaponAccurayGraphInternal` function and compiles/runs it with `-fsanitize=address,undefined` and leak detection. Test-only filesystem and parser providers cover valid files, short files, short header reads, short body reads, invalid magic, oversized body, truncated paths, bypass for irrelevant weapon types, empty graph names and parser rejection. Marker: `IW3_ORIGINAL_WEAPON_ACCURACY_FILE_IO_PASS`. The existing real graph knot parser regression also passed. This is **host-executed original code**, not Android device gameplay.

Other CI workflows for this branch are independently running and must not be assumed successful until their logs conclude.

## Remaining blocking work

The **critical ARM64 weapon ABI blocker remains**: the original `weaponDefFields[502]` table contains 32-bit offsets into `WeaponDef`, and the config parser has pointer-width assumptions. No blind widening of pointer writes is acceptable before mapping/verifying the complete LP64 layout and callback field semantics. Original `Com_Init` has not been shown executing in a functional Android process. The Android renderer, genuine map loading, original touch-driven client, weapons and actors have not been demonstrated in one device-executed game.

**`IW3_PLAYABLE_APK=false`**. A diagnostic JNI APK or host regression is not a playable engine. Do not merge PR #4 into main.
