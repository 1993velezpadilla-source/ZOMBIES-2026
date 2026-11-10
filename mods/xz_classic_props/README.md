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
