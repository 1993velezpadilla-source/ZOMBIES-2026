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
3. `tools/zombies_offline/weapon_schema_export.py` reads all **502**
   upstream WeaponDef parser declarations (501 unique names; duplicate
   `guidedMissileType` exists in upstream) and exports only field names,
   byte offsets and type labels, never weapon data or proprietary assets.
   `tests/test_zombies_weapon_schema.py` validates exact completeness.
4. `.github/workflows/iw3-offline-sp-weapons.yml` runs the tests and builds
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

## Gate 1B — ejecución real de mapa SP sin red (2026-10-24)

Se añadió un **smoke test experimental** que comprueba que el ejecutable SP
no solamente se construye, sino que intenta cargar y simular un nivel en
Windows con los datos previamente aportados por el propietario.

- `tools/zombies_offline/stage_sp_data.py`: lee el archivo original
  fragmentado, extrae solamente la selección explícita de archivos
  `main/*.iwd`, `zone/spanish/{code_post_gfx,common,ui,killhouse}.ff`
  y `localization.txt`, y rechaza binarios comerciales, DLL y rutas
  no seguras. Los datos viven **únicamente en el runner temporal**.
- `tools/zombies_offline/instrument_sp_level.py`: instrumenta
  exclusivamente un clon efímero del C++ single-player y registra tres
  etapas distintas: `G_INIT_ENTER`, `G_SPAWN_ENTITIES_RETURN` y
  `G_FRAME_ENTER`. Se exige evidencia de creación de entidades y de
  al menos un frame SP; el PID o pantalla abierta no bastan.
- `tools/zombies_offline/probe_sp_runtime.ps1`: lanza **solo**
  `KisakCOD-sp.exe`, sin cliente MP ni servidor, con
  `+map killhouse`, captura marcadores y detiene el proceso de prueba
  a los 40 segundos. No intenta entrar en Steam.
- `.github/workflows/iw3-offline-sp-runtime.yml`: descarga datos
  temporalmente desde el Release ya creado, valida tests con ZIP falsos,
  compila SP y publica **solo JSON de diagnóstico**, sin IWD, FF,
  ejecutable o DLL; luego elimina la copia temporal.

**Interpretación estricta:** `killhouse` es un nivel del juego original
usado **solo para verificar compatibilidad del motor**. No es nuestra
habitación Zombies. Una evidencia de `G_FRAME_ENTER` tampoco demuestra
que se vea el mundo, que un arma funcione ni que un zombi exista.

**Estado al añadir la prueba:** pendiente de resultados del runner.
No declarar GREEN hasta revisar los logs y la salida JSON.

### Resultado confirmado del gate 1B (Windows CI)

**GREEN: comprobada ejecución del loop nativo SP sin autenticar en Steam ni
arrancar servidor multiplayer.**

- [GitHub Actions run 40135712001](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40135712001)
  — workflow completado `success`, 2026-10-24 21:53 UTC.
- Entradas SP disponibles en el runner efímero: **20 archivos**,
  **2,336,292,403 bytes** (ningún EXE del juego comercial).
- Compiló `KisakCOD-sp.exe` (código fuente) y lo arrancó mediante
  `+map killhouse`; proceso **vivo a los 40 segundos**.
- Prueba del juego real en el C++ original modificado temporalmente:
  `G_INIT_ENTER` = **true**,
  `G_SPAWN_ENTITIES_RETURN` = **true**,
  `G_FRAME_ENTER` = **true**.
- `offline_sp_level_loop_verified` = **true**;
  `runtime_error` = **null**.
- En este gate `multiplayer_connection_attempted=false` y
  `steam_login_attempted_by_test=false`.
- Se verificó solo el ciclo de inicialización, entidades y ejecución del
  motor; **no** se verificó la imagen 3D ni FPS, los controles, disparos,
  recarga, IA, muerte, rondas Zombies, assets propios o APK.
  `actual_graphics_verified=false`,
  `weapon_fired_verified=false`, `zombie_spawned_verified=false`.

Esta evidencia demuestra que ya no dependemos de lograr una conexión MP
para obtener ejecución del engine SP en el CI. El siguiente gate es
**player/weapon state + disparo medible**, después un actor original y
nuestra sala. Mantener la prueba con el contenido original solo como
verificación efímera de compatibilidad.

### Gate 2 — player, loadout y combate nativos (24 octubre 2026)

