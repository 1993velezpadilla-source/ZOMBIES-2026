# IW3 Android phase HR — original D3D9 ATOC/SSAA state boundary (NOT GAME)

Date: 2026-11-02. PR #4 remains open and unmerged.

## Verified baseline
- HQ renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41461272240 — both jobs succeeded; **46/46 mocked host renderer regressions** passed with ASan/UBSan.
- The same CI's genuine full original `r_state.cpp` ARM64 compiler probe still returned **compiler_exit=1**. The first remaining D3D9 error was `D3DRS_ADAPTIVETESS_Y` in `R_SetAlphaAntiAliasingState` at line 3023, after polygon offset was bridged.
- This green CI does not mean the full original renderer is compiled, linked, rendering, or playable.

## Original engine modifications
- Original `R_SetAlphaAntiAliasingState` now calls `R_AndroidGlesSetAlphaCoverage(stateBits0, r_aaAlpha->current.integer)` on Android; retains Windows `D3DRS_ADAPTIVETESS_Y` under `#else`.
- Original D3D9 FOURCC `ATOC` (`0x434f5441`) can be represented by GLES3 `GL_SAMPLE_ALPHA_TO_COVERAGE` **only** when the current framebuffer reports an MSAA sample buffer with at least 2 samples. Context, query and mutation errors fail closed, with rollback.
- D3D9 `SSAA` (`0x41415353`, original `r_aaAlpha == 2`) is vendor-specific and is **explicitly rejected** when requested. Disabled alpha coverage disables the GLES3 state. This is not a shader/material implementation.
- New host ASan/UBSan regression `tests/test_iw3_android_renderer_original_alpha_coverage_gles3.py` covers missing EGL, pending GL errors, absent MSAA, SSAA rejection, success and failed mutation rollback. Legacy render-state host mocks were extended with required GLES constants.
- Renderer workflow triggers the new test and requires the GLES3 ARM64 provider to export `R_AndroidGlesSetAlphaCoverage`.

## Gates
- Verify the new renderer workflow **and its genuine full `r_state.cpp` compile probe** before claiming this translation unit compiled. Partial provider linkage is not a complete renderer.
- Still missing original GPU texture/buffer resource integration, material shaders, genuine map scene, Android touch input wired through the original client and gameplay, and real ARM64 device evidence.
- Keep PR #4 unmerged; the JNI APK is diagnostic only.

`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`
