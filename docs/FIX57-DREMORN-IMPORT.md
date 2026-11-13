# FIX57 — Dremorn Zombie visual adapter (asset pending)

Model owner: Dremorn, CGTrader #773096.
Official source: https://www.cgtrader.com/free-3d-models/character/fantasy-character/zombie-79f78dd5-e3c9-44d2-a9e4-9530f9139426
CGTrader free commercial license guidance: https://help.cgtrader.com/hc/en-us/articles/360015122437-Can-I-commercially-use-a-free-model

**No original Dremorn FBX, texture, animation or redistributed asset is committed here.** This branch does not produce an APK visually different from FIX56 until an authentic asset is provided.

Dremorn's original page lists 7,200 triangles, 12 animations, 2 FBX files and 4096 pixel PBR textures, with Royalty Free (no AI) licensing. Commercial distribution additionally requires protecting the model from extraction as a standalone resource. The existing Luanti compressed assets ZIP is extractable, so commercial publication of Dremorn inside that APK is **not cleared**. First test privately; obtain written authorization or compliant packaging before release. Do not upload third-party original files to a public CI artifact.

## What the optional adapter will load
- Model: `games/voxelibre/mods/xz_zombies_classic/models/xz_dremorn_zombie.glb`
- Texture: `games/voxelibre/mods/xz_zombies_classic/textures/xz_dremorn_body.png`
- If either does not exist, legacy VoxeLibre meshes, sounds, original 28 COD4 weapons, scores, barricades, AI, and animations are untouched.
- Converts VoxeLibre stand/walk/run/punch/punch2/die animations to original Dremorn named GLB clips `idle1`, `walk`, `run`, `atack1`, `atack2`, `death1`. The vendor uses misspelling `atack`.
- Apply ONLY to zombies spawned in Zombies Classic rounds, not all other world mobs.
- Uses existing Luanti 5.17+ `obj:play_animation` API.

## Authentic FBX conversion checklist
1. Download from seller via CGTrader to your own account. Preserve original license and original FBX/textures.
2. In Blender, import FBX with armature and 12 actions intact. Ensure each needed action exports to a named glTF animation track.
3. Export glTF 2.0 binary GLB; normalize to 18 mesh units tall (1.8 Luanti blocks); Luanti entity mesh scale is 10 units / block. Verify forward orientation (+Z).
4. Save Albedo/Base Color from TGA to `xz_dremorn_body.png` with an initial 1024-square mobile test variant. Luanti ignores glTF embedded images.
5. Validate glTF tracks, bones, UVs, mesh scale, rotation and textures on real Android before switching default model.
6. Do not commit seller's original art to the public GitHub repo. Do not release commercial APK with extractable raw Dremorn meshes without permissions/licensing review.

Docs: https://docs.luanti.org/for-creators/models/ and https://api.luanti.org/class-reference/
