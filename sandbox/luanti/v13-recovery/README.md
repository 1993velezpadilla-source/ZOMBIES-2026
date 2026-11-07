# COD4 Arsenal V13 — Original backup identity and mobile selector hotfix

## Original APK (preserved unchanged)

- Filename: `COD4-ALL-WEAPONS-ARSENAL-V13-ARM64.apk`
- Version: **V13**, `versionCode=5180018`, app ID `com.xziel.voxelsandbox.arsenalv0013`. **Not V13.1 (5180019).**
- Size: **462,304,888 bytes**
- SHA-256: `84ec47f43eddebf0be30aad8116983ae48178527ba3b54ce333c2419bd474daa`
- Recovered original retained in the user's ChatGPT Library; original source ZIP included inside `assets/COD4-ARSENAL-V13-SOURCE.zip`.
- **Not hosted as a GitHub binary:** >100 MB ordinary Git file limit, and this GitHub connector does not support release binary upload. This repo records provenance and patch text, *not* the 462MB APK file.

## Experimental V13 selection-hotfix APK (generated separately)

- Filename: `COD4-ARSENAL-V13-SELECTOR-HOTFIX-ARM64.apk`
- Version remains **5180018** with the same app ID (this is a hotfix of V13, **not** the lost V13.1).
- Size: **462,351,759 bytes**
- SHA-256: `f6bda43adf48bdbdf84b2a09c3f4cffdd09cd7c7c890627b9edb57a12dbe80a3`
- Exactly **one changed game file** in the nested Luanti asset archive: `games/voxelibre/mods/ak47dev/arsenal.lua`; source ZIP embedded was refreshed, and package signatures rebuilt.
- Signed with the **same private signing key** as the original; v1 JAR verification passed and v2 certificate fingerprint `271890e4f8c663e7ce83cb9f0470f31685ae46264f8304b915dfab77d15f36a5` matches the original.
- Custom v2 signature block integrity/digest checks passed. All 207 stored ZIP entries verified **4-byte aligned**, including `resources.arsc`; 412 outer ZIP entries pass CRC.
- **Not Android-device tested**: no physical-phone selector/touch validation and no Android SDK `apksigner verify` available in this environment. Do not call it a confirmed functional APK. **Also not hosted in GitHub:** retained as an output artifact in the owning conversation.

## Selector changes

Patch: `v13-selector-mobile.patch` applied from the original V13 source ZIP root using `patch -p1`. Test patch: `v13-selector-tests.patch`.

- Replace scrolling `image_button` targets with 8 large plain touch buttons per page; Prev/Next navigation.
- Handle `pick_<weapon>` before concurrent dropdown or quit fields.
- Keep category/page state; verify the selected weapon after equipping.
- If inventory full, replace selected firearm (all guns remain available via catalogue), but do not silently delete non-weapon items.
- Display an inventory-full message when a nonweapon blocks replacement.

## Tests

From the extracted source ZIP with the patch applied and the `arsenal_catalog.lua` extracted from the original V13 APK:

```bash
texlua --luaonly sandbox/luanti/ak47_hd_android/test_arsenal.lua arsenal_catalog.lua
# ARSENAL_PASS: firearm selection and Android touch conflict handling,
# full inventory and page navigation
```

Host test confirms all 26 COD4 gun profiles, along with the legacy AK47/M9, normal weapon functions, attachments, inventory-full swap, concurrent pick+category+quit, and page navigation.

**Remaining:** install and test on actual Android phone. This host test does **not** validate actual UI touch dispatch, performance or sound.

Related V13.1 recovery: [issue #18](https://github.com/1993velezpadilla-source/ZOMBIES-2026/issues/18). Keep V13 and V13.1 separate. No private signing keys or binary assets are added to this public branch.
