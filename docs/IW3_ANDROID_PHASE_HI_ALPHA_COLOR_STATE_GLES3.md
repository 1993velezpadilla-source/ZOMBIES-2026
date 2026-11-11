# Phase HI — original IW3 alpha-test safety and GLES3 color-write mask (NOT GAME)

Date: 2026-11-02. Branch: `feature/iw3-native-android-arm64-20261025`; PR #4 remains open and unmerged.

## Baseline
- Reviewed PR head `753bfcc6ebe0471c72a6fff92f1311f164feac92` and its 19 successful CI workflow runs, including the renderer run `41396195534`.
- The phase-HH renderer suite passed 38/38 host tests; those graphics tests mock EGL/GLES.
- Full original `r_state.cpp` AArch64 compiler probe remained **negative** at `R_HW_SetAlphaTestEnable`: D3D9-only `SetRenderState(D3DRS_ALPHATESTENABLE,...)`, followed by color mask, culling, blending, alpha compare and other D3D9 paths.

## Authentic engine changes
- In genuine KisakCOD `gfx_d3d/r_state.cpp`, the Android branch of `R_HW_SetAlphaTestEnable` now calls `R_AndroidGlesSetAlphaTestEnable`; the original Windows D3D9 code remains behind `#else`.
- GLES3 **has no fixed-function alpha test**. The provider validates a live EGL context and pre-existing GL errors, accepts only original `GFXS0_ATEST_DISABLE` (bit `0x800`) and **rejects enabled alpha test**. This prevents silently rendering alpha-tested IW3 materials incorrectly. `R_SetAlphaTestFunction` also rejects Android execution until the original shader path implements fragment discard for the genuine alpha comparisons; Windows D3D9 comparison/ref logic is retained.
- Original `R_HW_SetColorMask` now routes Android to `R_AndroidGlesSetColorMask`. It maps the authentic D3D9 color-write state bits `0x08000000` (RGB) and `0x10000000` (alpha) to `glColorMask`. It reads and preserves the previous GL color mask and attempts rollback on GL mutation failure.
- New provider: `r_android_render_state.cpp/.h`. No fabricated textures, actors, maps, shaders, or frames. No Godot or substitute engine.

## Regression and ARM64 compilation
- New `tests/test_iw3_android_renderer_original_alpha_color_gles3.py` compiles the provider under host ASan/UBSan (LP64), with mocked EGL/GLES. Covers missing context, pre-existing GL error, alpha-enabled rejection, all four RGB/alpha combinations, GL query error, GL color-mask mutation error and rollback.
- The renderer workflow now includes this test in discovery and requires a real NDK AArch64 ELF provider link against EGL and GLESv3 using `-Wl,--no-undefined`, with exported-symbol checks. It still separately records the **full original `r_state.cpp` compile outcome**; provider-only linking does not prove a full engine.
- **Verified:** [renderer GitHub Actions run 41402336863](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41402336863), implementation head `b227ef6cdbbe4a61f08ea93b65ddcc187def7776`, **both jobs success** (2026-11-02 06:50 UTC). Inspected host job logs: **39/39 tests passed**, including the new mocked EGL/GLES ASan/UBSan regression. Inspected NDK job logs: ELF64/AArch64 provider linked against real EGL/GLESv3 and exported both functions; `IW3_ORIGINAL_ALPHA_COLOR_GLES3_AARCH64_LINKED=true`.
- The same CI's **complete original `r_state.cpp` ARM64 compile still fails** (`compiler_exit=1`), now first at `r_state.cpp:1045` for `device->SetRenderState(D3DRS_CULLMODE,...)`, followed by `D3DRS_FILLMODE`, `D3DRS_ALPHABLENDENABLE`, blend operations, etc. The successful workflow is a **provider/test audit**, not a complete renderer or device test.

## Remaining hard gates
- **Shader alpha-test discard not implemented**. The alpha-enabled path deliberately fails rather than silently drawing incorrect material pixels.
- Original `r_state.cpp` still has additional Direct3D9-only render state operations (cull, polygon, blending, depth, stencil, sampler), and the full renderer remains unlinked.
- Original `r_buffers.cpp` GPU allocation and upload, vertex declarations/VAO, shader/material translation, image-backed FBOs, map loading, Android bootstrap, original touch-to-client loop, weapons and actors all remain unproven.
- `IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false` until the compiler probe proves otherwise.
- `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**.
- The JNI APK remains a diagnostic, not a game. Do not merge PR #4 to main.
