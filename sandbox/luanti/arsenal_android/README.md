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
