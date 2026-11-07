# Classic Zombies stock-only configuration (2026-11-07)

This branch disables the in-game ATTACH/Gunsmith menu in the **Arsenal source-test mod**, while retaining the accessory source files for future PvP work. It does **not** rebuild or alter the earlier 462 MB FIX22 APK.

- Stock, non-suppressed firearm sounds and iron-sight ADS; no selectable red dots, ACOGs, barrels, grips or silencers.
- Previously saved `xz_ar_variant` metadata gets cleared to the weapon's original model, without changing ammunition.
- The attachment button is no longer granted and old saved hotbar buttons are removed on join; a hidden inert compatibility item prevents unknown-item fallout.
- Weapon picker, ammo box, reload and existing Arsenal code remain available for source-level testing.
- Zombies rounds, perks, wall buys, Mystery Box and Pack-a-Punch are **future gameplay tasks**, not claimed to be implemented by this source patch.
- Requires Lua regression and real Android testing before any release; no new APK built or uploaded here.
- Third-party COD4 game assets still require appropriate redistribution rights before a public release.

---

# Luanti Arsenal Android: evidence gate (not gameplay sign-off)

The Work screenshot reports **95 new models**, **28 weapons**, **184 configurations**, a universal ammo refill box and category picker. These counts are **targets** until the actual APK and its authoritative catalog can be read. The connected GitHub PR #15 currently holds a separate *private COD4 AK-47* implementation, not the 28-weapon Arsenal files.

Run the negative/positive verifier tests:
```bash
python3 -m unittest discover -s sandbox/luanti/arsenal_android -p 'test_*.py' -v
```
A GREEN here proves only that the *auditor* rejects certain bad inputs; it does **not** prove the real APK works.

For the real APK, export the complete catalog JSON from the actual source and keep it next to the APK in **private** storage. Exact asset paths must match entries inside `assets/assets.zip`. Example schema (a one-weapon EXAMPLE, not the claimed Arsenal manifest):

```json
{
  "schema_version": 1,
  "models": ["games/voxelibre/mods/arsenal/models/m9.glb"],
  "weapons": [{
    "id": "m9", "category": "pistol",
    "model": "games/voxelibre/mods/arsenal/models/m9.glb",
    "animations": ["idle", "reload"]
  }],
  "configurations": [{"id": "m9.base", "weapon": "m9", "attachments": []}]
}
```

The real catalog must contain every model, weapon and configuration; optionally list weapon textures and sounds as exact asset paths. Then run:

```bash
python3 sandbox/luanti/arsenal_android/audit_apk.py /private/Arsenal.apk \
  --catalog /private/arsenal_catalog.json \
  --expected-weapons 28 --expected-models 95 --expected-configurations 184 \
  --report /private/arsenal_audit.json
```

The audit inspects the *actual* signed-APK ZIP structure (but not the cryptographic signature), ARM64 libraries, Luanti nested assets, model files, GLB JSON mesh headers and declared animation clip names, duplicate definitions, configurations and resources. Do **not** use an invented catalog to claim those counts.

## Physical-device acceptance (not part of host-only GREEN)

- Install, launch, create/load world, switch between all seven categories (assault, pistol, SMG, shotgun, sniper, LMG, marksman) and equip every weapon.
- Test hipfire, iron sights, all ADS optics and reload both with and without rounds, including distinct reload sounds, shooting recoil and dry-fire click on empty reserve.
- Test ACOG for the black square when zoomed and for consistent FPS when firing; verify sniper scopes don't block controls or hitch on shoot.
- Test grenade launcher: visible projectile, realistic blast effect and damage; verify compatible accessory combinations and removal/re-attachment.
- Interact with the universal ammo box using weapons from every category; validate ammo and reserve accounting.
- Measure idle, hipfire, ADS, sprint, sustained automatic fire and zoom FPS on the actual Pixel Fold, including 1% low and median frame times; inspect screenshots/video.
- The gameplay modes are separate: **Classic Zombies has wall buys, Mystery Box, perks, rounds and Pack-a-Punch, but no custom Gunsmith/attachments**. Weapon XP unlocks parts for later PvP only.

## Rights and distribution

COD4 models/audio and other third-party weapon assets are not automatically licensed for public redistribution or monetization. Verifier GREEN does not change that. This branch's CI intentionally **does not publish or upload any APK or copyrighted assets**. Do not mark the APK installation, runtime or commercial rights as tested until there is direct evidence.

## Real Bridge V12 proof (2026-11-06; not the final Work Arsenal)

A separate byte-level inspection of the user's previously generated
`COD4-AK47-M9-BRIDGE-V12-ARM64.apk` (192,693,087 bytes;
SHA-256 `efea2535768d7e22439f7ea67607af7b10add9ee06d33f38e44c82265e178dbd`)
finds two registered tools: `ak47dev:ak47` and `ak47dev:m9`.
There are **22 GLB models**, **52 PNGs** and **20 OGGs** in that mod.
Most GLBs are accessory/model combinations, **not additional weapons**.
The shared `ammo.lua` registry is present, but this is not proof that
ammo-refill interaction works on Android.

To independently inventory a *real* Luanti Android package without using
the build's claimed model counts:

```bash
python3 sandbox/luanti/arsenal_android/scan_installed_apk.py \
  /private/Arsenal.apk --require-tools 28 \
  --output /private/actual_installed_inventory.json
```

The source scanner recognizes literal Lua tool registrations and the
`for item_name,definition in pairs(definitions)` registration used in V12.
Unknown Lua dynamic registrations are reported as unresolved, not counted
as a false pass. GLB animation names are inspected as declarations only;
actual animation playback still needs on-device testing.

The original Work session's stated **28 weapons / 95 models /
184 configurations** are *not* present in the known V12 APK. Those counts
remain unverified without the distinct Work-produced APK and authoritative
catalog. Search of the connected GitHub branch list/releases and Drive did
not locate that distinct APK. Do not replace it with a renamed V12.
