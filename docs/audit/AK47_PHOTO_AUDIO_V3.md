# AK47 photo/foley V3 — targeted Android test

PR #15 development branch \`feature/ak47-cod4-original-mesh-luanti-20261106\`.

## Changes motivated by actual 59–60 FPS Pixel Fold screenshots

1. **FPS only:** native Luanti GameUI minimal FPS text remains at top-right.
   The extra basic-debug \`pos/yaw/pitch/seed\` text is hidden.
2. **Two ammunition-driven reload sounds:** if \`ammo==0\` before reload,
   use the \`empty\` event. If \`ammo>0\`, use \`normal\`.
   Enforced in Lua and a test that fires 30 rounds before reloading.
3. **Audio pitch 100% native:** the public CC0 GunLib repository currently
   provides **one** \`ak47_reload.ogg\` AK reload recording, NOT two separately
   recorded reloads. Previous variants were slowed time-stretched copies of
   that recording, which sounded bad.
   - Normal: original-pitch recording begins at 0.28 seconds in the 83-frame
     \`viewmodel_ak47_reload\` animation (2.7667 sec).
   - Empty: original-pitch recording starts at 0.47 seconds, with a **separate
     CC0 bolt click** at 2.93 sec in the 106-frame
     \`viewmodel_ak47_reload_empty\` animation (3.5333 sec).
   - Both are independently exported OGGs; the magazine recording's PCM is
     unchanged. The short click may be sample-rate converted to match the
     magazine file without altering its pitch or real-world duration.
     No slowing down, phase-vocoder effects or tempo changes.
   - NOTE: a future recording with truly separate magazine/charging Foley
     would still be an upgrade. This fix does not pretend those recordings
     exist.
4. **Visible material detail:** original AK model polygons/animations are
   preserved, with UV projection bounded to each source primitive instead of
   squeezing tiny metal parts into a full-gun UV range. New atlas combines
   actual CC0 1K photo sources with baked detail and separate hand islands.
5. **Direct Android installer:** GitHub Actions uploads a signed \`.apk\`
   itself, without the old \`.apk.enc\` encryption layer. GitHub Actions
   presents its own standard ZIP wrapper; inside is a ready-to-install APK.

## Texture sources and licensing

Images are downloaded fresh on the CI worker and verified against the
publisher's MD5 hashes. No third-party COD4 diffuse textures are used.

| Material | CC0 publisher | Asset | Download map |
| --- | --- | --- | --- |
| Walnut furniture | Poly Haven | \`wood_table_001\` | 1K JPG Diffuse |
| Rusty steel receiver, barrel and magazine | Poly Haven | \`rusty_metal_04\` | 1K JPG Diffuse |
| Skin microvariation + cuff surface grain | Poly Haven | \`leather_red_02\` | 1K JPG coll1 |

Poly Haven source/license: https://polyhaven.com/license
Public endpoints: https://api.polyhaven.com/files/wood_table_001 ;
https://api.polyhaven.com/files/rusty_metal_04 ;
https://api.polyhaven.com/files/leather_red_02

**These CC0 surface maps may be reused commercially.** That does **not**
grant rights to use the COD4 3D model/XANIM in a distributed commercial
game. Replace these game-derived resources with owned or properly licensed
ones before shipping.

## Release gate

- Lua tests must distinguish normal and empty sound events by ammunition.
- Native sound generator must prove output tracks have exact animation timing,
  use the original sample PCM unchanged, and put bolt action only on empty.
- Image downloads must match the pinned CC0 hashes; no silent procedural
  fallback for the Android build.
- Source-based material UV tests, native Luanti GLB loader check and
  arm64 release build must pass, with Android signature verified.
- User/physical-device screens and FPS must be checked before claiming
  actual in-game visual/audio sync quality. CI GREEN is not that test.

## Photo-material refinement after real Pixel Fold reload screenshots

The 22/38 FPS readings in screenshots are **not** treated as a GPU performance regression: tester confirmed rapid consecutive Android screenshots while otherwise seeing 60 FPS. Do not optimize/reduce 3D detail based solely on those frames.

Visual bugs addressed:
- Rusty Metal 04 stays the source photo, but white paint-chip values are clamped and rust color is subtle on dark blued-steel base.
- Walnut base is darkened; image material is grain, not a bright orange diffuse coat.
- Per-triangle classification of glove/wrist versus hand was causing severe sawtooth black/skin seams. Both hands now use uninterrupted UV islands; each contains a smooth cuff-to-skin gradient. Geometry and XANIM are unchanged.
- Device playtest still needed: verify both hand poses and exact look against photos at 60 FPS.
