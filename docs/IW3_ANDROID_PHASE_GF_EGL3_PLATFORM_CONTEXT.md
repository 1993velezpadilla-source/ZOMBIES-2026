# IW3 Android phase GF — real EGL3 platform context (NOT a renderer or game)

Date: 2026-10-31 Puerto Rico / 2026-11-01 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Baseline and verified blocker

At head `f5f0c8a159e609327ab81fe903e181d69ef1816a`, the original `r_init.cpp` AArch64 compile probe still reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` in [run 41264947138](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41264947138). The compile diagnostics include incomplete Direct3D9 COM interfaces (`IDirect3DSurface9`, `IDirect3DDevice9`, `IDirect3D9`), Win32 `GetActiveWindow`/`MessageBoxA`/`ShellExecuteA`, and x86 `__rdtsc`. The existing `r_android_display.cpp` only reads actual Surface dimensions/refresh and builds original IW3 dvars; **there was no Android EGL context/swapchain provider**.

## Concrete implementation

Added `third_party/KisakCOD/src/gfx_d3d/r_android_egl.h` and `.cpp` in the genuine KisakCOD source tree, with:
- `R_AndroidEglCreate`: acquires the caller's actual `ANativeWindow`, requests an EGL window configuration with ES3, RGBA8, depth24/stencil8, applies the real Android native visual ID, creates an EGL window surface and GLES3 context, makes it current, and queries actual surface dimensions. Failure paths release every acquired object.
- `R_AndroidEglPresent`: only swaps when the provider's EGL context and draw surface are current on the calling thread. A successful swap **does not** imply original IW3 draw submission or a visible scene.
- `R_AndroidEglDestroy`: unbinds only its own current context, destroys its context/surface, terminates its EGL display, releases its acquired native window, and resets its state. The provider cannot be copied and requires render-thread lifecycle serialization.

This is **real Android EGL API integration**, not a fake Direct3D9 device, a graphics translation layer, or a replacement game engine. The original IW3 geometry, material/shader, texture, command submission and render thread are not yet connected.

## Tests and CI gates

Added `tests/test_iw3_android_renderer_egl_lifecycle.py`. It compiles the **unmodified** provider source on LP64 host against mocked EGL/ANativeWindow functions and executes create/present/destroy, failure injection for nine EGL/native-window stages, ownership accounting, duplicate-create rejection, wrong-current-context rejection, swap failure and idempotent cleanup under ASan/UBSan. This test **does not** render a scene.

Extended `.github/workflows/iw3-renderer-init-arm64.yml` to include the new source and test in its triggers, execute the host regression, and build/link an actual ARM64 `.so` against Android NDK `libEGL` and `libandroid` with `-Wl,--no-undefined`, verifying exported platform provider symbols. A linked provider is **not** the linked IW3 renderer.

New CI: [run 41266136663](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41266136663) (check final job conclusions before treating tests as passed).

## Unmet gates and next engineering step

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` until the full original source compiles.
`IW3_RENDERER_BACKEND_LINKED=false`.
`IW3_RENDERER_FRAME_PROVEN=false`.
`IW3_REAL_MAP_LOADED=false`.
`IW3_GAMEPLAY_PROVEN=false`.
`IW3_PLAYABLE_APK=false`.

Next: connect the real Android native window and EGL lifecycle to the original renderer's render thread and implement the actual IW3 D3D9-to-GLES3 material, texture, geometry and draw-command translation (or a verified equivalent native backend). Continue integrating original `Com_Init`, FastFile/map assets, touch input and gameplay; do not merge PR #4 to main until a real ARM64 device proves all gates. Do not confuse JNI diagnostics or a context-only `.so` with a playable APK.
