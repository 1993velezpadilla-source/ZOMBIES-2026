# IW3 Android phase GX — GLES3 GPU synchronization provider (not gameplay)

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Initial evidence and block

The preceding phase GW established an ARM64 relocatable link of four original
KisakCOD renderer translation units and 29/29 host tests. The combined object
still had **273 unresolved external symbols**. `rb_backend.cpp` and
`r_setstate_d3d.cpp` still explicitly fail when their original D3D9 GPU-query
paths are reached on Android; the EGL3 platform context provider exists but is
not connected to IW3 rendering. The prior green CI was not an Android frame.

## Concrete implementation

- Added `third_party/KisakCOD/src/gfx_d3d/r_android_gpu_fence.h/.cpp`
  using **actual GLES3** `glFenceSync`, `glFlush`, `glClientWaitSync`
  and `glDeleteSync`. No D3D9 query is faked and no completion is inferred
  from elapsed CPU time.
- Binding requires the original, current EGL display/context and the owning
  render thread. Inserting a second fence without retiring the first fails.
  Polling distinguishes invalid, idle, pending and actually completed work.
  Waiting is bounded to 50 ms per call; `GL_WAIT_FAILED` preserves the
  fence for explicit cleanup. Abandon/release refuse unsafe deletion from
  the wrong thread or a non-current context.
- Added `tests/test_iw3_android_renderer_gpu_fence_gles3.py`, which builds
  and executes the genuine provider under host ASan/UBSan against mock
  GL/EGL entry points, including context/thread rejection, timeout,
  signaled fence, failed insertion/wait and resource release. The mock
  harness **does not prove device rendering**.
- Expanded `.github/workflows/iw3-renderer-init-arm64.yml` to build and
  link the real provider as an ELF64/AArch64 shared object with Android
  `-lEGL -lGLESv3`, check exported fence symbols and retain the object
  as a diagnostic artifact. No substitute engine is used.

## Explicit integration boundary

This is a **real GLES3 synchronization component**, not a working IW3
rendering backend. It is intentionally not wired into the original
`R_InsertGpuFence`, `RB_IsGpuFenceFinished`, `RB_AdaptiveGpuSyncFinal`,
or `RB_BackendTimeout` call paths until the EGL context is owned by the
actual original render thread and the frame lifecycle is integrated.
`R_AndroidEglCreate/Destroy/DetachWindow` do not yet manage the new
fence state. The original Android guards remain fail-closed.

Next: integrate the fence state into the real IW3 render-thread/EGL lifecycle,
handle context destruction/recreation and presentation fences, then connect
real materials, geometry, shaders, map loading and touch/gameplay. A successful
NDK compile, mock host test or JNI diagnostic APK is **not** gameplay evidence.

## Acceptance status

`IW3_GLES3_GPU_FENCE_PROVIDER_IMPLEMENTED=true` (source code only until CI)  
`IW3_GLES3_GPU_SYNC_WIRED_TO_ORIGINAL_RENDERER=false`  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_TOUCH_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

CI results and links will be recorded in PR #4 after verification. Do not
merge to `main` while the acceptance gates are unmet.
