# COD4 Arsenal V13 — Recovery and Android weapon selector hotfix

## Preserved binary identity (not uploaded to Git)

- Name: `COD4-ALL-WEAPONS-ARSENAL-V13-ARM64.apk`
- **Version:** V13, Android `versionCode=5180018` (**NOT** V13.1 `5180019`)
- **File size:** 462,304,888 bytes
- **SHA-256:** `84ec47f43eddebf0be30aad8116983ae48178527ba3b54ce333c2419bd474daa`
- The original APK has been recovered from the owner's ChatGPT Library and must be retained unchanged.
- The archive contains `assets/COD4-ARSENAL-V13-SOURCE.zip` with the original V13 source files.
- GitHub's ordinary repository files cannot hold a 462 MB APK. This branch **does not contain the APK**; a GitHub Release asset (or external artifact storage) is needed for the binary. Do not label this repository as hosting the APK yet.

## Fix developed from the real V13 Lua source

The original `sandbox/luanti/ak47_hd_android/arsenal.lua` registered an `image_button` inside a `scroll_container` and checked `fields.quit` and `fields.category` before `pick_<weapon>`. The category dropdown may be submitted together with a button click, causing the pick to be ignored on mobile.

**Patch:** `v13-selector-mobile.patch` (apply to the extracted `COD4-ARSENAL-V13-SOURCE.zip` with `patch -p1`):

- Use a paginated catalogue with **8 large plain buttons per page**, avoiding scroll-container tap/drag ambiguity.
- Process `pick_<weapon>` **before** any concurrent dropdown, quit, or page event.
- Maintain the active category/page correctly.
- Equip the clicked weapon into the selected hotbar stack; if the inventory is full, allow replacement of another selected firearm, **never silently delete a non-weapon item**.
- Confirm that the selected stack actually contains the chosen weapon.
- Display a clear inventory-full message when a nonweapon blocks replacement.

## Checks and constraints

- **Passed:** `texlua --luaonly sandbox/luanti/ak47_hd_android/test_arsenal.lua arsenal_catalog.lua` after patching, using the exact V13 `arsenal_catalog.lua` extracted from the APK. This verifies 26 COD4 weapon definitions plus AK47 and M9 inventory, firing, reload, attachment, category, page, and simultaneous `pick+category+quit` behavior in a Lua mock.
- **Not done:** Android APK rebuild, on-device touch test or end-to-end player acceptance. The current APK remains the unmodified **old V13**. No claim that the fixed selector is deployed.
- Do **not** merge public game asset files or signing keystores into the repository unless their redistribution permission has been independently checked.

Upstream follow-up: [issue #18](https://github.com/1993velezpadilla-source/ZOMBIES-2026/issues/18) for V13.1 APK `5180019` recovery. Keep V13 and V13.1 separate.
