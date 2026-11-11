# IW3 Android phase GC — genuine renderer display-mode backend seam

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4. **Not a playable APK.**

## Verified baseline / next actual blocker

At pre-change commit `d5eadacd4ea444219766f3b2d96954baa1d27410`, the authentic `gfx_d3d/r_init.cpp` Android AArch64 compile probe still reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` (Actions run 41251635593). Its compiler diagnostics include incomplete Direct3D9 COM types, `Direct3DCreate9`, `D3DFMT_X8R8G8B8`, Win32 `GetActiveWindow` / `MessageBoxA` / `ShellExecuteA` / `IsWindow` / `DestroyWindow`, and x86 `__rdtsc`. A green audit job is **not** a successful renderer compile.

## Original-engine implementation

Previously, `R_EnumDisplayModes` combined the D3D9-specific `GetAdapterModeCount` / `EnumAdapterModes` calls with platform-independent IW3 mode sorting, resolution/refresh collection, bounded text formatting and dvar registration. The authentic sorting/registration code now lives in `R_BuildDisplayModeDvars()` and `R_EnumDisplayModes` still enumerates through D3D9 on Windows, then calls the original mode builder. This creates a narrow entry point for a future Android-native display-mode provider to populate the real engine's `dx.displayModes` / `dx.displayModeCount` and invoke its genuine dvar registration. **No Android display provider, graphics backend, fake D3D9 implementation, or substitute renderer has been added.**

The mode builder explicitly rejects `dx.displayModeCount > 256` before `qsort` or array traversal, protecting the fixed 256-entry engine buffer from a future native provider reporting too many modes. `r_init.h` exposes the function for a real platform integration.

## Tests and evidence

The existing `tests/test_iw3_android_renderer_display_modes_lp64.py` extracts and executes the genuine original functions under host ASan/UBSan. It now checks both the D3D9 enumeration route and the platform-neutral route with `dx.d3d9 == nullptr` and real mode values populated in `dx.displayModes`; it also checks that 257 entries are rejected. `tests/test_iw3_android_renderer_mode_text_bounds.py` continues to extract the same genuine formatting blocks, now from the new function. Workflow: `.github/workflows/iw3-renderer-init-arm64.yml`. CI run 41253408882 was triggered for this change; inspect its **renderer-tracking-host** job for actual regression results and **original-renderer-compile-probe** for the expected remaining backend errors. Do not claim these checks passed until the run is complete.

## Remaining playable gates

1. Implement a real Android native-window display-mode provider that fills the engine's mode array; no hardcoded/fake modes.
2. Implement or port a genuine graphics backend for IW3 geometry/material/texture/shader/draw paths. D3D9 interfaces and Win32 device/window calls cannot be silently stubbed.
3. Integrate `Com_Init`, real game assets/map loading, original client loop, live touch input and original weapons/actors on Android ARM64.
4. Capture device-side evidence of a genuine rendered scene and gameplay; produce a real installable APK only after those gates pass.

**IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false (baseline; new probe pending). IW3_RENDERER_FRAME_PROVEN=false. IW3_REAL_MAP_LOADED=false. IW3_GAMEPLAY_PROVEN=false. IW3_PLAYABLE_APK=false.**

PR remains open, not merged to main.
