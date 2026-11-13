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

## FIX57 continuation after source audit (2026-11-13)

- Luanti official docs confirm `ObjectRef:play_animation(track, {speed=1,loop=...})` and `ObjectRef:update_animation(track, {speed=...})` for glTF 5.17+.
- VoxeLibre `mcl_mobs/effects.lua` calls the OLD `set_animation_frame_speed` on each native mob tick. The FIX57 per-instance wrapper now uses **named glTF track updates**, with 0.2 speed change threshold to avoid unnecessary Android updates.
- VoxeLibre `mcl_mobs/physics.lua` requires `animation.die_start` and `animation.die_end` to play `die` and time corpse removal. The FIX57 per-instance animation table is copied from original, then a **provisional** 1.6 second death duration is set. Adjust based on the authentic GLB action length; common mobs remain untouched.
- Neither `fx/OBJ` nor `FBX` can run unconverted. FBX import should export the six exact named tracks `idle1`, `walk`, `run`, `atack1`, `atack2`, `death1` to a **skinned GLB**. The seller advertises 12: `idle1`, `idle2`, `walk`, `run`, `rage`, `atack1`, `atack2`, `atack3`, `atack4`, `gethit`, `death1`, `death2`.
- Run `python3 incoming/luanti-fix50b/tools/inspect_dremorn_glb.py path/to/xz_dremorn_zombie.glb --texture path/to/xz_dremorn_body.png --report dremorn-report.json` before attempting Android packaging. It verifies GLB2, valid scene, skin, named tracks, one material and PNG with no asset extraction.
- Official documentation: https://api.luanti.org/class-reference/ ; https://docs.luanti.org/for-creators/models/ ; https://github.com/VoxeLibre/VoxeLibre/blob/master/mods/ENTITIES/mcl_mobs/effects.lua ; https://github.com/VoxeLibre/VoxeLibre/blob/master/mods/ENTITIES/mcl_mobs/physics.lua

**APK warning:** The signed FIX57 integration-only build intentionally does **not** contain Dremorn artwork, so in game the zombies still look native. This isolates and protects all existing gameplay functionality; the authentic FBX/PNG and a rights-cleared private Android trial remain outstanding. The build uses an independent test-signing key and the same Android package name as FIX56, so it cannot install as an update over FIX56; back up worlds and uninstall conflicting developer tests before installing.
