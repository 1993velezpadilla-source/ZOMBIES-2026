# COD4 AK47: native rig fields, original model attachment and fixed FPS rendering

The AK and viewhands now use the original IW3 runtime local transforms and
model assembly rule. The prior tag_weapon→tag_ak47_mount alignment was a
rejected hypothesis. The new path attaches the rifle's native model root to
the hands' tag_weapon, removes OAT's exported coordinate basis once, and
retains the original rifle and finger XANIM tracks.

## Source fields that must stay distinct

| Data | Authoritative source | Conversion |
| --- | --- | --- |
| Skin inverse binds and vertex coordinates | OAT GLB global bind matrices | Retained unchanged |
| Runtime local rest transforms | IW3 model.trans and model.quats | Captured directly by the pinned OAT converter |
| Named XANIM bone rotation | XAnimCalcParts | Absolute local quaternion; NO_QUAT is identity |
| Named XANIM translation | CalcSkelNonRootBones | Native model.trans plus animation delta |
| Weapon-to-hands attachment | CG_RegisterWeapon / ChangeViewmodelDobj | Gun model root under hands.tag_weapon |

The viewhands are the important counterexample: their native local translations
and glTF-derived bind translations differ by up to **16.59575 model units**.
For this AK rifle the maximum difference is below 0.000001. Consequently,
adding XANIM deltas to *glTF-derived* hand bind offsets is incorrect even
though adding them to *native model.trans* follows the engine. The exported
skin binds and native runtime rest transforms are independent inputs.

Primary references:

- [OAT model fields](https://github.com/Laupetin/OpenAssetTools/blob/v0.34.0/src/ObjWriting/XModel/XModelToCommonConverter.cpp.template): native localOffset/localRotation versus global baseMat.
- [OAT glTF writer](https://github.com/Laupetin/OpenAssetTools/blob/v0.34.0/src/ObjWriting/XModel/Gltf/GltfWriter.cpp): exports global frames and vertices through C=Rx(-90 degrees), then derives bind locals.
- [IW3 skeleton evaluation](https://github.com/SwagSoftware/KisakCOD/blob/master/src/xanim/dobj_skel.cpp): CalcSkelNonRootBones adds model.trans before parent transformation.
- [IW3 animation evaluation](https://github.com/SwagSoftware/KisakCOD/blob/master/src/xanim/xanim_calc.cpp): XAnimCalcParts identity rotation and zero translation semantics.
- [IW3 weapon assembly](https://github.com/SwagSoftware/KisakCOD/blob/master/src/cgame/cg_weapons.cpp): CG_RegisterWeapon attaches handXModel first and gunXModel under tag_weapon.

## Executed verification

Built the pinned OAT source commit `28b14ea0ee41844cfad9875176f9dc693db045cf`
for Linux x64 with a small private native-local sidecar patch. Extracted the
user-provided common_mp fastfile with **0 warnings and 0 errors**. Its weapon
definition confirms viewmodel_ak47_mp, viewmodel_base_viewhands,
viewmodel_ak47_reload and viewmodel_ak47_reload_empty.

Actual conversion: 891 rifle cuboids, 1,063 hand-only cuboids, 9 native rifle
joints and 71 native hand joints. Native sidecars and all model/keyframe
buffers remain private scratch data. Only raster previews and non-reversible
metadata are uploaded. The workflow caches only the open-source exporter
binary, never source game assets.

Seven regression tests cover native/glTF kinematic equivalence, independent
runtime versus bind transforms, explicit NO_QUAT, single-basis model
attachment, Y-up projection and near clipping, timeline-aware framing and GIF
time. The batched rasterizer also matched the old renderer's interior pixels
exactly on the original synthetic test model.

The final actual-source pass rendered **117 frames**. Normal reload has
**67 samples at approximately 24 fps**, source duration **2.76666665 s**, and
encoded GIF duration **2.77 s**. Empty reload is sampled at approximately
12 fps. One fixed perspective is used across every action; no per-frame
recentring follows the magazine.

The review camera is explicitly calibrated, not the original game camera:
position (-16,0,-6), +X forward, Y up, horizontal FOV 95 degrees. It was selected
from a local 720-configuration inspection and then checked across 38 action
poses and every rendered frame. The lowest in-view fraction among sampled
receiver/handguard/barrel vertices was **0.97597**. Stock and detached magazine
are excluded from this framing criterion and may leave the viewport. Full-mesh
visibility is reported separately. Native-origin camera mode remains available
as an explicit comparison.

This verifies source conversion and produces reviewable real geometry and
animation. Finger contact throughout all reload phases, iron-sight ADS and
Android gameplay remain unapproved. No APK has been produced by this branch.
