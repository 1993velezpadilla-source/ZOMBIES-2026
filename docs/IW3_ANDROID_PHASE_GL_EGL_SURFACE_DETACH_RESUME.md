# IW3 Android phase GL — EGL Surface detach / resume (not a game)

Date: 2026-11-01. Branch: `feature/iw3-native-android-arm64-20261025`, PR #4. All changes are in the authentic KisakCOD tree. No Godot, substitute engine, simulated game, or JNI diagnostic APK is claimed as playable.

## Evidence reviewed before editing

The most recent completed renderer probe on commit `60fcd2578c99440af6ad2458873ab45986bf9a16` was [Actions run 41285313342](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41285313342). The job succeeded **as a diagnostic workflow**, while the full original `r_init.cpp` AArch64 compilation explicitly reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. First compiler errors include `r_utils.h` calling `IDirect3DSurface9::Release()` on an opaque D3D type, `__rdtsc`, Win32 window/dialog functions, and original Direct3D device/mode enumeration. These are genuine renderer porting blockers, not solved by compiling the EGL provider.

## Concrete bug / change

Android can call Surface destruction before a replacement Surface exists (pause, rotation, background). The existing `R_AndroidEglReplaceWindow` requires the old surface and ES3 context to be current, so the engine could not cleanly release a lost Android window while preserving its original graphics context for later resume.

- Added `R_AndroidEglDetachWindow` in `third_party/KisakCOD/src/gfx_d3d/r_android_egl.cpp/.h`. It rejects foreign threads and invalid/non-current contexts, unbinds EGL before destroying the window surface, releases the acquired `ANativeWindow`, clears cached dimensions, and **retains** EGLDisplay/EGLContext/config for later reattachment.
- Updated `R_AndroidEglReplaceWindow` to accept either an attached current surface or the explicitly detached context. It refuses to steal another EGL context and reuses the genuine existing ES3 context on reattachment.
- The detach path rejects unbind failure without touching state and attempts to restore the prior binding if surface destruction fails.
- Extended `tests/test_iw3_android_renderer_egl_lifecycle.py` with owner-thread checks, unbind/destroy failure paths, detached-state rejection of draw/present, rejected foreign binding, failed reattachment and successful resume, plus balanced `ANativeWindow` references.
- Extended `.github/workflows/iw3-renderer-init-arm64.yml` to require the new `R_AndroidEglDetachWindow` symbol in the **real NDK-linked AArch64 shared object**.

## Proof gates (must not conflate)

The host test uses mocked EGL calls under ASan/UBSan; the NDK compile checks only binary architecture and linkage. Neither proves an Android display frame or the real IW3 renderer. The unchanged `r_init.cpp` compile probe is intentionally still diagnostic.

- `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` until new CI proves otherwise.
- `IW3_RENDERER_BACKEND_LINKED=false`
- `IW3_RENDERER_FRAME_PROVEN=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

## Next actual blocker

Port original D3D9 material, shader, geometry, and draw-command implementation to a real GLES3 backend, then integrate the renderer initialization with the Android engine lifecycle. Separately address Win32 and x86 dependencies in `r_init.cpp` **without fake D3D stubs**. Full-device evidence must show the authentic IW3 engine loading map assets and rendering them, accepting touch, and running real actors/weapons before claiming playable.
