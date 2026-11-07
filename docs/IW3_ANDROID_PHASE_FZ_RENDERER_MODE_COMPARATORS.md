# Phase FZ — authentic IW3 renderer display-mode comparator integrity (2026-10-31)

## Scope and baseline

PR #4, branch `feature/iw3-native-android-arm64-20261025`, baseline `745f28defe28143d5106e382a8e8fbecc0398619`. The 19 GitHub Actions workflows associated with that baseline completed successfully; this is **not** evidence of an Android game. The renderer probe still records `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`, because the original renderer has unresolved Direct3D 9, Win32 and x86 dependencies.

## Real original-engine change

In `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`, corrected both original sorting comparators:

- `R_CompareRefreshRates`: compare DWORD values directly, not by subtraction that wraps at `UINT32_MAX`.
- `R_CompareDisplayModes`: lexicographic unsigned width/height/refresh comparisons without arithmetic overflow or implementation-defined unsigned-to-signed narrowing. Preserves the existing ordering contract and equality semantics.

The previous `1u - 0xffffffffu` comparison produced a positive result instead of negative, which violates the sort comparator contract. This is a real source-code defect independent of Android and can corrupt the order of mode enumeration. The change is confined to authentic KisakCOD renderer code; it does **not** replace or simulate the renderer.

## Regression

Expanded `tests/test_iw3_android_renderer_display_modes_lp64.py`, which extracts and executes five genuine renderer functions, to check antisymmetry and equality for both comparators at the 32-bit extremes, including width, height and refresh. Existing enumeration tests still cover sorted/deduplicated modes, the 256-mode cap and empty-mode rejection.

Local focused C++17 sanitizer smoke for the comparator functions: `LOCAL_COMPARATOR_ASAN_UBSAN_PASS` (ASan + UBSan). This smoke is **not** the full extracted-source CI test. GitHub Actions full test workflow for the new commit: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41240681415 (check its job result before interpreting success). Engine commit `064e512274ce7480138421ff5ff0caf5772b1a8b`; regression commit `6ef81510410d3e7dee0e7205863bea09c188c0fa`.

## Outstanding release gate

`IW3_PLAYABLE_APK=false`. The renderer `r_init.cpp` still cannot be compiled fully for Android ARM64 without an authentic Android graphics backend. No evidence of an Android `Com_Init` startup, map load, renderer frame, touch input, weapon/actor gameplay or installable playable APK exists. The JNI diagnostic APK must not be labeled as gameplay. Keep PR #4 open and unmerged; no Godot or substitute engine was used.
