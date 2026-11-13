# FIX56 research — Minecraft-style voxel navigation + rigged zombies (2026-11-13)

## Root cause traced from actual FIX55 source
- `rotu_ai.lua` called VoxeLibre `entity:gopath(brain.last_seen)` and returned for the entire `gowp` state.
- VoxeLibre `mods/ENTITIES/mcl_mobs/pathfinding.lua` explicitly rejects new `gopath` destinations while already in `gowp`; `_target` is a frozen position.
- Zombies followed old player positions even after moving far away. More raw speed does not fix stale goals.
- VoxeLibre `combat.lua` already has `do_states_attack()`, `smart_mobs()`, A* via `minetest.find_path`, collision and stuck handling. Retaining native attack has lower regression risk than a second route driver.

## FIX56 narrow test, isolated from production
- Remove `gopath` behavior in `rotu_ai.lua` and use established `do_attack`/native combat. Keep RotU visible-first target priorities.
- On hidden moving player, supply updated target position at most every 1 second and clear stale path if destination shifted 3+ blocks. Never fake attack line of sight.
- Escape legacy `gowp` states from FIX55. No extra A* calls in Lua.
- 28 guns, animations, old source-specific hit points, NZ:P v26 barricades and APK native files remain byte-identical.
- Pending physical Pixel Fold tests: L-shaped room, walls, stairs, a door, a five-stage barricade, many zombies (10–12), out-of-range target, narrow corridor, moving player, FPS.
- This **does not solve** all large-world A* problems. VoxeLibre's native smart_mobs uses a 16-block path search; gopath uses a 25-block search. The cathedral needs higher-level room/door waypoints for cross-map navigation.

## Follow-up architecture after live playtest
Minecraft-style pathfinding has independent goal choice, navigation, motion, and attack execution:
- Walkable voxel nodes: two block-clearance, supported ground, legal jump/fall limits, doors and hazard penalty, do not step into unloaded chunks.
- Local A* path, optional straight-line waypoint smoothing, stuck detection with cooldown.
- Goals always refer to a live player or a *bounded*, recently lost location. Refresh if goal changes materially, not solely on reaching old destination.
- Portal graph across rooms: generate strategic nodes for doorways, staircases, barricades and map sectors; local A* between portals. Prefer generated navigation over manually placed per-block path markers.
- Cache maps and stagger route calculation for many mobs (10–12 at once), and consider shared reverse-distance/flow fields for the crowd; update dirty regions after Create Map edits.

## Sources
- https://github.com/VoxeLibre/VoxeLibre/blob/master/mods/ENTITIES/mcl_mobs/combat.lua
- https://github.com/VoxeLibre/VoxeLibre/blob/master/mods/ENTITIES/mcl_mobs/pathfinding.lua
- https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_melee_attack?view=minecraft-bedrock-stable
- https://minecraft.wiki/w/Mob_AI
- https://docs.luanti.org/for-creators/models/

## New zombie artwork choices (do not copy proprietary COD characters)
- Quaternius **Zombie Apocalypse Kit**: four enemies and other characters, FBX/OBJ/glTF/Blend, pack-page CC0 commercial use. https://quaternius.com/packs/zombieapocalypsekit.html
- Quaternius **Animated Zombie Pack**: animated zombie, FBX/OBJ/Blend, pack-page CC0. https://quaternius.com/packs/animatedzombie.html
- Kenney **Animated Characters 3**: male/female zombie skins, FBX, CC0. https://kenney-assets.itch.io/animated-characters-3
- An `.obj` has **no skeletal animations** in Luanti; export skeletal model as `.glb` or `.gltf`. Luanti 5.18 supports skeletal glTF named tracks; embedded image textures in glTF are not read, extract PNG to mod textures.
- Keep license and artist/distro metadata alongside imported models.

## Free skeleton rigging (check export license per tool and asset)
- **Android Prisma3D**, manual bones/rigging/skinning, OBJ/FBX/glTF import/export: https://play.google.com/store/apps/details?id=com.prisma3D.prisma3D
- **Android RiggerDroid**, free body rig GLB import, GLB output: https://play.google.com/store/apps/details?id=com.aistudio.retargetforge.kxmq
- **3DValley free AI auto rig**, OBJ/GLB input, rigged GLB output, daily free GPU allowance: https://3dvalley.com/tools/fix/auto-rig
- **Adobe Mixamo** free with Adobe ID, accepts OBJ/FBX/ZIP, commercial games allowed: https://helpx.adobe.com/creative-cloud/help/mixamo-rigging-animation.html
- **Grab3D auto rig** free/no sign in, OBJ/GLB -> GLB/FBX, website explicitly targets desktop WebGL browsers: https://grab3d.com/es/tools/auto-rig/
- **afk.ai** browser rigging with animations, but requires desktop Chrome/Edge; phone unsupported: https://afk.ai/
- Avoid assuming all free tiers grant commercial export rights (Meshy's free exports are personal/evaluation only per https://www.meshy.ai/animation-library).

## Commercial-use safeguards
- CC0 covers specified Quaternius/Kenney packs; archive the download page/license.
- A rigging tool does NOT change ownership or licensing of the original mesh.
- The converted model must be tested in original Luanti engine on ARM64 before changing default zombies. Do not merge FIX56 or replace existing stable APK until real-phone chase/FPS/AI test.
