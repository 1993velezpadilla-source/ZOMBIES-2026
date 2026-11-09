# Xziel Classic Zombies — interactable blocks (Luanti)

First source-level gameplay block pack for the existing Luanti/VoxeLibre project. **This is not an APK**, not a claim of on-device testing, and not integrated into the signed FIX43 installer yet.

## Registered placeable nodes

| Node | Cost | Behavior |
| --- | ---: | --- |
| \`xz_classic_props:power_switch\` | Free | Turns world power ON persistently. |
| \`xz_classic_props:perk_vitality\` | 2,500 | Iron Heart (Jugger-style): +20 max health, heals. |
| \`xz_classic_props:perk_revive\` | 1,500 | Second Chance (Revive-style): consumes on one lethal hit, self-revives. |
| \`xz_classic_props:perk_speed\` | 3,000 | Rapid Hands (Speed-style): exposes 0.5 reload-time multiplier. |
| \`xz_classic_props:perk_double\` | 2,000 | Double Impact (Double Tap-style): exposes 0.85 fire interval / 1.25 damage multipliers. |
| \`xz_classic_props:mystery_box\` | 950 | Random verified Arsenal weapon from registry; never charges if none is installed. |
| \`xz_classic_props:wall_buy\` | 1,200 | AK-47 from Arsenal, if present. |
| \`xz_classic_props:pack_a_punch\` | 5,000 | Tags the held Arsenal weapon, exposes 2x upgraded damage multiplier. |
| \`xz_classic_props:buyable_door\` | 1,000 | Charges points and opens the blocked passage. |
| \`xz_classic_props:barricade\` | Free | Repair damaged boards for +10 points each. |
| \`xz_classic_props:round_display\` | Free | Reports current round and own points. |
| \`xz_classic_props:zombie_spawn_marker\` | Free | Marker for future AI. |
| \`xz_classic_props:player_spawn_marker\` | Free | Marker for future mode controller. |

**13 nodes total.** Machines are lightweight 1-node cabinets with original low-cost textures. No trademarked textures/audio or copied CoD game data.

## Installation

Put the \`xz_classic_props\` folder under your **VoxeLibre game mods** directory or in the world's enabled mods. Enable the mod and load the map. New blocks will appear in the creative inventory; right-click/tap the interactive face to use one. The mobile interaction must be tested in an actual Android build.

Players start with 500 points once per profile. Real zombie-kill points are intentionally **not fabricated**; the later wave AI must call \`xz_classic_props.award_kill(player, headshot)\`. For safe solo testing, admin command: \`/xzcp_points playername 20000\`.

## Integration contract with existing Arsenal

The perk state and Pack-a-Punch metadata survive save/reload. The existing \`arsenal\` mod uses private fire/reload functions and must explicitly call:

\`\`\`lua
local z = rawget(_G, "xz_classic_props")
local reload_scale = z and z.reload_time_multiplier(player) or 1
local fire_scale = z and z.fire_interval_multiplier(player) or 1
local damage_scale = z and z.damage_multiplier(player, weapon_stack) or 1
\`\`\`

Apply the scales to the *original Arsenal data*, without changing its source animations or normal weapon parameters. **Speed, Double Impact and upgraded weapon damage are not active until this bridge is wired.** No real zombie spawns or round controller exists in this mod, and the Round Counter defaults to round 0.

The existing Arsenal universal ammunition box should stay as-is; this mod doesn't duplicate it. Separate wave AI and an upgraded weapon appearance/sound system can be built later.

## Test

\`\`\`sh
luac -p mods/xz_classic_props/init.lua
lua tests/test_xz_classic_props.lua
\`\`\`

Run with a 5.1-compatible Lua interpreter. This checks registration and point purchase safety; it does **not** test real Android gameplay.

## License

Original Lua and procedurally created textures in this folder are made for this project, released as MIT (see LICENSE). Confirm licensing of all other bundled third-party assets before monetizing or publishing.
