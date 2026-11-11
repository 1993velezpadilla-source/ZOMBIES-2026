# Phase GY — original IW3 GPU fence call sites to real GLES3 GLsync (NOT GAME)

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

Starting point: phase GX had a GLES3 GLsync provider built for ARM64, but original `R_InsertGpuFence`, `RB_IsGpuFenceFinished`, `RB_IsGpuFinished`, `R_FinishGpuFence` and `RB_AbandonGpuFence` still aborted instead of using it. Four original renderer TUs linked relocatably with 273 unresolved externals; no renderer frame existed.

Changes: a render-thread-owned, explicitly bound bridge in `r_android_gpu_fence.cpp/.h` connects the five original KisakCOD call sites to `glFenceSync`, `glClientWaitSync`, `glDeleteSync` and bounded waits. Polling only reports completion when GLES actually signals. No implicit binding, no fabricated success; unbound/wrong-context calls remain fatal. Desktop D3D9 branches remain untouched. Original backend's other D3D9 paths remain guarded.

Regression: new host ASan/UBSan test extracts the five **original** function bodies, executes them with the real provider source and mock GL/EGL entry points, and checks unbound rejection, idle/pending/completed, duplicate insertion, 250ms bounded timeout, abandonment, wrong context, and release. Existing fail-closed regressions remain for unbound contexts. Android CI also links four original ARM64 objects with the GLES3 provider object and checks bridge symbols are resolved. This relocatable link is NOT a runnable renderer.

**Unfinished**: the EGL platform provider still does not bind/release the bridge as part of original render-thread startup/pause/destroy. GLES materials, geometry, shaders, map load and real device gameplay are absent. No JNI diagnostic is accepted as gameplay.

IW3_GLES3_ORIGINAL_CALLSITES_LINKED=true (relocatable ARM64 link only)  
IW3_GLES3_GPU_SYNC_EGL_LIFECYCLE_WIRED=false  
IW3_RENDERER_BACKEND_LINKED=false  
IW3_RENDERER_FRAME_PROVEN=false  
IW3_REAL_MAP_LOADED=false  
IW3_TOUCH_GAMEPLAY_PROVEN=false  
IW3_PLAYABLE_APK=false

Do not merge to main until all actual device gameplay gates pass.

## Verified CI — 2026-11-01

- [Renderer workflow 41353172143](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41353172143): both jobs passed, including the original source ARM64 compile and four-TU-plus-GLES-provider relocatable link.
- **31/31 host renderer tests passed**, including the new original-function-body GLsync integration regression under ASan/UBSan. Host EGL/GL entry points were mocks, not an Android GPU execution.
- The original four-TU object reports 277 undefined symbols before adding the GLES3 provider (273 in the previous pass, plus four new bridge references). The combined relocatable object resolves all `R_AndroidGpuFenceOriginal*` bridge symbols. Other engine and GL/EGL dependencies remain; no complete executable or rendering evidence exists.
- Other workflow jobs triggered by this commit were still running when the renderer jobs were inspected; their results must be checked separately. No playable APK is produced.
