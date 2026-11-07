# IW3 Android phase HP — genuine direct R_ClearScreenInternal GLES3 path

Date: 2026-11-02. **Port incomplete — NOT A GAME.**

## Baseline verified before edits
- PR #4 was open/unmerged at `98bed592bd16720247bc3ecc511bfc2b1712b53d`.
- Previous renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41438686579
  - Both jobs succeeded; 45/45 renderer host tests, including mocked GLES3/EGL ASan/UBSan coverage.
  - The **complete original** `gfx_d3d/r_state.cpp` AArch64 compiler probe **failed** with `compiler_exit=1`. Its first remaining diagnostic was `device->Clear` at line 2725 in `R_ClearScreenInternal`, followed by D3D9 slope/depth bias and adaptive tessellation.
  - The green workflow was a probe and partial provider link, **not** a complete renderer.
- Existing authentic IW3 `RC_CLEAR_SCREEN` backend already routed to `R_AndroidGlesClear`, but direct `R_ClearScreenInternal` still dereferenced the incomplete D3D9 device.

## Code changes
- `third_party/KisakCOD/src/gfx_d3d/r_state.cpp` now includes `r_android_clear.h` on Android.
- On Android, the **original** `R_ClearScreenInternal` delegates to the **existing** `R_AndroidGlesClear(whichToClear, color, depth, stencil)`, the same provider already used by `RC_CLEAR_SCREEN`.
- It rejects non-null explicit viewport (matching the existing original `iassert(!viewport)` contract) and reports failure through the original fatal render-error path. Android no longer asserts that a D3D9 device exists for this operation.
- The Windows `device->Clear` path and packed-color behavior remain unchanged under `#else`.
- `tests/test_iw3_android_renderer_original_clear_gles3.py` now asserts the direct authentic callsite, Android/Windows branch separation, error path and retained D3D9 call. The existing ASan/UBSan mock EGL/GLES3 regression still covers clear masks, viewport scissor behavior, state restoration, invalid input and missing context.
- No new renderer, shader, map, actor, or synthetic frame was introduced.

## Evidence
- Baseline log (actual original ARM64 compiler errors): https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41438686579
- Change commits: `d3cde66b75da21a72af40d3c032c786fe0c0bd5c` (engine callsite), `9b19f74961aa2018ead2137ba2cecf4da8e84644` (regression), `b1ce0313e4e70dad98b157b6d75d98a4bba6a8c4` (newline matching fix).
- New renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41446793102 — **queued when this document was first authored**. Inspect its final logs before claiming test success or that the compiler advanced.
- Even if the regression passes, mock EGL/GLES execution is not device rendering. The new callsite still requires a fully linked renderer and Android gameplay proof.

## Next gates
1. Confirm the complete original `r_state.cpp` compiler probe advances past `device->Clear`; address D3D9 depth bias and adaptive tessellation without inventing a replacement engine.
2. Connect genuine IW3 texture/image upload, VBO/IBO allocation, shader/material binding and complete renderer linkage.
3. Run a real ARM64 Android APK with genuine map assets, a rendered scene, touch-driven original client commands, and original weapon/actor gameplay; retain runtime logs/screenshots.

`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=unverified_for_HP`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

The JNI APK is diagnostic only. Do **not** merge PR #4 into main or announce completion.
