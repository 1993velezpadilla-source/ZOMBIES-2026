# COD4 Android: controlled GPU A/B — red rendering incident

**GitHub Actions run:** [40053316280](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40053316280). Both isolated Android 15 emulator jobs finished successfully.

## Controlled comparison

Both jobs used the same unchanged COD4.apk and temporary 21-file original PC-data subset (~2.42 GB), same x86_64 Android emulator/ARM64 translation, same menu navigation; **only Android emulator GPU backend was changed**.

| Measured property | -gpu swiftshader_indirect | -gpu swangle |
| --- | --- | --- |
| Google emulator GLES backend | OpenGL ES 3.0 Google SwiftShader | OpenGL ES 3.1 ANGLE (Vulkan SwiftShader) |
| Real COD4 Spanish-language campaign menu | **Strong red tint** | **Normal gray/white appearance** |
| Center of menu: red-dominant pixels, computed on screenshot | **83.45%** | **0.00%** |
| Center of menu mean RGB | **[62.52, 0.00, 0.00]** | **[62.87, 63.78, 63.73]** |
| Native game campaign process alive at end | Yes | Yes |
| Process TOTAL PSS at end (single meminfo reading) | 1,605,463 KB (~1.53 GiB) | 1,169,557 KB (~1.12 GiB) |
| 3D level scene visible within this 100-s observation | **No**, HUD drawn over gray/black frame | **No**, gray/black loading screen |
| Full game color/shader defect corrected | **Not verified** | **Not verified** |
| Real physical ARM64 device FPS | Not tested | Not tested |

**Strong finding:** The menu-level red tint **changes drastically with the GPU backend**, while the APK and imported assets stay the same. This implicates the emulator GLES compatibility/rendering path rather than a missing Spanish texture as the only cause. **It does not prove a specific engine shader defect or explain any redness during actual 3D gameplay**, and **does not make the game playable**.

The original baseline [run 40041071926](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40041071926) did produce a 3D scene and HUD under SwiftShader, with severe red tint and very low FPS. In this controlled A/B neither backend completed rendering a 3D world by 100 seconds, so **the A/B supports menu color compatibility, not gameplay GPU performance comparisons**.

SwANGLE used an ANGLE-on-Vulkan SwiftShader path. The existing original setup used Google SwiftShader's GLES 3.0 translator; GLES backend strings were confirmed from Android SurfaceFlinger. The colored screen comparison is supported by **real Android screenshots**, not generated illustrations.

### Additional observations

- The software GPU is still emulated and ARM64 engine is translated on an x86_64 host; this is not a proxy for a physical Qualcomm Adreno or ARM Mali device.
- The PSS values are single snapshots from separate emulator runs, not a statistically controlled memory improvement or memory leak measurement.
- Emulator logged intermittent `Failed to find ColorBuffer` and `Failed to bind to texture: invalid color buffer`; a causal connection to the red image has **not** been established.
- GPU backend selection (`-gpu swiftshader_indirect` vs `-gpu swangle`) is an **emulator flag**, not a setting of the compiled user-facing COD4 APK. We have not modified the APK or engine.
- Both APK test runs used temporary original input game assets from the user's existing release, deleted after the run. GitHub artifacts contain screenshots/logs/metrics only.

### Evidence

[Run 40053316280](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40053316280) has two artifact files:
- `cod4-gpu-swiftshader_indirect` — real `05-campaign-probe.png` (red), logs, `renderer-diagnostic.json`.
- `cod4-gpu-swangle` — real `05-campaign-probe.png` (normal colors), logs, `renderer-diagnostic.json`.

Next gate: observe whether the SwANGLE renderer can finish a 3D level after a longer wait, then test frame latency and reliable player input in a physical ARM64 device.

## Follow-up: extended SwANGLE level loading

[Workflow run 40053989682](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40053989682) repeated the same Android 15 test with SwANGLE and waited another three minutes after the earlier ~100-second baseline observation.

- Authentic COD4 menu remains **normally colored**, unlike the red SwiftShader menu.
- At +60 and +120 seconds the app showed a dark loading screen. At **+180 seconds additional**, it displayed **a mobile control HUD on dark gray**, but **no verified 3D world geometry**. This is **not** a successful level rendering/gameplay result for SwANGLE.
- The campaign process stayed alive (PID 4868); no Android fatal exception or SIGSEGV appeared in the collected workflow log.
- During the prolonged render, GitHub Actions recorded **4,535** emulator log occurrences matching `glUniform4fv:3993 error 0x502` (OpenGL `GL_INVALID_OPERATION`). There were also two instances each of `Failed to find ColorBuffer` and `Failed to bind to texture: invalid color buffer`. These are serious renderer-compatibility clues, **but do not prove a particular cause in the unavailable native game source code**.
- Process total PSS single-timepoint series: **1,382,573 KB → 1,526,528 KB → 1,483,977 KB** over the extended observations; swap PSS rose to **436,533 KB**. This does not establish a steady memory leak, but the memory pressure is notable.
- Full engine performance and 3D view correctness remain **RED/UNVERIFIED**, even though the menu color issue was ameliorated by switching the emulator GPU backend.

The run uploaded no original game assets, only screenshots, meminfo and a JSON report in `cod4-swangle-extended-evidence`. The newest test's `swangle-extended-180.png` is visual confirmation of HUD-on-gray, not a rendered level.

**Decision:** Keep SwANGLE as a diagnostic reference for emulator menu-color correctness, **not** as a proven fix for the whole APK. Native physical-device Adreno/Mali testing and access to engine renderer source/build options are necessary to pursue a real shader fix; do not mislabel the emulated menu improvement as a solved game.
