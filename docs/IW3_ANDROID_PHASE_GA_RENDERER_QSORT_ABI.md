# IW3 Android phase GA — original renderer qsort callback ABI

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4.

## Authentic code changes

Updated `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`, without a renderer replacement:

- `R_CompareRefreshRates` and `R_CompareDisplayModes` now take `(const void *, const void *)`, matching the callback type required by C/C++ `qsort`. The previous calls cast incompatible typed comparator function pointers; calling through that cast has undefined behavior, independently of the CPU architecture.
- Preserve the existing unsigned comparison ordering (including extreme `uint32_t` values). Display-mode comparison reads actual `_D3DDISPLAYMODE` members (`Width`, `Height`, `RefreshRate`) rather than treating the struct as an array of integers (avoids C++ object-layout/type-punning undefined behavior).
- Replace the hard-coded qsort strides (4 and 16 bytes) with `sizeof` of the corresponding actual array elements.

## Regression

Extended `tests/test_iw3_android_renderer_display_modes_lp64.py`. Its LP64 host harness extracts the **actual renderer functions**, asserts the exact callback function-pointer types, invokes both callbacks through real `qsort`, verifies mode and refresh-rate ordering, and retains existing display enumeration tests. CI workflow: `.github/workflows/iw3-renderer-init-arm64.yml`, which runs the renderer test family under AddressSanitizer and UndefinedBehaviorSanitizer.

Commits: `adc82cd93354ad55d588af789258eba99a3e6782` (engine) and `4d810899b7316806fa6748de5def0165527fb6f1` (regression).

## Honest build/runtime gate

The latest **prior** complete AArch64 `r_init.cpp` probe reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`: original Direct3D 9 interfaces, Win32 calls and x86 `__rdtsc` still block compilation. The renderer backend is **not** linked. This change addresses the qsort callback ABI only, not the D3D9-to-Android rendering backend.

Verified host CI on commit `4d810899b7316806fa6748de5def0165527fb6f1`: [renderer workflow run 41247266560](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41247266560), job `renderer-tracking-host` (job ID `124673231490`) **success**, `Ran 8 tests in 5.260s`, `OK`. The new display-mode callback ABI regression ran under ASan/UBSan and passed. The separate full `r_init.cpp` AArch64 compile-probe job was still running when this note was updated; a successful host job does not imply an Android renderer build. No original IW3 renderer frame, real map load, touchscreen gameplay or actors/weapons in an ARM64 APK have been demonstrated.

`IW3_PLAYABLE_APK=false`. Do not merge PR #4 to main; do not advertise the JNI diagnostic as a playable game.

## Follow-up on original object layout

Further commits `7abd5e23bcd92f5426c8eeceea2bf3a89ca0a8f7` and `b481d4f8ec93d911c0d2ae7930bb1d8f00ca5818` remove struct-member type-punning and make the host harness define the genuine 16-byte `_D3DDISPLAYMODE` layout. The final source/test commit `b481d4f8ec93d911c0d2ae7930bb1d8f00ca5818` was independently checked: [renderer CI run 41247357569](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41247357569), host job `124673454343`, **8/8 tests passed** (`Ran 8 tests in 1.674s`, `OK`), including the genuine renderer comparator extraction and ASan/UBSan harness. The separate AArch64 full-renderer compile probe was still in progress at inspection time; this is not an Android renderer success.
