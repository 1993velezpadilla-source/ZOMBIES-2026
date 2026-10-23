# COD4 Android vs PC C4 — compatibility preflight

**Scope:** directory structure, required asset names, APK architecture and compiled import strings. **NOT** an Android runtime or gameplay test.

## Static checks

| Check | Status | Evidence |
| --- | --- | --- |
| original-zip-structure | **PASS** | PC package recognized, 215 files directly in outer ZIP |
| main-directory | **PASS** | 14 numbered IW package(s) found |
| campaign-critical-paths | **PASS** | main/iw_00.iwd=True, zone/spanish/code_post_gfx.ff=True, zone/spanish/common.ff=True, zone/spanish/ui.ff=True |
| multiplayer-critical-paths | **PASS** | main/iw_00.iwd=True, zone/spanish/code_post_gfx_mp.ff=True, zone/spanish/common_mp.ff=True, zone/spanish/ui_mp.ff=True |
| spanish-zone-coverage | **PASS** | Fastfile localization folders: ['spanish']; main language variants: ['spanish'] |
| android-native-abi | **PASS** | Native Android libraries: 8 under arm64-v8a |
| apk-import-references | **PASS** | Compiled Android app references 'Import the complete campaign files' and 'main/iw_00.iwd' |
| asset-folders-preserved | **PASS** | Source root folder 'Call of Duty 4 Modern Warfare/' contains main/ and zone/spanish/ |
| iwd-catalog | **PASS** | 22 nested IWDs, 24,104 entries, 0 errors |
| apk-fastfile-headers-available | **PASS** | Inspected 3 APK bundled COD4X .ff headers |

PC installation: **215** files, **14** main IWD banks, **72** zone fastfiles.
Language zone directories: spanish; localized main IWDs: spanish.

## What's NOT proved
- **UNVERIFIED — Android app imports and loads this Spanish game installation:** Requires installing APK on authorized ARM64 Android device and testing file import and campaign launch.
- **UNVERIFIED — Game rendering, crashes, frame rate, audio, touchscreen and GPU driver:** No device execution was performed; those properties cannot be confirmed by archive inspection.
- **RISK — Spanish localization while APK mentions zone/english:** Source has zone/spanish/ but no zone/english/. Runtime engine may support Spanish via setting; this was not tested.
- **LEGAL — Public redistribution:** Do not assume rights to publicly distribute proprietary Call of Duty files or third-party APKs.

## Next real-world test requirements

On an ARM64 Android test device that you control, install the APK only after evaluating its provenance and security. Use a legally obtained compatible copy of the PC game and the app's supported in-app import flow. Preserve the **main/** and **zone/** subdirectories, and verify that Spanish content is accepted. Capture the app's import result, any errors, and a launch/frame-rate log. Don't publish or copy licensed assets into new public repos for this test.

**Machine-readable report:** [android-pc-compatibility.json](android-pc-compatibility.json).
