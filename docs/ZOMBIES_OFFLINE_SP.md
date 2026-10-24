# ZOMBIES-2026 — single-player offline first (decision: 2026-10-24)

## Product decision

This is **our own offline Zombies game**, not COD4 matchmaking or COD4 public multiplayer.
The user's priority is **weapon feel and source-driven weapon behavior**, not
connecting to Steam MP or emulating other peoples' online servers.

**Architecture chosen for the next technical gate:**

- Compile a source-based **single-player (SP) IW3** executable with the existing
  game-side actor/AI code, navigation, weapons, physics and animation systems.
- Build and test *only* `KisakCOD-sp`. No `KisakCOD-mp` and no dedicated server
  for this gate; no TCP/UDP handshake or player-login test.
- For the disposable SP source copy, do not call `Steam_Init()` in `WinMain`
  when `KISAK_SP` is defined. The multiplayer/Steam ticket source is unchanged.
  The purpose is an original **standalone single-player build**, not bypassing
  authentication to join an existing online service.
- Start with **one original test room**, one **original or appropriately licensed**
  weapon definition, one player, one test enemy actor. Verify spawn, pathing,
  damage, death and replay/restart before adding perks, rounds, Mystery Box or
  Android controls.
- Weapon data is **not to be guessed**. Read exact owned/authorized data when
  available, or use independently authored stats. The SP source exposes
  `weaponDefFields[502]`, including `fireTime`, `clipSize`, `reloadTime`,
  `reloadEmptyTime`, `adsTransInTime`, `adsTransOutTime`, `damage`, and
  viewmodel/animation links. The presence of parser fields alone does **not**
  prove that any particular weapon definition, animation, model or sound is
  loaded into the new game.
- Use RotU's scripting architecture as a **reference**, not as a drop-in SP
  mod. RotU was designed for multiplayer `addTestClient()` entities, while the
  Kisak SP actor system uses different entities and callbacks. A bridge or
  independently authored script/game mode is necessary.

## Evidence / source references

- `third_party/KisakCOD/scripts/sp/CMakeLists.txt`: native
  `KisakCOD-sp` target with `KISAK_SP` compile flag.
- `third_party/KisakCOD/scripts/sp/sp_files.cmake`: built-in
  `game/actor.cpp`, `actor_spawner.cpp`, `actor_navigation.cpp`,
  `game/g_main.cpp`.
- `third_party/KisakCOD/scripts/common_files.cmake`: shared
  `bg_weapons.cpp`, `bg_weapons_load_obj.cpp`, `g_weapon.cpp`.
- `third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp`: 502 weapon
  definition schema fields. This is **source layout**, not rights to game assets.

## Implemented in the branch

1. `tools/zombies_offline/sp_source_gate.py` prepares an isolated copy for SP,
   leaves the checked-in KisakCOD sources untouched, and outputs a truthful
   source audit JSON. Refuses to edit the vendored original.
2. `tests/test_zombies_offline_sp.py` proves exactly what the script changes,
   checks SP actors and weapon source contracts and tests failure cases.
3. `.github/workflows/iw3-offline-sp-weapons.yml` runs the tests and builds
   **only SP** in a disposable Windows 2022 runner, with no Steam login,
   original game ZIP download, localhost server or COD4 data unpacking.
   It publishes only JSON evidence, not the EXE or commercial data.

## Gates — strict evidence, no fake GREEN

| Gate | Criteria |
| --- | --- |
| 0. Source-only SP | Tests pass; SP has actor and WeaponDef source. |
| 1. Native SP compilation | GitHub Actions actually produces `KisakCOD-sp.exe` (no launch). |
| 2. Original offline test room | An explicitly licensed/original map loads and draws in-game. |
| 3. Weapon usable | Player can fire, reload and ADS; timestamps/stat values measured. |
| 4. One enemy | SP actor tracks player, takes damage and dies; test is recorded. |
| 5. Zombies loop | Rounds, economy, respawns, death/restart; no network needed. |
| 6. Android | Real ARM64 renderer, touch/gyro, playable performance on device. |

None of gates 2–6 may be declared completed because a compiler produced an EXE.
A successful GitHub Actions workflow is not proof of gameplay.

## Distribution and licensing

KisakCOD's GPLv3 source is separate from the proprietary COD4 assets.
The original COD4 weapons' models, animation data, sound and textures are
**not included** here and must not be redistributed without permission.
Do not ship the imported COD4 archive or APK as part of an original game's
public package. Own game weapons may be inspired by functional principles,
but create/license the commercial content needed for release.

**Explicitly paused:** MP `127.0.0.1:28960` connection testing, public
multiplayer, Steam authentication debugging, and RotU dedicated gameplay
claims. These are not prerequisites for our current offline Zombies milestone.
