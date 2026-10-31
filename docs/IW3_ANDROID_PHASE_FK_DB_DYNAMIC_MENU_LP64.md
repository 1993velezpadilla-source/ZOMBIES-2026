# Phase FK — authentic IW3 menu asset pointer-width correction

Date: 2026-10-31. PR #4 / `feature/iw3-native-android-arm64-20261025`. **NOT A GAME OR PLAYABLE APK.**

## Blocking original-code defect

`DB_DynamicCloneMenu` in `third_party/KisakCOD/src/database/db_registry.cpp` treated a `menuDef_t` as `XModelPieces[]`, then traversed menu item pointers with hard-coded `4 * index` strides. Those decompiler offsets assume 32-bit Windows layouts. On Android ARM64, `XModelPieces` occupies 24 bytes rather than 12, and pointers occupy 8 bytes, so the old code could read or write unrelated memory while cloning menu assets. This directly affects the genuine FastFile asset database/UI path, not a diagnostic JNI mock.

## Implemented on the original engine

- `baa2818c70af036b97e2b245f2a1ba181e4220fa`: restore the full original database translation unit and replace only the actual function definition with typed `from.menu`, `to.menu`, `menu->items[index]`, `item->window`, and `menu->window.staticFlags` accesses. Reject null menus/lists and negative counts. Preserve name matching, dynamic-flag transfer, and `DB_RemoveWindowFocus` behavior.
- `7a0a9424b2f14fa094e5ee1439c2a4aa93b41b62`: `tests/test_iw3_android_db_dynamic_menu_lp64.py` extracts the **original** function body and executes it against independent 64-bit menu fixtures under AddressSanitizer/UndefinedBehaviorSanitizer. Cases include matched and unmatched names, null items, static flags, focus clearing, and invalid menu pointers.
- An intermediate source edit (`cd0e6c1`) accidentally matched the forward declaration instead of the definition and removed unrelated functions. It was **immediately superseded** by `baa2818c`, which restored the full source and targeted the exact definition. CI must validate the corrected branch head, not that intermediate commit.

## Evidence and remaining gates

The `IW3 ORIGINAL SOURCE Android ARM64 math port (NOT APK)` workflow runs `python3 -m unittest discover -s tests -p 'test_iw3_android_*.py' -v` and compiles the complete authentic `db_registry.cpp` as an AArch64 object. Review its new run for the marker `IW3_ORIGINAL_DB_DYNAMIC_MENU_LP64_PASS` and for `IW3_ORIGINAL_DB_REGISTRY_AARCH64_OBJECT_PASS`. **No CI success is claimed by this document until the run is inspected.**

The original Android bootstrap, `Com_Init`/`Cmd_Init`/`Dvar_Init`/`FS_Startup` execution, real licensed FastFile/map loading, renderer/backend, client touch consumption, and live weapon/actor gameplay remain unproven. The JNI APK is diagnostic, `IW3_PLAYABLE_APK=false`, and PR #4 must remain open and unmerged.
