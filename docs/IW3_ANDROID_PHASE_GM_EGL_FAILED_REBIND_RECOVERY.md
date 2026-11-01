# IW3 Android Phase GM — failed EGL surface-rebind recovery (NOT GAME)

Date: 2026-11-01. Scope: original KisakCOD IW3 Android EGL platform module, not a substitute engine.

## Starting evidence

PR #4 remained open and unmerged at the start of this pass, head `eec4e1f41e719d6410535acf2d91d37393e2cc2d`. Renderer probe run [41287506542](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41287506542) completed its *probe* jobs, but explicitly reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. First compiler errors included incomplete `IDirect3DSurface9` in `r_utils.h`, missing `__rdtsc`, and Win32/D3D9 calls. A green diagnostic workflow is not a passing full renderer build.

## Actual defect fixed

In `R_AndroidEglReplaceWindow()`, failure of `eglMakeCurrent` for a candidate replacement EGLSurface immediately destroyed the candidate, assuming the previous EGL binding was still current. Some driver/error paths can leave the render thread unbound instead. This broke subsequent `R_AndroidEglPresent()` and `R_AndroidEglRefreshSize()` despite returning failure and preserving the old surface in the provider state.

The original IW3 Android EGL platform code now attempts to restore the previous draw/read EGLSurface and context before destroying a failed candidate. The old window reference, old surface, and published width/height are retained. No D3D9 emulator or replacement renderer was introduced.

## Regression

The existing host ASan/UBSan test `tests/test_iw3_android_renderer_egl_lifecycle.py` now injects a failure where `eglMakeCurrent` clears the previous binding. The test requires restoration of the old EGLSurface, no leaked native-window reference, and subsequent successful window replacement. This is a mocked EGL failure injection, **not** proof of real-device rendering.

Source commit: `c16bd7d7d05173f35f8f58de35ed043e07cc1794`.
Regression commit: `f17f580aa8786e249f97afede7db9213b390e045`.

## Explicit incomplete gates

- `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` at baseline.
- `IW3_RENDERER_BACKEND_LINKED=false`.
- `IW3_RENDERER_FRAME_PROVEN=false`.
- `IW3_REAL_MAP_LOADED=false`.
- `IW3_GAMEPLAY_PROVEN=false`.
- `IW3_PLAYABLE_APK=false`.

Next priority is resolving the **actual** D3D9/Win32 boundary in `r_init.cpp` and implementing authentic IW3 draw/material/geometry translation over GLES3, then validating the entire engine and real map/weapon/actor execution on an ARM64 device. JNI diagnostics and EGL-only tests cannot close any gameplay gate.
