# COD4 Android — Native Touch Control Gauntlet

**Run:** [40048577930](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40048577930) · **Date:** 2026-10-24 UTC.

## Actual test, not a mockup

This run reused the 21 original game-resource files (2,419,742,180 bytes) from the previously audited C4 package in a **temporary, offline Android 15 emulator**. It launched the APK's original launcher, imported the same test data, opened the original 3D campaign environment, and executed touchscreen input through Android Debug Bridge.

After opening a scene, the runner captured a baseline screenshot and issued these inputs in sequence:

| Native screen control input | ADB delivered | Difference in cropped world center vs preceding image |
| --- | --- | ---: |
| Swipe right to turn view | Yes, exit code 0 | 98.71% |
| Drag left virtual joystick to right | Yes, exit code 0 | 8.84% |
| Fire tap | Yes, exit code 0 | 16.81% |
| Aim/ADS tap | Yes, exit code 0 | 11.25% |
| Reload tap | Yes, exit code 0 | 36.94% |
| Jump tap | Yes, exit code 0 | 36.79% |
| Crouch tap | Yes, exit code 0 | 51.14% |

These percentages are image pixel differences only, **NOT proof that movement, shooting, ADS, reload, jump, or crouch worked as intended**. Differences may be driven by shader/animation changes even when a tap has no effect. The first baseline was largely black, while subsequent frames showed a strongly red-tinted scene viewed at sharply differing rotations and positions. This makes action-by-action attribution unreliable.

## What can genuinely be marked GREEN

- The complete automated sequence **ran to completion**, and every ADB touch injection returned code 0.
- All eight state screenshots (baseline + seven action results) were captured from Android. They were not generated illustrations.
- The original ARM64 COD4 game process **was still alive** after all seven injected actions (`pidof com.cod4.firstmission:sp` returned process ID 4813).
- The app remained visible in Android's activity status. No copyrighted game-data archives were attached to the workflow artifacts.
- The last-run game screen still has native Chinese-labeled FPS mobile controls in landscape mode.

## Blockers — not GREEN

- **Red rendering issue remains**: the central image crop was almost entirely red (green/blue mean roughly 1.7 each in the sampled frames), indicating a major graphical issue not diagnosed from pixel data alone.
- **Frame-rate remains inadequate** in the emulated ARM64-on-x86_64 environment. Previous screenshots observed around 2–4 FPS, not a physical phone benchmark.
- **Game controls' actual action semantics not verified**: no direct telemetry of player coordinates, ammo count, hit detection, ADS field of view, or weapon state. The automated controls are sequential and don't validate multitouch simultaneous gameplay.
- **Not verified**: complete 7.02 GB data import, one full mission, native ARM64 physical-device FPS, Zombies-specific rounds, Godot editor/project.

## Next technical gate

Run a **physical ARM64 Android device** test with performance counters and permission-checked original game data, and instrument actual gameplay state if source/build permits. Distinguish GPU shader/tone-map faults from camera injury overlay and from texture-loading faults. The original APK includes only compiled binaries: the repository does not contain its native engine source code for fixing the shader directly.

**Evidence archive:** GitHub Actions artifact `cod4-real-source-import-evidence` in [run 40048577930](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40048577930). Files include `touch-control-report.json`, `09-control-baseline.png`, and `10-control-*.png`.

**Accuracy note:** GitHub Actions success means the scripted test completed; it does **not** imply seven controls were functionally validated.
