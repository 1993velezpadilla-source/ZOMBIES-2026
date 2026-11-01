# Phase GJ — EGL Surface replacement without losing original Android IW3 context

Date: 2026-11-01 UTC. Scope: KisakCOD original source, `src/gfx_d3d/r_android_egl.{h,cpp}` and host regression. **NOT A PLAYABLE GAME.**

## Baseline / blocker

Prior head `d92dde1b931768f965081ef302a5ebce7452ffba`, renderer workflow [41277720437](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41277720437): both jobs successful, but the `r_init.cpp` compile step is a **non-failing diagnostic probe** and still reports `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. D3D9/Win32/x86 dependencies remain. EGL platform provider linking alone is not a renderer or gameplay.

The existing EGL provider could initialize and resize an existing surface but could not switch to a newly created `ANativeWindow` when Android destroys/recreates its Surface. Full teardown would discard the existing GLES3 context and any future GL resources.

## Changes

- Keep the selected `EGLConfig` and native visual ID in the provider's state, resetting both on teardown.
- Add `R_AndroidEglReplaceWindow`: owning render thread only, validates the original context and read/draw surfaces, acquires the replacement window, configures the native pixel format, creates and validates a new EGL window surface **before** switching the existing ES3 context to it.
- On setup/query/bind failure, destroy only the candidate surface, release only the candidate window, and leave the original current surface and dimensions untouched. On success, publish the new surface and dimensions, destroy the old EGLSurface and release the old ANativeWindow reference.
- Extend the unchanged-source host lifecycle regression with a foreign-thread rejection, failure injection at native format selection, window surface creation, EGL dimension query, and context binding; validate no window-reference leaks and successful presentation after replacement.

This is **not** wired into an Android Activity/engine render loop yet. It does not solve `EGL_CONTEXT_LOST`, context restoration, or the missing D3D9-to-GLES draw backend.

## Validation and acceptance

Source commits: `0f14f39c3b77e725d94e540a3a692ae9d4f1a50a`, `4620c78d9d33f0e62ae248f0b387bbc386b0a551`, `6cf6a02ccb8fd887517731237bb0c0f72c08d4bc`. CI symbol assertion: `1a6c9d652c1262cc2b35d3f004a709924c64163e`.

CI workflow: [renderer-init-arm64](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/workflows/iw3-renderer-init-arm64.yml). Final verified run for commit `1a6c9d652c1262cc2b35d3f004a709924c64163e`: [41277984555](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41277984555), **both jobs success**. Host regression: **10/10 tests OK** under ASan/UBSan, including injected failures and foreign-thread Surface replacement rejection. Android NDK linked EGL provider ELF64/AArch64 with `-Wl,--no-undefined`; `llvm-nm -C` explicitly found `R_AndroidEglReplaceWindow(IW3AndroidEglContext*, ANativeWindow*)`. The diagnostic full original `r_init.cpp` compile **still fails** (`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`, compiler_exit=1) on D3D9 incomplete types, Win32 APIs and `__rdtsc`. `IW3_ANDROID_EGL3_PLATFORM_PROVIDER_LINKED=true` is not real-device rendering.

Required to finish: compile/link original `r_init.cpp`, integrate a GLES backend for original material/geometry/draw commands, connect lifecycle to native Android runtime, load real map assets, and demonstrate on-device touch-controlled original weapons/actors and gameplay.

`IW3_RENDERER_FRAME_PROVEN=false` · `IW3_REAL_MAP_LOADED=false` · `IW3_GAMEPLAY_PROVEN=false` · `IW3_PLAYABLE_APK=false`. Keep PR #4 open; do not merge to main.
