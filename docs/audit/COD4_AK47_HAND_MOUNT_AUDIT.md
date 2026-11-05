# COD4 AK-47 voxel + original viewhands — real mounted-pose gate

Date: 2026-11-05. Branch `feature/iw3-ak47-voxelize-all-xanim-20261105`, PR #14.

## What was actually executed

- Re-extracted COD4 user-provided source from privately staged split 7 GB archive using OpenAssetTools.
- Selected `viewmodel_ak47_mp_lod0.glb`. Converted source into skinned cuboids using independent toon materials (no COD4 texture redistribution).
- Loaded the source XANIM tracks for both rifle and `viewmodel_base_viewhands_lod0.glb`.
- Added a real glTF pose evaluator: interpolated bone tracks, inverse bind matrices and per-vertex skinning.
- Added `render_mounted_viewhands.py` to render **the rifle AND both viewhands in the same frame** during idle, fire, fire ADS, reload and empty reload. Saved 21 real frames.
- Tested two distinct bone-mount strategies: (1) maintaining imported rifle origin while following movement of source hands `tag_weapon`; (2) direct `tag_weapon` mounting equivalent to Godot `BoneAttachment3D` with weapon child transform identity.
- Produced comparative screenshots `ak47_tag_strategy_comparison.png`, full original source XANIM timings and numerical distance diagnostics.
- Green: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42121894415

## Hard evidence (not marketing)

The AK GLB **does not contain its own `tag_weapon`**, while the hands GLB does. Thus exact dual-anchor alignment cannot be claimed; we can only test alternatives.

Selected proximity measure = median sampled distance from hand surface vertices to nearest rifle vertices divided by rifle extents (lower can indicate proximity but NOT anatomically correct grip).

| Original action | Hands source tag delta (no rifle tag) | Direct source hands tag attachment |
| --- | ---: | ---: |
| idle | 0.1700 | 0.1209 |
| reload at 50% | 0.2289 | 0.3184 |
| reload empty at 50% | 0.1937 | 0.2121 |

Directly attaching the rifle to the source `tag_weapon` moves the rifle closer to the hands in idle but **makes the reload worse** according to this coarse metric and the captures; this is not an acceptable gameplay fix. At 50% reload, the magazine is visually disconnected / there is not a coherent grip.

**Structural GREEN != working reload.** The current rest-pose and coordinate handling for the hand bones is not visually correct. Hands remain oversized/rotated, and the rifle is insufficiently detailed for a release.

## Next engineering gates

1. Inspect source bind-pose and original IW3 animation local-vs-world coordinate relationship, not hand-coded XYZ guesses. Resolve original `tag_weapon` transform with inverse bind matrix and bone hierarchy.
2. Confirm separate bolt and magazine bones actually transform the corresponding cuboid geometry, and match each original XANIM notetrack to visible action.
3. Compare idle/hip/ADS axis and camera projection from first-person (with real viewhands) and only accept rendering when grip/magazine motion is visually plausible at 0%, 25%, 50%, 75%, 95%.
4. Re-author visually recognizable AK-family cuboid rifle and hands with properly weighted block segments before using in a published/monetized game. COD4-derived resources cannot be shipped publicly without permission.

No APK has been created from this experiment. Commercial licensing remains uncleared.