**Medición confirmada de la fase anterior:** [run 40140113173](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40140113173)
completó el diagnóstico y demostró `PLAYER_ENTITY_ACTIVE=true`,
`SP_ACTOR_PRESENT=true` y `actor_ai_think_executed=true` en
single-player. Pero mostró `player_weapon_equipped=false`,
`actual_weapon_fire_callback=false`, `bullet_fire_dispatched=false`,
`actor_damage_callback=false` y `actor_death_callback=false`.
El comando `+attack` inicial no era suficiente para generar un disparo.

**Acciones implementadas para aislar ese bloqueo:**

1. `instrument_sp_loadout.py` espera varios frames y que finalice la
   inicialización. En un **clon temporal solo de pruebas**, busca una
   definición de arma de bala con modelo válido **ya registrada** por el
   motor en esa partida, y utiliza las funciones SP originales
   `G_GivePlayerWeapon`, `InitializeAmmo` y `G_SelectWeaponIndex`.
   Los marcadores `TEST_*` no se confunden con equipamiento natural:
   `PLAYER_WEAPON_EQUIPPED` sigue siendo el criterio real.
2. `instrument_sp_input.py` usa `CL_CreateCmd` para emitir un máximo
   de doce comandos de cliente con `BUTTON_ATTACK`, únicamente cuando
   el snapshot de cliente declara un arma. No llama directamente a
   `FireWeapon`, `Bullet_Fire` o `G_Damage`. El marcador
   `TEST_ATTACK_BUTTON_INJECTED` significa solo input de prueba;
   `FIRE_WEAPON_ENTER` y `BULLET_FIRE_DISPATCH` son necesarios
   para declarar disparo real procesado.
3. `probe_sp_runtime.ps1` distingue en JSON descubrimiento, concesión,
   selección, equipamiento, generación de comandos, disparo y daño.
   No atribuye ningún zombi al proyecto hasta tener uno propio.
4. Tests sintéticos específicos y CI repiten una escena SP original
   **solo como input de compatibilidad**. El engine vendorizado, las
   verificaciones de red y la autenticación MP permanecen intactos.

**Estado al preparar Gate 2:** el nuevo workflow
[run 40141908316](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40141908316)
estaba ejecutándose. No declarar carga de arma o disparo GREEN hasta
revisar su JSON de resultados.

### 🟢 Gate 2 — disparo original de SP confirmado (2026-10-24)

**EVIDENCIA REAL, no inferencia:** [GitHub Actions run 40141908316](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40141908316) compiló y ejecutó el motor nativo KisakCOD-sp en una prueba local durante **40 segundos**, sin servidor multiplayer y sin iniciar sesión en Steam.

La prueba solo modificó temporalmente su copia efímera del código, no `third_party/KisakCOD`:

- `test_loadout_bootstrap_attempted=true`: inició test-only bootstrap.
- `test_valid_registered_bullet_weapon_found=true`: localizó una definición de arma válida **ya registrada** en la escena original.
- `test_weapon_granted=true`, `test_ammo_initialized=true`, `test_weapon_switch_requested=true`: llamadas originales del motor completadas.
- **`player_weapon_equipped=true`**: el estado real del jugador cambió y registra el arma equipada; no se confunde con solo solicitar equiparla.
- `test_client_attack_button_injected=true`: se generaron comandos de cliente originales limitados usando `BUTTON_ATTACK`, no llamadas directas a armas o daño.
- **`actual_weapon_fire_callback=true` y `bullet_fire_dispatched=true`**: el motor ejecutó `FireWeapon` y llegó a `Bullet_Fire` a través del procesamiento normal de controles. **`weapon_fired_verified=true`.**
- También continuaron **`sp_actor_present=true`**, **`actor_ai_think_executed=true`**, y **`offline_sp_level_loop_verified=true`**.
- `runtime_error=null`.

**Aún pendiente:** `g_damage_callback=false`, `actor_damage_callback=false`, `actor_pain_callback=false`, `actor_death_callback=false`, `zombie_spawned_verified=false`, `actual_graphics_verified=false`. La prueba demuestra el procesamiento del disparo pero no un impacto sobre un objetivo, un enemigo muerto ni nuestra sala.

**Limitaciones de empaquetado:** se usaron archivos del juego previamente aportados solo dentro del runner para validar compatibilidad SP; ni datos, ni modelos ni EXE comerciales se exportaron desde este gate. Una distribución de ZOMBIES-2026 exige assets propios o derechos de uso adecuados.

**Siguiente gate:** colocar un objetivo original verificable y medir en runtime la trayectoria/impacto, daño y muerte. Luego integrar una entidad zombi original y el control de rondas. No cambiar de ruta hacia Steam/MP.
