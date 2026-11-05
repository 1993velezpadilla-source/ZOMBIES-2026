# TaCZ FPS system -> Voxel Sandbox / Luanti 5.18 engineering audit

> **Status:** Source-code reverse engineering completed at architecture level; **NOT** a
> completed port or permission to use TaCZ art. No upstream proprietary assets were
> copied into this branch. Does not alter any V1/V2/V3 Android build.

## 1. Exact upstream materials and licensing

- Source: https://github.com/MCModderAnchor/TACZ, official `1.20.1` branch (Minecraft Forge Java).
- Game content: upstream `src/main/resources/assets/tacz/custom/tacz_default_gun/` contains:
  models, textures, sounds, gun scripts and keyframe animations.
- Published README and CurseForge: **code GPL-3.0**; **assets CC BY-NC-ND 4.0**.
- GPL permits commercial use of covered source code, subject to the copyleft and
  source distribution requirements when conveying derivatives.
- **CC BY-NC-ND art cannot be put into our ad-monetized APK or repackaged/
  modified and redistributed merely by extracting or renaming it.**
  Independent artist permission would be required for protected art/animations/audio.
- The mod's general FPS *ideas and behavior* are what we are re-implementing.
  Do **not** copy its gunpack content or `.jar` resources into an APK.
- Project Aether material has separate unresolved license provenance. Do not
  silently use its weapon models or recordings in commercial distributions.
- Review proposed use of any GPL code with a license expert if proprietary
  distribution is planned. Our intent here is original implementation using
  *technical understanding*, not a verbatim code transplant.

## 2. Concrete Java source architecture checked (upstream branch `1.20.1`)

| Function required by our phone-first FPS | Relevant official source | Luanti destination |
| --- | --- | --- |
| Camera-space gun placement, ADS smoothing, recoil and sway | `src/main/java/com/tacz/guns/client/event/FirstPersonRenderGunEvent.java` | Luanti `src/client/camera.cpp`: **native FPS viewmodel camera** rather than default low-right wield mesh |
| Loading and drawing model parts | `src/main/java/com/tacz/guns/client/model/BedrockGunModel.java` | glTF/OBJ with explicit bones/piece transforms; separate first-person pass |
| Animation plans, blending and keyframe tracks | `src/main/java/com/tacz/guns/api/client/animation/AnimationController.java` | Native Luanti glTF animation and a small event scheduler |
| Per-gun animation state logic | `src/main/java/com/tacz/guns/client/animation/statemachine/GunAnimationStateContext.java` | Luanti mod state machine, server-authoritative ammo, client visual cues |
| Author-authored gun behavior and reload times | `src/main/java/com/tacz/guns/resource/GunPackLoader.java` and separate data definitions | **Our own** JSON configs and loader, **not** original packaged TaCZ assets |
| The first-person ADS-specific structure | `src/main/java/com/tacz/guns/client/resource/pojo/display/gun/AdsPath.java` and `FirstPersonRenderGunEvent.java` | `hipfire` / `aim` transforms in the custom camera, interpolated at 60 FPS |
| Sound cues | `src/main/java/com/tacz/guns/client/sound/GunSoundInstance.java` and animation sound channel classes | Per-weapon OGG mapping with events synchronized to reload keyframes |
| General future weapon plugins | `src/main/java/com/tacz/guns/api/item/IGun.java` and gun-pack indexes | Our reusable Luanti `weapon_core`, weapon-specific data and licensed models |

**Do not port Forge dependencies**. The Minecraft rendering event, Forge hooks,
Mojang `PoseStack`, data registry, Java graphics bindings and Minecraft server
packet classes are not usable inside the C++/Lua Luanti client.

## 3. Technical inspection of TaCZ's AK-47 asset *format* (no copying)

TaCZ's packaged AK references separate layers:
- `data/tacz/index/guns/ak47.json`: logical ID links data and display.
- `data/tacz/data/guns/ak47_data.json`: weapon behavior, including
  30-round magazine and 600 rounds/minute.
- `assets/tacz/display/guns/ak47_display.json`: model, textures,
  animation ID, state machine and separate sound-event IDs.
- `assets/tacz/animations/ak47.animation.json`: bone keyframes and animation
  sections, including hand position/rotation and camera channels.
- `assets/tacz/geo_models/gun/ak47_geo.json`: **artist-made geometry**.
- `assets/tacz/tacz_sounds/`: **artist-made audio**.

This decomposition is suitable for an original, extensible **weapon-pack data
format**. The original JSON animation, geometry, graphics, voice and sound
content are **not** licensed for redistribution in commercial Voxel Sandbox.

## 4. Current Voxel Sandbox Android evidence (user-tested)

- V2: functioning flat creative maps and red limits, save/reopen, around 59 FPS
  on Pixel Fold's outer screen. Preserve V2 untouched.
- V3: inventory, ammo and audio logic are present, but first-person GLB was invisible.
- V3.1: native mesh node makes model visible, but it appears too small and
  rotated/positioned at the screen's bottom right. **This is a camera-wield
  placement issue, not a successful FPS gun.**
- Luanti's upstream `src/client/camera.cpp` uses generic wield position
  `(55, -35, 65)` and orientation `(-100, 120, -100)` degrees. Those are intended
  for tools/blocks, **not ADS rifle ironsight alignment**.

## 5. Recommended implementable port (start with one gun, not thirty)

1. **Render isolation:** For our AK only, replace the generic first-person
   wield placement with a dedicated camera-space `hipfire` matrix. Re-use
   V3.1's original 47-part model. Set up a render probe for Android.
2. **ADS:** Define a true `aim` transform with the rear notch/front post
   aligned against the screen crosshair. Interpolate between the two
   transforms, synchronized with FOV.
3. **Reload:** Use our own glTF rig (existing original V3 asset) to animate
   magazine, bolt and hands; synchronize existing CC0 audio by keyframes.
   The original native static OBJ cannot physically animate magazine bones.
4. **Weapon-core data:** Separate per-gun stats and sound names into JSON/Lua,
   then expand only once gun 1 works in screen captures and physical tests.
5. **Licensing gate:** Before adding any external model/audio/animation,
   establish explicit permission for modification, redistribution and
   ad-supported commercial use; log origin and license.

### Acceptance tests on *real* Android (never infer from CI alone)
- Camera HIP: right-hand grip at right lower third, left support under
  handguard, barrel points toward reticle; no tiny horizontal gun.
- ADS: iron sights center, clear view through aligned sight; no two-hands-on-wheel.
- FIRE: muzzle motion visible, CC0 AK shot, ammo decrements once per shot.
- RELOAD: visible curved mag moves out/in, bolt moves, hands track,
  sound aligned, ammo replenishes at completion.
- Equip, unequip, reload, map save/reopen and 60 FPS-ish idle performance on
  actual phone; no touch conflicts or disappearing world boundaries.

## Honest status

This branch **documents verified source entry points and the legal/technical
boundaries**. It does not contain a TaCZ asset rip, APK, working custom FPS
camera code, or proof that 3D animations have run on Android. Implement that
in a *separate* Android iteration only after the graphics path is validated.
