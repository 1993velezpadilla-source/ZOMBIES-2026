# Xziel Zombies — Luanti Classic Map Builder

PR #22 source prototype, separate from FIX43 APK. Custom Lua logic; NZ:P v26 is a design reference only, not imported code.

## Organised editor inventory
- Gameplay: Power Switch, four perk dispensers, Mystery Box, Upgrade Station, Barricades, Round Display.
- Purchases: Wall Buy (choose any installed Arsenal weapon and an individual price), Buyable Door (individual price).
- Spawns: Player Spawn Marker and Zombie Spawn Marker.
- Utilities: Invisible-during-PLAY Barrier, Light 5, Light 10, Light 14.
- Tools: XZIEL Map Editor PLAY/STOP item or /xz_editor.

### Configure wall purchase
Place Wall Buy in EDIT; an Arsenal weapon list opens. Select one weapon, enter 0–50000 points in the next dialog and tap CONFIRM. Re-tap the wall in EDIT to change its settings. Costs are per block, not global.

### Configure a door
Place Door Buy; enter its price (0–50000), confirm. Re-tap in EDIT to change. Each one saves its own price.

### Player and zombie spawns
Place Player Spawn Marker where the player should appear during PLAY and on respawn. Zombie Spawns mark positions for the later round AI; they do not yet generate live zombies.

## PLAY / STOP test
Use the map editor item or /xz_editor. Tap MAP BLOCKS - CATEGORIES for four sections (Machines, Purchases, Spawns and Utilities); tapping any block gives a placeable item. Then tap PLAY TEST. All map-helper blocks swap into hidden runtime variants: lights keep emitting, barriers keep blocking, player/zombie spawn positions remain registered. The player moves to Player Spawn. You can test perk, points, door and weapon purchases.
STOP TEST restores temporarily bought doors, starting health, points, main inventory, perk flags and player position. This is NOT a full snapshot of arbitrary block edits. Do not dig or build during PLAY until complete world duplication is implemented.
The source now includes an experimental low-load wave controller: real marked spawn points, up to 12 simple enemies active, basic chase/attack, health/damage, points for hits and kills, and increasing rounds. This is NOT the final zombie AI, animation or pathfinding and is not yet tested in Android. Exported-map conversion and signed APK integration remain pending.

## Integration with weapons
The current Arsenal must call the reload, fire interval and damage multipliers exposed by xz_classic_props for perks and Pack-a-Punch to affect its shooting mechanics. The source mod deliberately does not alter weapon model files.

## Tests
- luac -p mods/xz_classic_props/init.lua
- luac -p mods/xz_classic_props/mode.lua
- luac -p mods/xz_classic_props/builder.lua
- luac -p mods/xz_classic_props/waves.lua
- lua tests/test_xz_classic_props.lua
- lua tests/test_xz_classic_editor.lua

15 original PNG textures are included. No Activision/NZ:P art or source is included.

## New visual + debug additions
- Wall Buy configured with a real Arsenal item: a small world-facing item miniature appears floating near the wall. This is the **registered item visual**, not a converted GLB world mesh; the weapon GLB includes first-person hands and is unsuitable for direct wall rendering without a dedicated export/conversion.
- Mystery Crate: original two-block wooden chest front, using a custom companion node (not VoxeLibre storage chest), still charges 950 points and awards a random registered weapon.
- Zombie Spawner: editor marker uses `mob_spawner.png` from VoxeLibre but deliberately does NOT start the vanilla spawner timer. Our wave controller retains control; markers hide in PLAY.
- Developer: inside PLAY, map-maker can open the DEVELOPER panel from editor. Add 1k/10k/50k points, toggle infinite health and ammo, or pick any registered Arsenal weapon. Restricted to `xz_map_builder` / server privilege; resets on STOP. Arsenal ammo implementation uses its original `ar_clip`/`ar_reserve` stack metadata and will need an actual Android integration test.
- This is GitHub source **not yet part of FIX43 APK** and not Android runtime-validated.

The Developer tool is automatically added to an authorized map maker’s inventory only during PLAY, making its panel accessible from the mobile hotbar; it is removed on STOP by the inventory rollback. The floating wall-item icon is rotated for a sideways/profile view. Both halves of the Mystery Crate activate the same purchase logic.

## Every weapon: genuine 3D gun miniature (source implementation)
The `wall_models.lua` resolver parses the **actual private Arsenal runtime manifest** installed alongside the guns. For every registered `arsenal:<id>` it verifies its own `arsenal_<id>_gun.glb`, and maps no weapon to the AK except AK itself. `decorations.lua` creates a non-collidable, unmoving Luanti mesh entity scaled to 10%, using the preinstalled, gun-only GLB and preinstalled `arsenal_flat_metal.png`; it never duplicates 28 models in the public GitHub repo. The same code handles AK-47, M4, M249, RPG-7, M9 and all other registered weapons without special-casing any one. Legacy items missing verified private gun meshes retain only their **own** icon, never another weapon’s model. The exact orientation, visible size and rendering of GLB `mesh` entities still require Pixel Fold validation on the customized native GLB-capable client (and possibly client-level changes).

The Wall Buy itself is now a **thin non-solid wall mount**, so the 3D gun is the primary visual, not an oversized cabinet. The mount stays selectable for purchases and can coexist with a nearby wall. The mesh preview supplies the original Arsenal flat metal texture to up to 64 material buffers; no gun is substituted for another.

### FIX43 reality check — corrected item namespaces and private models
The working FIX43 APK contains **26 `cod4:<id>` tools plus `ak47dev:ak47` and `ak47dev:m9`**, all in `games/voxelibre/mods/ak47dev/`. Earlier guesses that these were all `arsenal:*` with `arsenal_<id>_gun.glb` were incorrect. Wall Buy discovery now includes all 28 REAL IDs. Real first-person `a_*` GLBs contain gun and hands in one mesh; during private APK packaging, a separate generator strips hand material/rig/animation and outputs `xz_wall_<id>.glb`. One gun-only mini mesh is mapped to each ID and its exact atlas (`a_<id>_shared.png`, or AK/M9 HD atlas). These extracted proprietary meshes must stay in the PRIVATE APK, not in the public GitHub repository. Runtime GLB entity rendering is still not validated on Pixel Fold.
