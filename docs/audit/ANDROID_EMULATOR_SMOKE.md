# COD4.apk — real Android emulator startup test (2026-10-23)

**Result: GREEN for APK installation and launcher startup in a disposable emulator. Game/campaign loading remains UNVERIFIED.**

## Test environment

- Test workflow: [Android emulator COD4 startup and UI smoke test](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40032171064).
- Android **15** (SDK **35**), Google APIs x86_64 emulator.
- Supported ABIs reported: `x86_64,arm64-v8a`. ARM translation: `libndk_translation.so`.
- Unmodified `COD4.apk` (SHA-256 verified against original import).
- Network disabled in disposable emulator before launching. No user credentials or full PC game resources provided.
- Package: `com.cod4.firstmission`; activity: `.MainActivity`.

## What was actually proved

| Check | Verified |
| --- | --- |
| APK installation | **PASS** — `adb install` returned `Success` |
| MainActivity startup | **PASS** — `am start -W` returned `Status: ok`, `LaunchState: COLD` |
| Process/activity visible after launch | **PASS** — `dumpsys activity` includes the package |
| Crash in filtered logcat during observation | **None observed** (not a comprehensive stability guarantee) |
| Screenshot of running launcher | **PASS** — artifact `screenshot.png` |
| Importing `main/` and `zone/` content | **NOT TESTED** |
| Starting a campaign mission / multiplayer gameplay | **NOT TESTED** |
| Actual performance on physical ARM64 device | **NOT TESTED** |

The screen is a **Chinese-language COD4 Android launcher test build**. It explicitly offers **“Import game resources folder”**, mentions Steam 2007 original files, and calls out preservation of the `main/` and `zone/` directories. It also displays that `localization.txt` has not been imported. The menu claims **21 selectable stages**, but their loading is **not verified**.

A no-driver-package warning appears on this emulator: no preconfigured driver for this GPU; it falls back to the system driver. That is expected to require separate tests per Android GPU.

## Evidence and caveats

- Screenshot, install output, launcher output and filtered logcat are in the workflow artifact **cod4-android-emulator-smoke** on the [successful Actions run](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40032171064). The artifact expires according to Actions retention settings.
- The earlier static compatibility preflight reports **10/10 PASS**, including required `main/iw_00.iwd`, `zone/spanish/common.ff`, `ui.ff`, `code_post_gfx.ff`, the main MP fastfiles and native ARM64 libraries; [see preflight](ANDROID_PC_COMPATIBILITY.md).
- **Spanish-localized PC data vs Chinese-language launcher:** `zone/spanish` is present in the PC archive; import success in this APK is **not yet verified**. Do not rename Spanish `.ff` to English or Chinese as a shortcut.
- The public repository currently contains third-party proprietary game binary assets in Releases. Ensure redistribution rights before sharing further; neither the emulator test nor static compatibility grants rights.

**Interpretation:** The Android launcher actually starts. That is a genuine advance over static archive analysis, **but does not mean COD4 is playable on Android using this ZIP yet**, and does not supply source code for Zombies/Godot.
