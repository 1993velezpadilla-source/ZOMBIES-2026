# IW3 Android phase GA — original renderer qsort callback ABI

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4.

## Authentic code changes

Updated `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`, without a renderer replacement:

- `R_CompareRefreshRates` and `R_CompareDisplayModes` now take `(const void *, const void *)`, matching the callback type required by C/C++ `qsort`. The previous calls cast incompatible typed comparator function pointers; calling through that cast has undefined behavior, independently of the CPU architecture.
- Preserve the existing unsigned comparison ordering (including extreme `uint32_t` values), with explicit typed reads inside the comparators.
- Replace the hard-coded qsort strides (4 and 16 bytes) with `sizeof` of the corresponding actual array elements.

## Regression

Extended `tests/test_iw3_android_renderer_display_modes_lp64.py`. Its LP64 host harness extracts the **actual renderer functions**, asserts the exact callback function-pointer types, invokes both callbacks through real `qsort`, verifies mode and refresh-rate ordering, and retains existing display enumeration tests. CI workflow: `.github/workflows/iw3-renderer-init-arm64.yml`, which runs the renderer test family under AddressSanitizer and UndefinedBehaviorSanitizer.

Commits: `adc82cd93354ad55d588af789258eba99a3e6782` (engine) and `4d810899b7316806fa6748de5def0165527fb6f1` (regression).

## Honest build/runtime gate

The latest **prior** complete AArch64 `r_init.cpp` probe reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`: original Direct3D 9 interfaces, Win32 calls and x86 `__rdtsc` still block compilation. The renderer backend is **not** linked. This change addresses the qsort callback ABI only, not the D3D9-to-Android rendering backend.

The new-commit CI is the authoritative source for regression results; do not count a queued or running job as passed. No original IW3 renderer frame, real map load, touchscreen gameplay or actors/weapons in an ARM64 APK have been demonstrated.

`IW3_PLAYABLE_APK=false`. Do not merge PR #4 to main; do not advertise the JNI diagnostic as a playable game.
