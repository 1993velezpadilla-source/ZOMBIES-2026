# Phase HH — authentic IW3 initial render-state GLES3 boundary (2026-11-02)

## Baseline verified before edits
- PR #4 open/unmerged, branch `feature/iw3-native-android-arm64-20261025`, baseline head `770b648a982b8b8989dd499b7b7d13313eea76bd`.
- Baseline renderer workflow `41394220171`: both host and AArch64 jobs completed successfully, but the full original `r_state.cpp` compile still failed at `R_SetInitialContextState` due to D3D9-only `SetRenderState` / `D3DRS_SEPARATEALPHABLENDENABLE`.
- Baseline 37/37 host renderer tests from phase HG; those use mocked EGL/GLES for the graphics paths, not a real phone.
- Original vertex/index resource allocation, vertex declarations, shader/material translation, complete engine link, map loading and gameplay remain unfinished.

## Actual source changes
- Preserve the original Windows Direct3D9 `R_SetInitialContextState` implementation behind the non-Android preprocessor branch.
- Route the **original** KisakCOD IW3 `R_SetInitialContextState` on Android to `R_AndroidGlesSetInitialContextState`.
- New provider `r_android_initial_state.cpp/.h`: reject absent EGL display/context and pre-existing GL errors; use real `glDisable(GL_DEPTH_TEST)` for the original `D3DRS_ZENABLE=FALSE`. GLES3 inherently supports independent alpha blending and separate front/back stencil operations; unlike D3D9, these are not individually enabled by render-state switches. Do not fabricate a frame or silently claim unsupported render-state translation.
- Fail the original call path through `Com_Error(ERR_FATAL)` on provider failure.
- Add `tests/test_iw3_android_renderer_original_initial_state_gles3.py`: host ASan/UBSan mock-EGL/GLES regression for missing context, pre-existing GL error, injected `glDisable` error, and successful initialization; static checks preserve Windows D3D9 path.
- Extend the existing renderer workflow to compile/link the GLES3 provider for AArch64 against actual Android EGL and GLESv3 with `--no-undefined`, and upload the provider ELF as an artifact. The original `r_state.cpp` full compile remains a separate diagnostic gate.

## Validation status
- Independent local host mock compiled with `g++ -std=c++17 -D__ANDROID__ -fsanitize=address,undefined` and printed `IW3_ORIGINAL_INITIAL_RENDER_STATE_GLES3_HOST_SANITIZER_PASS_NOT_FRAME`.
- **Verified GitHub Actions [41396087438](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41396087438)** (head `343f8d55468efa75ae4df0ed93b35b7d3501e2e1`): both `renderer-tracking-host` and `original-renderer-compile-probe` jobs completed successfully on 2026-11-02.
- Host renderer suite: **38/38 tests passed**; new test exercised mocked EGL/GLES under ASan/UBSan. Independent local mock also passed.
- Android NDK: real EGL/GLESv3 provider linked as **ELF64/AArch64**, with `IW3_ORIGINAL_INITIAL_STATE_GLES3_AARCH64_LINKED=true` and `--no-undefined`. This is a provider shared object, not the full original engine.
- Full original `r_state.cpp` still **does not compile**: `IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false (compiler_exit=1)`. The first observed new error is `r_state.cpp:957` D3D9 `SetRenderState` member access, then `D3DRS_ALPHATESTENABLE` at line 958. Subsequent D3D9 blockers include `D3DRS_COLORWRITEENABLE`, `D3DRS_CULLMODE`, `D3DRS_FILLMODE`, `D3DRS_ALPHABLENDENABLE`, `D3DRS_BLENDOP`, and `D3DRS_SRCBLEND`. No claim that the full translation unit is portable.

## Explicit gates
- `IW3_ORIGINAL_INITIAL_STATE_GLES3_AARCH64_LINKED=true` (provider-only, verified).
- `IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false` until proven otherwise.
- `IW3_ORIGINAL_VERTEX_BUFFER_ALLOCATOR_WIRED=false`
- `IW3_ORIGINAL_VERTEX_DECLARATION_VAO_WIRED=false`
- `IW3_RENDERER_FRAME_PROVEN=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

**This is a narrow portability correction on the original KisakCOD IW3 renderer, not a runnable game.** The diagnostic JNI APK remains non-playable. Do not merge to main until real Android ARM64 on-device rendering, map, touch and gameplay evidence exists.
