# IW3 Android phase GW — original D3D9 GPU-query boundary and four-TU ARM64 link

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Starting point and identified portability block

The prior phase GV proved that three genuine KisakCOD renderer translation units (`r_init.cpp`, `r_rendercmds.cpp`, `rb_backend.cpp`) compile for ELF64/AArch64 and can be linked relocatably, while leaving 273 external symbols unresolved. This is **not** a runnable GLES renderer.

The next original engine unit `gfx_d3d/r_setstate_d3d.cpp` still unconditionally dereferenced `dx.flushGpuQuery->GetData()` and maintained Direct3D9 query bookkeeping. That interface is opaque/unavailable on Android. Returning true as a placeholder would incorrectly tell the engine that GPU work completed.

## Code changes

- The **original** `RB_IsGpuFinished()` and `RB_IsGpuFenceFinished()` retain their complete desktop Direct3D9 implementations behind `#else`; Android explicitly reports `ERR_FATAL` and returns false until actual GLES3 `GLsync` lifecycle and ownership are connected. No fabricated GPU completion is introduced.
- New `tests/test_iw3_android_renderer_gpu_query_arm64.py` extracts the genuine original function bodies and executes their Android paths under host AddressSanitizer/UndefinedBehaviorSanitizer. It checks that the Windows D3D9 bodies are preserved.
- `.github/workflows/iw3-renderer-init-arm64.yml` now compiles the **fourth original** `r_setstate_d3d.cpp` with the pinned Android NDK and performs a strict `ld.lld -r` link of all four original renderer objects. The existing three-object probe remains for comparison. Undefined externals are inventoried, not hidden.
- No Godot, replacement engine, renderer mock, or `main` merge.

## Evidence gates

The workflow must prove `IW3_ORIGINAL_GPU_QUERY_AARCH64_COMPILED=true` and `IW3_ORIGINAL_RENDERER_FOUR_TU_RELOCATABLE_LINK=true` before those intermediate milestones may be reported as verified. A successful relocatable link still permits unresolved engine dependencies. The Android GPU completion code intentionally **cannot execute as a working GLES fence yet**.

`IW3_GLES3_GPU_SYNC_WIRED=false`  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

## Next engineering work

Implement an EGL-context-owned GLES3 `GLsync` implementation (insertion, poll, wait, abandonment, and cleanup across pause/context loss), connect it to the original `rb_backend.cpp` and `r_setstate_d3d.cpp` call sites, and validate it on an actual Android GLES3 context. Then resolve the remaining original renderer dependencies and translate authentic IW3 materials, geometry and shaders; load a real map and prove gameplay, weapons, actors and touch on device. The JNI diagnostic APK is not acceptance evidence.
