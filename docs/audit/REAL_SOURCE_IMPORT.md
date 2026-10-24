# COD4 Android — REAL PC content import + native engine initialization

Date: 2026-10-23. Verified GitHub Actions run: [40037696157](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40037696157).

**Important distinction:** The test used a *temporary subset of actual files* from the user-provided `C4-Mocs.zip` package. This is not the 7 GB complete installation, a working mission, a Zombies game or a playable APK confirmation. Original game asset bytes were NOT added to git, released or uploaded as an artifact by this workflow.

## Real test environment

- Disposable Android 15 (API 35) Google APIs x86_64 emulator with `libndk_translation.so` for ARM64 libraries.
- `COD4.apk` unchanged, SHA-256 verified.
- Emulator internet disabled; test copies from the existing GitHub Release to ephemeral runner and then a disposable emulator.
- Import through **the app's real Android SAF folder picker**, not a mocked importer.
- Test folder contained 5 original PC files: `localization.txt`, `main/iw_00.iwd`, `zone/spanish/code_post_gfx.ff`, `zone/spanish/common.ff`, and `zone/spanish/ui.ff`.
- Total authentic source bytes imported: **244,365,466 bytes (~233 MiB)**.

## GREEN verified

1. App imported those five authentic source files using the native Android picker.
2. Launcher displayed: **`导入完成，共 5 个文件。`** (Import complete, 5 files).
3. Launcher displayed: **`基础资源检查通过。`** (Basic resource check passed).
4. Tapping Campaign launched `com.cod4.firstmission/.CampaignActivity` (logcat: `Displayed ... CampaignActivity`).
5. The **native COD4 engine actually initialized**, reported renderer initialization, Direct3D device initialization, a 1280×590 render view, and began to load `code_post_gfx`, `ui`, and `common` fastfiles. These are **runtime log lines**, not assumptions from static APK metadata.

## RED: a mission has NOT loaded

Logcat identified `ERROR: image 'images/devfonts.iwi' is missing`; immediately afterward the campaign process died and Android returned to the launcher (`Process ...:sp has died`). The missing image is one plausible initial blocker; additional assets or GPU compatibility problems may remain once resolved.

A search of the verified 24,104-entry nested IWD catalog located **`images/devfonts.iwi` inside `main/iw_01.iwd` (87,436 bytes)**. This bank was NOT included in the initial five-file partial test. The `main/localized_spanish_iw00.iwd` bank also contains `images/gamefonts_pc.iwi`. The next gate should include those banks and observe the engine outcome; **do not conclude the full game works until a real mission renders**.

## Evidence

- [Run 40037696157 — logs and artifact with screenshots](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40037696157), artifact `cod4-real-source-import-evidence`.
- Screenshot `04-post-import.png`: successful import and basic resource check.
- Screenshot `05-campaign-probe.png`: launcher visible after campaign process exited.
- Logcat: `CampaignActivity` launched, renderer initialized, missing `devfonts.iwi`, process died.
- [Static nested IWD inventory](c4-iwd-file-inventory.json) lists which bank contains the missing asset.

## Security and licensing

The repo already contains publicly available third-party commercial binaries in Releases. This test does not establish a redistribution license. Avoid publishing additional copies or including original game files in screenshots/artifact ZIPs. The APK remains untrusted beyond tests in disposable offline emulator; nothing was installed on the user's personal device.

## Extended 21-file import test — successful original game menu

Run: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40039223813

- A temporary set of 21 files (2,419,742,180 bytes) from the archive was imported into an offline Android emulator.
- The Android application confirmed basic resource checks and started its native campaign process.
- **Screenshot evidence:** the authentic Spanish COD4 menu rendered with `Nueva partida`, `Selección de misión`, `Controles`, `Opciones` and `Multijugador`.
- Graphics and sound initialized. Earlier missing texture startup errors were not observed in this expanded test.
- A playable mission is **not yet verified**. This is a confirmed *menu rendering* result only.
- Test artifact contains screenshots and logs, not extracted game assets.

## Nueva prueba de ejecución: escena 3D visible (run 40041071926)

El 23-oct-2026 se repitió la importación temporal de **21 archivos originales (2,419,742,180 bytes)** al emulador Android 15 sin acceso de red. [GitHub Actions, ejecución 40041071926](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40041071926) terminó con **conclusión de infraestructura success**.

**Evidencia visual verificada:** después de entrar al menú de campaña, la automatización tocó **Nueva partida** y observó capturas durante 100 segundos. En las capturas de 80 s y 100 s aparece **geometría 3D del juego**, HUD con controles táctiles y métricas del renderizador OpenGL ES. En la de 100 s aparece una perspectiva próxima a primera persona con arma parcial y escena de interior; a los 80 s se ve una toma elevada. No son fotogramas inventados, sino capturas del emulador guardadas como artefacto de Actions.

**Rendimiento observado, NO aprobado:** indicador de aproximadamente **2.4 FPS a los 80 s** y **4.0 FPS a los 100 s**, con pantalla intensamente roja. Son cifras puntuales de un **emulador x86_64 con traducción ARM64 y renderizador software**, no una prueba del rendimiento en un dispositivo Android físico. El software está lejos de mostrar una experiencia estable en este entorno.

**Límites:** se verificó que llegó a renderizar una escena 3D, pero **todavía no** se comprobó movimiento por joystick, disparos, ADS, recarga, colisiones, completitud del nivel, estabilidad prolongada o Zombies. El indicador `gameplay_confirmed` en el JSON de la prueba permanece `false`, correctamente. Se usaron 21 archivos, no los 7.02 GB completos.

El artefacto `cod4-real-source-import-evidence` contiene `08-loading-observe-080.png`, `08-loading-observe-100.png` y logs. No se adjuntaron recursos originales del juego; los datos temporales se limpiaron al terminar.
