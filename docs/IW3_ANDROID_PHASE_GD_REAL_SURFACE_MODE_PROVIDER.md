# IW3 Android phase GD — real Android Surface display-mode provider

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4. **Not a playable APK.**

## Baseline and actual blocker

At `802cd6e277f06aed3ab0ef70e34fbcbd9e2ea644`, the original renderer's `R_BuildDisplayModeDvars()` had been separated from Windows D3D9 mode enumeration, but Android did not have a native source of display modes. The `r_init.cpp` AArch64 compile probe in run 41253446790 still reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` (D3D9 COM interfaces, Win32 window calls, and x86 `__rdtsc`). Its green audit wrapper is not a renderer build.

## Original-engine implementation

Added `third_party/KisakCOD/src/gfx_d3d/r_android_display.cpp` and `.h`. The adapter accepts live Android `Surface` and `Display` objects, reads the real `ANativeWindow` dimensions and `Display.getRefreshRate()` through JNI, and passes the measured **current surface mode** to the original renderer's `dx.displayModes` / `dx.displayModeCount` and `R_BuildDisplayModeDvars()`. It rejects absent JNI objects, failed native-window acquisition, Java exceptions, surfaces below the original 640x480 minimum, non-finite refresh rates and invalid frequencies. JNI local references and native-window references are released. It does not hardcode 60 Hz, fabricate extra supported modes, initialize Direct3D9, or replace original IW3 sorting/dvars. The mode `Format` is explicitly zero/unknown because Android does not supply a D3D9 pixel-format enum; the original builder uses only Width/Height/RefreshRate.

**Integration boundary:** this function is not yet called by the Android Activity. It cannot be linked into the existing diagnostic JNI APK without the real `dx` state and `R_BuildDisplayModeDvars` symbol; doing so with stand-ins would misrepresent the engine. It must be invoked by the eventual genuine renderer initialization after a live Surface/Display exists. The current surface mode is not an exhaustive list of all OS-supported modes.

## Verification

- `tests/test_iw3_android_renderer_native_window_modes.py` extracts and executes the **unchanged provider function** on an LP64 host under ASan/UBSan. JNI and native-window calls are test doubles only; cases cover current dimensions/59.94->60 Hz/144 Hz, null inputs, invalid dimensions, NaN/infinity/zero/out-of-range refresh, Java failures and reference release.
- `.github/workflows/iw3-renderer-init-arm64.yml` now treats the new adapter's complete NDK AArch64 compilation and ELF symbol inspection as a **required** check, while retaining the original `r_init.cpp` compile probe's explicit negative status until D3D9 is actually ported.
- New workflow run triggered by `afe95d54af5ff070cdb738d2cbfb72becda579c7`: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41257776682 . **Pending** at documentation creation; do not report tests passing until inspected.

## Remaining gates

`IW3_RENDERER_BACKEND_LINKED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`. The native mode adapter is not a GPU backend. Still required: Android EGL/Vulkan or other actual graphics backend connected to original IW3 geometry/material/shader/texture/draw systems, integrated `Com_Init` and client frame loop, genuine map/asset loading, touch gameplay and device-side proof. No Godot, no substitute engine, no merge to main.
