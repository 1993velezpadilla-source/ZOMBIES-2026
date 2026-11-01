# IW3 Android phase GH — live EGL Surface dimensions and display ownership (NOT GAME)

Date: 2026-10-31 Puerto Rico / 2026-11-01 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Reviewed baseline and blocker

Baseline `80d9f2d12d8021f27634816529e3a4bc2690131a`. The genuine KisakCOD `r_init.cpp` Android AArch64 probe in [Actions 41266179705](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41266179705) completed its **audit**, but reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. Actual compiler diagnostics include incomplete `IDirect3DSurface9`/`IDirect3DDevice9`/`IDirect3D9`, `__rdtsc`, and Win32 window calls. The separate EGL platform-only provider compiled and linked; it is **not** the IW3 renderer.

The provider cached width/height only once at `eglCreateWindowSurface` time. Android may resize an existing EGL window surface during orientation, fold/unfold or multiwindow changes without a new `EGLSurface`; the original IW3 viewport must not be fed stale dimensions. The present path also checked the current context and draw surface, but not the thread's current EGL display.

## Implementation on authentic source

Updated `third_party/KisakCOD/src/gfx_d3d/r_android_egl.h/.cpp`:
- `R_AndroidEglRefreshSize` requires the provider's actual EGL display, context and draw surface to be current on the render thread. It queries `EGL_WIDTH` and `EGL_HEIGHT` from the real `EGLSurface`, rejects failed or nonpositive results, and publishes both dimensions only after both queries pass. A failure preserves the last valid dimensions.
- Initial EGL creation now uses this same validation, so the two paths cannot diverge.
- `R_AndroidEglPresent` additionally checks `eglGetCurrentDisplay` before swapping. This prevents accepting a context/surface match with a different current EGL display.

The API does **not** change IW3's viewport, does not draw, and does not create a new surface. The future renderer-owned frame loop must call it after Surface resize events, update original `vidConfig`/viewport appropriately, and coordinate EGL context/surface lifecycle with the Android UI thread.

## Verification and evidence

Extended `tests/test_iw3_android_renderer_egl_lifecycle.py` to execute the **unmodified production EGL source** against mocked EGL/ANativeWindow functions under LP64 host ASan/UBSan. The harness covers a portrait-to-landscape dimension change without replacing the surface, invalid/failed width and height queries preserving the last good size, wrong EGL display rejection, and existing create/swap/destroy and nine failure-injection cases.

The existing `.github/workflows/iw3-renderer-init-arm64.yml` automatically runs this host regression and separately builds/links the real Android EGL provider against NDK `libEGL` and `libandroid` as an ELF64 AArch64 shared object. The CI triggered at commit `8a600160c0e573443e0423792f12085e58365199`: [Actions run 41271045805](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41271045805). **Check its final job conclusions; queued/running is not a pass.**

## Unmet completion gates

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` at baseline.
`IW3_RENDERER_BACKEND_LINKED=false`.
`IW3_RENDERER_FRAME_PROVEN=false`.
`IW3_REAL_MAP_LOADED=false`.
`IW3_GAMEPLAY_PROVEN=false`.
`IW3_PLAYABLE_APK=false`.

Next engineering priority: replace/port the Direct3D9-dependent original renderer initialization, material, geometry and draw submission onto a native Android GLES3 backend, then connect it to original IW3 `Com_Init`, real FastFile/map loading and real touch-driven `CL_CreateCmd`/gameplay. No fake renderer, Godot, or diagnostic JNI APK is a completion criterion. Keep PR #4 open and unmerged.
