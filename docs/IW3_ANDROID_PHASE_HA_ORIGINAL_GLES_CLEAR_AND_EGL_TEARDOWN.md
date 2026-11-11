# Phase HA — original IW3 clear command on GLES3 and retryable EGL teardown (NOT GAME)

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`. No Godot, substitute engine, main merge, or playable-APK claim.

## Starting evidence / next portability blocker

At head `0c56103e` the original renderer's EGL/GLsync provider had passed the [GZ CI run](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41362320915), but the genuine IW3 `RB_ClearScreenCmd` still invoked the D3D9 `R_ClearScreen` implementation on Android. The original `R_InitGraphicsApi` still fails closed because geometry, materials, shaders, render targets and full renderer bootstrap are missing. The JNI diagnostic APK is **not** a game.

Also discovered a concrete EGL driver-failure issue: `R_AndroidEglDestroy` discarded its handles even if `eglMakeCurrent`, `eglDestroyContext`, `eglDestroySurface`, or `eglTerminate` failed. That prevented retrying render-thread cleanup after Surface loss, risking leaked native resources.

## Actual code changes

- `third_party/KisakCOD/src/gfx_d3d/r_android_egl.cpp`: EGL teardown now stops at a failed step, retains live handles and ANativeWindow ownership, and clears individual handles only after successful destruction. It still releases the original IW3 GLsync before unbinding the context. Windows behavior is untouched.
- `tests/test_iw3_android_renderer_egl_lifecycle.py`: real EGL+GLsync provider host regression now injects four failure points (unbind, context destroy, Surface destroy, display termination), checks retained ownership, then retries teardown without leaks or double-destruction. EGL/GLES calls are mocked.
- `third_party/KisakCOD/src/gfx_d3d/r_android_clear.{h,cpp}`: a real GLES3 implementation for the original `RC_CLEAR_SCREEN` command: IW3 bitmask 1=color, 2=depth, 4=stencil; validates arguments and current EGL context, performs `glClear`, and restores scissor, write masks and clear values. It does **not** synthesize a scene.
- `third_party/KisakCOD/src/gfx_d3d/rb_backend.cpp`: the genuine `RB_ClearScreenCmd` consumes the original `GfxCmdClearScreen` payload through this GLES3 translation on Android; Windows continues calling `R_ClearScreen`.
- `tests/test_iw3_android_renderer_original_clear_gles3.py`: host ASan/UBSan harness for the real GLES3 clear implementation, with mocked GL/EGL calls, validating all seven valid attachment masks, invalid inputs, context absence, state restoration and GL error handling; also asserts the authentic backend call site.
- `.github/workflows/iw3-renderer-init-arm64.yml`: adds the new sources/tests to path triggers, host test discovery and an ARM64 shared-library link against actual EGL/GLESv3 with `--no-undefined`. CI success proves only an ARM64 command provider, **not** an engine frame.

## Verification gates (must be checked after CI completes)

The workflow's `renderer-tracking-host` job must pass the full renderer test suite including the new ASan/UBSan tests. The `original-renderer-compile-probe` job must compile `rb_backend.cpp` and link `libiw3-original-clear-gles3-arm64.so` against the NDK EGL/GLESv3 libraries. If either fails, preserve the error log and fix it; do not claim a green result based on this document.

`IW3_ORIGINAL_CLEAR_COMMAND_GLES3_SOURCE_WIRED=true` (not a frame)  
`IW3_ORIGINAL_CLEAR_COMMAND_GLES3_AARCH64_LINKED=pending_CI`  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_TOUCH_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

## Next required work

Implement genuine GLES3 render-target/FBO binding and viewport translation, followed by texture/material/shader/geometry command execution, then connect the complete original IW3 renderer startup and real map loading. Only an ARM64 runtime capture with map, touch input, original weapons and actors can satisfy the playable-APK gate. Keep PR #4 open and unmerged.
