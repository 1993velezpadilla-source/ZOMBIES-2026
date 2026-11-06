# AK47 native ADS composition and centered preview

The sparse `viewmodel_ak47_ads_up` / `ads_down` clips animate only tag_ads.
Playing either alone reset every absent wrist/finger channel to native rest.
The new path layers these channels over the full idle or ADS-fire hand pose.
The rifle remains attached by its native root under hands.tag_weapon with
OAT_TO_NATIVE applied once. Every original source clip is retained unchanged.

Primary reference: [IW3 cg_weapons.cpp](https://github.com/SwagSoftware/KisakCOD/blob/master/src/cgame/cg_weapons.cpp),
WeaponRunXModelAnims and PlayADSAnim. The engine evaluates ADS as weaponPosFrac
while the current weapon animation continues. Raw up/down tracks last 13/30s;
the user's ak47_mp definition sets enter/exit to 0.25s. The preview samples the
entire original curve through that normalized fraction. ADS FOV is the source
definition's 50 degrees. The review's hip FOV is 75 degrees, interpolated linearly
during transitions; this does not claim to reproduce every IW3 FOV easing rule.

## Importable paired clips

Both private GLBs add the same names, with complete local TRS channels:

| Clip | Duration | Pose composition |
| --- | ---: | --- |
| ak47_hip_idle | 1s | Original idle grip |
| ak47_ads_enter | 0.25s | Idle plus normalized source ADS-up |
| ak47_ads_hold | 1s | Idle plus full ADS-up |
| ak47_ads_fire | 1/6s | Source ADS-fire plus full ADS-up |
| ak47_ads_exit | 0.25s | Idle plus normalized source ADS-down |

The rifle now has 44 clips, including its original 39. Hands have 54, including
their original 49. Base model node/skin/mesh definitions and all prior binary
data remain intact. Added composite keyframes stay private. Play the same
derived clip on both components. Complete channels preserve grip even in a
plain glTF player without a custom animation-layer mixer.

## Fixed alignment

Landmarks are selected from upward-facing quads on the emitted HD rear iron
shoulders and front post, within explicit AK47 model-space regions. These are
review-derived landmarks, not original engine sockets. One rigid correction
aligns their line with +X and places them at the optical center: approximately
0.113 degrees and translation (0.000124,-0.083486,-0.022782) model units.
Only the hands' root gets the correction, blended through ADS fraction; the
attached rifle follows. It is already baked into the five composed hand clips:
do not apply it again while playing those clips. The rear iron is assigned
steel UVs instead of inheriting the handguard's wood region.

Camera position remains (0,0,0), forward +X, up +Y across the sequence.
Projection's center offset is explicitly zero, so aim center is (width/2,height/2).
The rendered hold has under one pixel of projected landmark center error.
No per-frame recentering follows the rifle or suppresses source recoil.

## Validation and limits

Seventeen local tests pass, including independent sparse-layer kinematics,
standalone baked grip and enter/hold/exit boundaries, quaternion half turns,
embedded 512px GPU texturing and the existing native-rig regressions. The
actual-source ADS GIF contains 128 sampled poses over 2.12s, with paired
source-derived enter/hold/fire/exit and a fixed camera. Every frame samples
four textured rifle primitives and has nonempty rendered geometry.

The prior static painter's 65,000-triangle cap rejected the HD rifle before
other CI gates could run. Static previews now use the same depth renderer,
which was checked locally on all 144,134 triangles and the embedded texture.

This verifies composed viewmodel clips and technical renders. Android gameplay,
frame rate, every anatomical contact and the final in-engine camera remain
unapproved. No APK is produced. CI publishes only rasters and metadata; private
model/keyframe outputs are destroyed after the review gates.
