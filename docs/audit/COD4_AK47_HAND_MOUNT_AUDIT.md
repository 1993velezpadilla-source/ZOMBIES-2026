# COD4 AK-47 voxel + original viewhands — real mounted-pose gate

Date: 2026-11-05. Branch `feature/iw3-ak47-voxelize-all-xanim-20261105`, PR #14.

## What was actually executed

- Re-extracted COD4 user-provided source from privately staged split 7 GB archive using OpenAssetTools.
- Selected `viewmodel_ak47_mp_lod0.glb`. Converted source into skinned cuboids using independent toon materials (no COD4 texture redistribution).
- Loaded the source XANIM tracks for both rifle and `viewmodel_base_viewhands_lod0.glb`.
- Added a real glTF pose evaluator: interpolated bone tracks, inverse bind matrices and per-vertex skinning.
- Added `render_mounted_viewhands.py` to render **the rifle AND both viewhands in the same frame** during idle, fire, fire ADS, reload and empty reload. Saved 21 real frames.
- Tested three bone-mount strategies: relative source delta, the prior direct identity-child path, and **true original `tag_weapon`→`tag_ak47_mount` paired mounting**. The latter is now the default conversion diagnostic.
- Produced comparative screenshots `ak47_tag_strategy_comparison.png`, full original source XANIM timings and numerical distance diagnostics.
- Green: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42121894415

## Hard evidence (not marketing)

**New root-cause discovery:** the AK GLB does **not** contain a bone literally named `tag_weapon`, but it **DOES** contain its proper COD4 rifle-specific attachment `tag_ak47_mount`. The hands skeleton contains `tag_weapon`. The earlier proof incorrectly treated the absence of the generic name as absence of a rifle anchor.

The proper skeletal alignment follows two genuine original transforms (at each XANIM time):
`AKworld = HandsWorld(tag_weapon) × inverse(RifleWorld(tag_ak47_mount))`.

Original source also contains rifle `tag_flash`, `tag_clip`, `j_bolt2`, and `tag_reflex_sight`; `tag_iron_sight` is absent. The hands `tag_camera` exists but stays at (0,0,0), so it alone does not provide a correct camera-to-gun depth. Independent original `tag_flash` and mount positions imply a forward muzzle vector ~`(+0.9978, -0.0657, -0.0007)` in the neutral mounted pose. A camera positioned at source origin can be INSIDE the rifle mesh: a giant flat gray surface in perspective proves why our previous viewmodel mounting was unusable.

Selected proximity measure = median sampled distance from hand surface vertices to nearest rifle vertices divided by rifle extents (lower can indicate proximity but NOT anatomically correct grip).

| Original action | Prior relative delta | Prior direct attachment | **Correct source-native tag pair** |
| --- | ---: | ---: | ---: |
| idle | 0.1700 | 0.1209 | **0.1124** |
| reload at 50% | 0.2289 | 0.3184 | **0.2333** |
| reload empty at 50% | 0.1937 | 0.2121 | **0.2355** |

The real dual-tag pairing has zero mathematical anchor-position error and improves idle geometric proximity. **It still does not certify the hand grip:** the reload distance can increase legitimately as the off-hand moves to the magazine, and this whole-arm average is a poor measure of fingertip/magazine contact. In our original camera-origin screenshots the gun can completely occlude the screen; we now render both true tag-based muzzle direction and a geometrically measured rear camera diagnostic. The underlying animation and world-view orientation still require FPS device validation.

**Structural GREEN != working reload.** The current rest-pose and coordinate handling for the hand bones is not visually correct. Hands remain oversized/rotated, and the rifle is insufficiently detailed for a release.

## Next engineering gates

1. Verify the **already discovered** authentic `tag_weapon`→`tag_ak47_mount` transform on the Android runtime, not the incorrect identity-child placement. Use the muzzle and camera tag diagnostics to establish a correct first-person depth without burying the camera in the stock.
2. Confirm separate bolt and magazine bones actually transform the corresponding cuboid geometry, and match each original XANIM notetrack to visible action.
3. Compare idle/hip/ADS axis and camera projection from first-person (with real viewhands) and only accept rendering when grip/magazine motion is visually plausible at 0%, 25%, 50%, 75%, 95%.
4. Re-author visually recognizable AK-family cuboid rifle and hands with properly weighted block segments before using in a published/monetized game. COD4-derived resources cannot be shipped publicly without permission.

No APK has been created from this experiment. Commercial licensing remains uncleared.
