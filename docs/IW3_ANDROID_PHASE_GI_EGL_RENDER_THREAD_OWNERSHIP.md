# IW3 Android phase GI — EGL render-thread ownership enforcement (NOT GAME)

Date: 2026-11-01 (UTC). PR #4; branch `feature/iw3-native-android-arm64-20261025`.

## Baseline and concrete portability defect

Reviewed genuine KisakCOD source `third_party/KisakCOD/src/gfx_d3d/r_android_egl.cpp/.h` and the current renderer workflow. The previous GH provider required all calls on the same engine render thread **in comments only**. `R_AndroidEglDestroy()` would nevertheless call `eglDestroyContext`, `eglDestroySurface`, `eglTerminate` and `ANativeWindow_release` when called from a different Android thread. It checked only whether its context was current **on the caller's thread**, which cannot establish ownership of a context current on another thread. Surface-destroy callbacks on the UI thread therefore risk invalidating resources still used by the render thread.

At baseline [renderer workflow 41271203367](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41271203367), the authentic full `r_init.cpp` compile still reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. Compiler errors include incomplete Direct3D9 interfaces, missing Win32 window calls, and x86 `__rdtsc`. An EGL provider is not a replacement renderer.

## Implementation

- Store the creator's `pthread_t` and an explicit validity flag in `IW3AndroidEglContext`, without copying the context.
- Set ownership before any EGL/ANativeWindow acquisition so all partial-creation failures can clean up on the correct thread.
- Reject `RefreshSize`, `Present`, and `Destroy` from foreign threads. Foreign-thread destruction returns `false` **without modifying or releasing the live EGL state**; the Android lifecycle must dispatch cleanup to the owner thread.
- Change `R_AndroidEglDestroy` to return `bool` to make wrong-thread cleanup failure observable. Preserve idempotent cleanup after success and partial creation failure. Reset ownership only after cleanup.
- Extend `tests/test_iw3_android_renderer_egl_lifecycle.py` to compile the actual production provider with `-pthread` and host ASan/UBSan. A real `std::thread` attempts all three foreign-thread operations and asserts no surface/context/window release; then the owner thread performs successful cleanup. Also verify ownership resets on every failure-injection path.

## Evidence and limits

Code commits: `364ca8738e5b08fdbdc36a767f55eecdaf558e96`, `3e2f2098f02e2176abb51b79b6908fb770cbad8c`, `dd6f228df7a719be7470e13c7d387cdf7702c62b`.

New renderer CI run: [41277583886](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41277583886). **Await its actual completion before claiming tests pass.** The workflow is a host regression and AArch64 compile/link probe, not a real-device renderer/gameplay test. The independent Android NDK `libiw3-android-egl-platform-arm64.so` is only a platform EGL provider.

Remaining gates: `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` at baseline; `IW3_RENDERER_BACKEND_LINKED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; `IW3_PLAYABLE_APK=false`.

Next: connect an Android-native GLES3 backend to the **original** IW3 material, geometry and draw-command path; resolve the genuine `r_init.cpp` Direct3D9/Win32/x86 dependencies and integrate with `Com_Init`, real map assets, original touch-driven input and SP gameplay. Keep PR open and do not merge to main.
