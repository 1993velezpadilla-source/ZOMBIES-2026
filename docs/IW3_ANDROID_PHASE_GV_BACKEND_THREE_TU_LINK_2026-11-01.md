# IW3 Android ARM64 — phase GV: authentic backend object and three-unit relocatable link

Date: 2026-11-01. Branch: `feature/iw3-native-android-arm64-20261025`. PR: #4. **No Godot, no replacement engine, no main merge.**

## Starting evidence and first CI regression

At head `ff7250af`, the original `gfx_d3d/r_init.cpp` and `r_rendercmds.cpp` compiled as ELF64/AArch64 objects, but the original `rb_backend.cpp` failed with incomplete Direct3D9 interfaces, Windows-only surfaces/gamma, `__rdtsc`, D3D9 Present/EndScene and GPU-query operations. The general Android source audit run 41333587384 also failed one Python test because it expected the obsolete `#if !defined(__ANDROID__)` guard in `rb_backend.h`, while the header had correctly switched to Android-first opaque declarations.

Commit `cad6434b` corrected that test to assert the actual Android-first `r_d3d9_opaque.h` branch and separate desktop `d3d9.h` include. No production header was reverted.

## Original-engine changes (not a GLES implementation)

- `2e731f55`: isolated seven Windows Direct3D9-only backend operations from Android compilation in the **original** `gfx_d3d/rb_backend.cpp`: `R_Resolve`, `RB_StretchRaw`, `RB_SetGammaRamp`, `RB_BeginFrame`, `RB_SwapBuffers`, `RB_AdaptiveGpuSyncFinal` and `RB_BackendTimeout`. On Android these explicitly call `Com_Error(ERR_FATAL, ...)` rather than dereference nonexistent D3D9 interfaces or silently claim success. The full original Windows implementations are retained under `#else`.
- `988a618a`: added an executable host ASan/UBSan regression that extracts and executes those seven **actual original function bodies** under `__ANDROID__`, verifies fatal rejection, and checks desktop D3D9 bodies are preserved.
- `dd8ae1cc`: separated the final D3D9 `EndScene` call inside original `RB_CallExecuteRenderCommands` from Android. Importantly, the original `RB_ExecuteRenderCommandsLoop(backEndData->cmds)` source path is still present; this is **not** evidence it runs on Android.
- `7b9c6d51`: regression checking the original command dispatcher remains before the guarded D3D9 EndScene.
- `9ceb9df4` and `9d1e6583`: added a strict `ld.lld -r` AArch64 relocatable-link probe for the three original translation units, with symbol inventory and explicit non-game markers. This detects duplicate definitions and resolves references among the three objects, but permits unresolved engine services by design.

## Verified CI and remaining dependency inventory

- [Renderer Actions 41338418468](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41338418468): **success**, 28 host renderer tests; the complete original `rb_backend.cpp` now compiles for AArch64 (139 undefined externals at individual-object stage), along with original `r_init.cpp` and `r_rendercmds.cpp`.
- [Renderer Actions 41338587615](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41338587615): **success**, 28/28 host tests, all three original ELF64/AArch64 objects compile, and **`IW3_ORIGINAL_RENDERER_THREE_TU_RELOCATABLE_LINK=true`**. The combined relocatable object still has **273 undefined external symbols**. The separate Android EGL platform provider links, but the full IW3 renderer does not.

The combined object is **not** a linked shared renderer, a GLES3 implementation, or an APK. The `Com_Error` guards are intentionally fatal until real GLES render-target resolves, texture uploads, frame lifecycle, presentation and GPU synchronization are implemented. The next work must resolve original engine service dependencies, implement actual GLES command execution/material/geometry/shader mapping, and run map and gameplay on an Android ARM64 device.

## Honest gates

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=true`  
`IW3_ORIGINAL_RENDERCMDS_AARCH64_COMPILED=true`  
`IW3_ORIGINAL_BACKEND_RB_BACKEND_AARCH64_COMPILED=true`  
`IW3_ORIGINAL_RENDERER_THREE_TU_RELOCATABLE_LINK=true`  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

Do not merge PR #4 into main or report a playable APK until a real ARM64 Android build renders a map, consumes touch input and executes original IW3 gameplay/actors/weapons with device runtime evidence.
