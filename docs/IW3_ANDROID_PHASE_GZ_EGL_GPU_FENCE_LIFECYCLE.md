# Phase GZ — bind authentic IW3 GLES3 GPU fences to EGL render-thread lifecycle (NOT GAME)

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`. No Godot, substitute engine, merge, or playable-APK claim.

## Audited starting point

Phase GY [CI 41353172143](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41353172143) compiled four genuine KisakCOD renderer translation units plus the GLES3 GLsync provider, and passed 31 host renderer tests. The original call sites had a bridge but the Android EGL provider did not bind or release it; consequently they could not execute safely after Android Surface creation, pause, or resume. The renderer still lacks real GLES material/geometry/shader translation and full engine startup.

## Implementation on the original KisakCOD renderer branch

- `r_android_egl.h`: explicitly tracks whether the original IW3 GLsync bridge is bound to this provider's current EGL context.
- `r_android_egl.cpp`: binds the original bridge only after successful EGL ES3 context creation, current-context validation and surface-size query; releases any live GLsync **before** unbinding, destroying the Surface, or destroying the context. Wrong-thread/wrong-context release failures refuse teardown instead of silently leaking or deleting GLsync from a foreign context.
- On Surface detach, releases the bridge before EGL unbind and restores it after a recoverable unbind/destroy failure. Detached state keeps the EGL context but does not falsely advertise a bound fence. On successful Surface resume, binds the bridge after `eglMakeCurrent` and before publishing the replacement. An attached Surface replacement retains its original context/bridge.
- `R_AndroidEglPresent` rejects an unbound bridge, but EGL swapping alone is **not** evidence of an IW3 frame.
- Host `tests/test_iw3_android_renderer_egl_lifecycle.py` now compiles the **real** `r_android_gpu_fence.cpp` with the **real** `r_android_egl.cpp` under ASan/UBSan. EGL/GLES/ANativeWindow functions are mocks, with pending GLsync inserted across create, destroy, failed detach, successful detach and resume; checks actual provider's GLsync deletion and rebind bookkeeping.
- Android NDK CI now links the EGL lifecycle provider and original GLsync provider together with `-Wl,--no-undefined -lEGL -lGLESv3 -landroid`, checking both bridge symbols. This verifies the provider's ARM64 link only, not full IW3 engine linking.

## Evidence and honest gates

Code commits: `14dc7a70` (header), `cf32611f` (original EGL lifecycle), `8ee10e05` (host regression), `c7acd99d` (NDK CI).

New renderer CI: [Actions 41362180287](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41362180287). **Queued when this document was written; do not claim test success until the actual run completes.** Check host sanitizer and NDK link jobs and retain failure logs if red.

`IW3_GLES3_GPU_SYNC_EGL_LIFECYCLE_WIRED=implemented_in_provider_pending_CI`  
`IW3_ORIGINAL_RENDERER_STARTUP_WIRED=false`  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_TOUCH_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

## Next blocker

The EGL+GLsync provider still is not invoked by a **complete original IW3 Android renderer startup**; `R_InitGraphicsApi` deliberately fails closed. The authentic `rb_backend.cpp` still rejects missing GLES render-target, texture, scene, shader, geometry, and presentation translations. Four original renderer units remain only relocatably linked with unresolved external engine symbols. Next passes must build a real GLES command path and original engine startup and then demonstrate a genuine map with touch-driven gameplay, weapons and actors on ARM64 hardware/emulator. JNI diagnostics do not satisfy this gate.
