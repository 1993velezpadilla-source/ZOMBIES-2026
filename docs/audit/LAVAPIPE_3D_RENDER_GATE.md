# COD4 Android — Lavapipe breakthrough (2026-10-24)

**Workflow:** [40055353083](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40055353083). Both backend test jobs concluded **success** as test executions. This is evidence of renderer progress, **not** a playable, optimized Android build.

## Verified result

In a disposable **Android 15 x86_64 emulator using the ARM64 native bridge**, the unchanged third-party COD4.apk imported a **21-file, 2,419,742,180-byte subset** of the user's existing PC archive. All temporary game-data inputs were deleted after each job; evidence uploads contain only screenshots and logs.

The test compared `-gpu lavapipe` with `-gpu swiftshader` using the same APK and imported game data:

| Signal | Lavapipe | SwiftShader |
| --- | --- | --- |
| Android app and importer | PASS | PASS |
| Campaign process remained visible | Yes | Yes |
| Authentic COD4 **3D interior with visible walls, lights, textures, weapon and controls** by screenshot 40s | **PASS** | **NO** (gray/black) |
| Severe red tint in observed 3D screenshot | **Not observed** | 3D scene not rendered in this test |
| Mean RGB of center crop at ~100s | **[95.52, 92.19, 83.27]** | **[32.19, 32.29, 32.31]** |
| Red-dominant pixels in 3D center crop (~100s) | **0.00%** | **0.00%**, but scene was gray/black |
| Reported in-game FPS at 100s | **~4.2 FPS** | Unverified during this test |
| 3D game usable at normal speed | **NO** | **NO** |

At 40s the Lavapipe screenshot also showed real Spanish-language **COD4 campaign narrative text** and the tutorial mission scene. At 100s the actual engine screen showed the map, first-person weapon fragment, Chinese touch controls and Spanish-labeled in-world item `Gaz`; these screenshots were captured directly from the Android emulator, not generated.

## What changed, and what did not

- This is **not** a modified Android game or shader fix: **Lavapipe is a host emulator GPU backend selected through an emulator launch parameter**. It is not an option inside COD4.apk.
- SwANGLE previously made the **menu colors normal**, but the last [extended SwANGLE test](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40053989682) **still had no rendered 3D world after the observation window** and showed many GL errors.
- Lavapipe improved the **3D visual output** relative to the other tested software backends. However the **~4.2 FPS is nowhere near playable**, and neither the native ARM64 physical-device GPU nor multitouch inputs have been performance-qualified.
- The Lavapipe screenshot demonstrates **a 3D level loading and rendering**, not successful level completion, reliable shooting, ADS, dynamic navigation, or Zombies gameplay.
- The frozen/repeated scene and fixed camera across screenshots alone cannot establish gameplay responsiveness.
- A specific shader source-level root cause **is not identified**; the existing APK has native compiled libraries without a linked buildable engine source tree in this repo.

## Evidence and follow-up

The [successful GitHub Actions run 40055353083](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40055353083) has **two separate artifact packages**:

- `cod4-gles-lavapipe`: `08-loading-observe-040.png`, `08-loading-observe-100.png` (normal-colored 3D level), `renderer-diagnostic.json`, Android logcat.
- `cod4-gles-swiftshader`: same test window, gray scene without visible 3D level.

**Next gate:** run the same scripted touch-control probe on Lavapipe after the world appears, and examine whether motion/weapon operations change the actual world without treating random pixel changes as proof of gameplay. A physical ARM64 GPU test remains necessary.
