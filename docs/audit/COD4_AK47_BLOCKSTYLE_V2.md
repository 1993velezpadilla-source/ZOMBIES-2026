# AK-47 COD4 → cuboid FPS | visual quality pass 2

## Input provenance
- Original source family: `viewmodel_ak47_mp_lod0.glb`, selected from 22 extracted IW3 AK-47 LOD0 candidates.
- Real data comes from the owner's COD4 original split ZIP inside a private ephemeral GitHub Actions runner.
- Original model's materials include `mc/mtl_weapon_ak47`, `mc/mtl_weapon_ak47_misc_nocamo`, plus **ACOG and reflex optics**; the original v1 converter was including unrelated optic variants together.

## What changed in pass 2
- The converter now filters accessory-only mesh primitives (ACOG/reflex/lens/reticle) from the bare iron-sight version.
- Density is increased from 42 subdivisions to as high as 76, with bounded fallback levels to stay under 4,000 cuboids. Hands have their own bounded resolution.
- Procedural **adult-cartoon wood/steel/skin vertex palette** is embedded in the GLB as `COLOR_0`, so it is usable outside the screenshot utility; no original copyrighted texture is redistributed.
- Rendered raster previews read actual `COLOR_0` vertex values rather than painting the whole model gray.
- Skeleton hierarchy, source skin, inverse-bind matrices and matching named original XANIM channels are retained.
- V1/V2/V3/V3.3 original independently-authored weapon and APK remain untouched.

## Gates that cannot be silently equated to success
1. Original IW3 extraction and GLB validity.
2. Accurate cuboid silhouette with clear handguard, receiver, mag, stock and iron sights.
3. Spatial mounting of both animated hands at the correct `tag_weapon`, not simply standalone hand meshes.
4. Actual reload motion under the original XANIM timeline, including magazine separation and correct hand placement.
5. Camera aim through authentic iron sights, fire event alignment, and mobile frame rate.
6. Artistic authoring/legal clearance for any public/monetized distribution. The original COD4-derived mesh must NOT ship in a public APK without permission.

Screenshot output is still a **render of real converted geometry**. A GREEN structural CI is not evidence of steps 2–6. This PR stays draft pending independent visual review.

## Links
- Code + PR: https://github.com/1993velezpadilla-source/ZOMBIES-2026/pull/14
- New v2 run: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42115627761
- Blockbench/Mosaicary plugin: https://github.com/MopicMP/mosaicary — import GLB as GeckoLib/Bedrock/Generic Model with cube bones and animations (license for original model unchanged).
