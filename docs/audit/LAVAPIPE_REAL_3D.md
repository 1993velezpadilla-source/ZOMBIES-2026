# COD4 Android: Lavapipe produces actual 3D geometry in natural colors

**Verified:** [GitHub Actions run 40055353083](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40055353083). Both Lavapipe and current SwiftShader software-renderer jobs completed, using the same original, SHA-verified `COD4.apk` and the same **21 original source files** (2,419,742,180 bytes) extracted temporarily from the user's existing 7 GB release archive.

## Finding: third GPU backend is a major improvement in the emulator

The Android 15 Google APIs x86_64 emulator supported `-gpu lavapipe`, a Mesa software renderer, and the original ARM64 engine ran using Android's native ARM translation (`libndk_translation.so`).

**Lavapipe:** At 40, 60, 80 and 100 seconds after the campaign menu interaction, a true COD4 3D interior scene rendered **with natural colors**. The latest frame clearly contains world geometry, textured walls, lighting, a first-person weapon, and the native mobile-control overlay. The in-game HUD displayed approximately **4.2 FPS** at the end (a **software GPU on an emulated x86_64 system**, not an Android phone FPS measurement).

**SwiftShader:** The latest control-run frames remained mostly uniform gray with no validated 3D scene within 100 seconds. In the previous run using `swiftshader_indirect`, a red-tinted scene appeared, but severely incorrect colors remained.

| Verified outcome | Lavapipe | SwiftShader |
| --- | --- | --- |
| Android APK installs and imports 21 files | PASS | PASS |
| Original COD4 Spanish campaign menu | PASS | PASS |
| 3D level visible in latest screenshot | **PASS** | Not demonstrated in this run |
| Normal-colored 3D walls and floor | **PASS** | Not demonstrated |
| Native touch overlay visible in 3D | **PASS** | Not demonstrated |
| Red-dominant pixels in center scene, measured | **0.00%** | 0.00% of plain gray/black frame |
| Latest center-scene RGB mean | **[95.52, 92.19, 83.27]** | **[32.19, 32.29, 32.31]** |
| Measured process total PSS at end | **1,409,349 KB** | **1,545,510 KB** |
| Good sustained frame rate | **NO** — around 4 FPS on screenshot | **NO** |
| Verified shooting, movement, ADS, reload | **Not yet** | **Not yet** |

**Proof of actual scene rendering:** GitHub Actions artifact `cod4-gles-lavapipe`, screenshot `08-loading-observe-100.png` in run 40055353083. This is a captured emulator frame, not an image generated or mocked for the report.

## Interpretation and limitations

- **The emulator GPU backend was the controlled variable**. This strongly supports a GPU translation/backend compatibility problem behind the tint or missing-scene symptoms. It does **not** identify a precise `glUniform4fv` defect in the compiled native APK or prove it will work on a physical ARM64 device.
- Lavapipe is an **Android Emulator launch flag** and does not represent a toggle that users of COD4.apk can select in their Android settings. Do not claim the APK itself has been patched.
- The screenshot's ~4 FPS reflects costly ARM64-on-x86_64 translation and software Vulkan/GLES rendering. Do not extrapolate that number to a real phone, nor claim a physical-device fix.
- The scene displayed **Call of Duty 4**, **not** the user's Godot *IGLESIA* map or Zombies rounds. The COD4 engine source is not in this repo, and the runtime assets alone cannot create Zombies features.
- Real gameplay controls, action results and stability remain distinct gates. The next workflow [cod4-lavapipe-touch.yml](../../.github/workflows/cod4-lavapipe-touch.yml) issues the same seven Android touch events on the Lavapipe 3D scene for further validation.
- All original binary game data were staged temporarily on disposable GitHub runners, never uploaded within the reports or artifacts. Check redistribution rights for already-public third-party release binaries.

## External technical references

Android's official emulator documentation lists `lavapipe`, `swiftshader` and `swangle` as supported emulator GPU modes: https://developer.android.com/studio/run/emulator-acceleration

This is a **test-environment breakthrough**, not a finished or redistributed game.


## Follow-up: real-color scene plus seven Android touch inputs

**Run [40056652935](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40056652935) is fully GREEN as an *execution test*.** The previous run 40055971407 collected valid visual/input evidence but its workflow failed on an incorrectly split shell heredoc during report validation. The report validator was moved to a standalone script and the rerun passed.

- The original APK imported the same 21-file subset, started the 3D mission scene in **natural colors**, and remained active after the touch sequence.
- Native on-screen inputs **delivered successfully** through ADB: look right, virtual joystick move right, fire, aim/ADS, reload, jump, and crouch (7/7 input-injection commands returned exit code 0).
- The rendered-world center changed **98.70%** after a rightward look swipe, and **14.76%** after the joystick drag, supporting a visual camera/movement response. Some of the difference can be caused by animation or delayed scene changes; no internal player-coordinate telemetry exists.
- After fire, aim, reload, jump and crouch **no large central world-crop visual changes** were measured. That is neither proof they work nor proof they fail, particularly with single short presses and software rendering at extremely low FPS.
- The campaign process was still alive after all seven touch events; real screenshots of each state are in artifact `cod4-lavapipe-real3d-touch` on run 40056652935.
- Android emulator host logs on that run included **189,739 occurrences of `glUniform4fv:3993 error 0x502`**; the source of these OpenGL invalid-operation errors remains unidentified. That many log errors indicate serious rendering trouble but do not prove precisely which native shader or which FPS cost.
- The screenshot HUD showed around **2–4 FPS**; the result is **NOT** a usable framerate in the current x86_64 software-GPU test. This test does not benchmark ARM64 physical hardware.
- We have still **not** verified correct shot emission, ammo decrement, reload animation, ADS transition, jump/crouch physics, map completion, multiplayer or a Zombies game.

**Result labels:** 3D world colors ✅; scene onscreen ✅; seven ADB gestures delivered ✅; game process alive ✅; functional weapon/locomotion behavior ❔; smooth FPS ❌; physical ARM64 result ❔.
