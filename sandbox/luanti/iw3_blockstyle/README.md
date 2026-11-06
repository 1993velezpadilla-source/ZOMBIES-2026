# COD4 AK-47 -> Minecraft-style block geometry + every XANIM

> Complete ADS review/export is now available through `ads_pipeline.py`:
> five paired clips preserve the idle/fire hand pose while layering the source
> tag_ads curves. Enter/exit follow the weapon definition's 0.25s timing;
> iron alignment is calibrated once, with a fixed camera throughout.
> See [ADS verification and import](../../../docs/audit/COD4_AK47_ADS.md).

> The rifle now has an original **512x512 PNG texture atlas**, embedded in its
> GLB and mapped through new rest-space UVs. Wood grain, pressed magazine
> grooves and machined-metal detail are painted at native resolution. The
> 144,134-triangle mesh, original rig and all 39 rifle clips are preserved.
> Pose/FPS depth previews sample the embedded image directly. The hands keep
> their existing vertex colors. See [texture verification](../../../docs/audit/COD4_AK47_TEXTURE_512.md).

> High detail is now the default rifle profile: 384 grid divisions and
> 144,134 triangles after internal-face removal. Use `--rifle-detail legacy`
> for the original 10,692-triangle comparison. Primary pose/FPS previews use
> OpenGL/EGL depth testing; install ModernGL 5.12.0 and Mesa EGL.
> See [geometry verification](../../../docs/audit/COD4_AK47_HIGH_DETAIL.md).

> Current native-rig path: build the pinned OAT exporter with
> `patch_oat_native_locals.py` and set `IW3_NATIVE_LOCALS_DIR` while extracting.
> Pass those private sidecars with `voxelize.py --native-locals DIR`.
> The native model rest fields are independent of the glTF skin bind pose.
> The rifle model root attaches to hands.tag_weapon; tag_ak47_mount is not
> the hand socket. See [native-pose verification](../../../docs/audit/COD4_AK47_COORDINATE_FRAME.md).

**Engineering prototype, not an asset release and not an APK.**

## Converter selection

We researched the existing **Mosaicary / glTF to Minecraft** Blockbench plugin
(MIT): https://github.com/MopicMP/mosaicary . It imports glTF/GLB, converts
polygonal surfaces to Minecraft-compatible cubes and carries **bones plus
rotation, translation and scale animation tracks** into GeckoLib / Bedrock Entity
/ Generic Model. This is the preferred editor/visual QA tool once a GLB has
valid, correctly calibrated animations. Use Blockbench -> File -> Plugins ->
load the Mosaicary URL, then File -> Import -> Import glTF Model -> choose the
private animated GLB -> **Cubes** -> **Generic Model** (or GeckoLib). Do *not*
use a static Java block/item export when reload animation is required.

Another online GLB->BBModel converter was evaluated; tools that explicitly
discard skin rigs and animation keyframes are not suitable for our FPS pipeline.

## Actual, implemented conversion

The executable `voxelize.py` does the conversion inside an isolated CI runner.
It reads the existing COD4 sample archive in our release through the prior
PR #6 OpenAssetTools extraction pipeline (checkout on its source branch).

1. Select the original first-person AK-47 LOD0 model whose joint names overlap
   the most available AK47 XANIM tracks.
2. Decode **all** available `viewmodel_ak47*` XANIM (not a four-clip subset).
   Include idle/ADS/fire/reload and all other matching actions. Count and
   report clips with no matching bone rather than declaring them successful.
3. Approximate the original mesh triangles as **axis-aligned surface cuboids**,
   bound to their dominant existing skin joint; preserve hierarchy and
   inverse-bind matrices; enforce explicit geometry budgets (40,000 rifle
   cuboids in high detail; 4,000 with the legacy profile).
4. Independently rebuild both first-person AK geometry and original viewhands
   (if present) as cubes, preserving their skinning and associating each
   compatible XANIM clip as a named glTF animation channel.
5. Output `*_BLOCKSTYLE_*_PRIVATE.glb` in an ignored scratch directory.
   A separate JSON audit contains names and counts only. **No actual COD4
   geometry, textures, animated keyframes or derived proprietary mesh is
   committed or exposed in public GitHub Actions artifacts.**

The generated model uses independently drawn procedural wood/metal materials;
it is a **starting point for reauthoring an original AK-family weapon**, not
a commercially cleared game asset.

## What still requires a real visual/functional gate

- Validate the original IW3 local-vs-global rest pose, axis orientation and
  animation curves on the *converted skinned cubes*. Correct matching of joint
  names is necessary but not sufficient.
- Confirm both hands hold the gun, rather than passing through it; verify
  reload magazine, bolt, ADS front/rear irons and muzzle alignment frame by
  frame. Camera FOV/hip pose and timing need real game testing.
- The voxelized output is an animated **glTF**, not yet a Minecraft Bedrock
  geometry export or an APK swap. Mosaicary's visual import/export is a
  separate verification gate, and the existing independent original V3.3
  game AK remains untouched until the new weapon passes it.
- Genuine COD4 model/animation assets have not been licensed for commercial
  redistribution. Do not publish unencrypted original/derived assets or an
  APK containing them. A new, independently authored game model is needed
  for the product.

## CI

- Workflow: `.github/workflows/iw3-ak47-blockstyle-private.yml`
- Code: `sandbox/luanti/iw3_blockstyle/voxelize.py`
- First job runs against **our own original** editable AK test GLB, confirming
  cube production, five-bone skin structure and animation preservation.
- Second job downloads the user-supplied original COD4 package into the
  ephemeral runner, then runs the full real conversion and uploads only a
  metadata JSON report.

**Do not equate unit-tests GREEN with gameplay/ADS/reload verified.**

