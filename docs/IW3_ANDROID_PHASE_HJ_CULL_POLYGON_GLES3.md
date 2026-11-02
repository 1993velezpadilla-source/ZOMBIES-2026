# Phase HJ — original IW3 culling and polygon state on GLES3 (NOT GAME)

Date: 2026-11-02. PR #4, branch `feature/iw3-native-android-arm64-20261025`. Keep open and unmerged.

## Baseline
- Reviewed head `a34bed4b25e5d827a1f4692e7afa2c60a1869ac3`; all 19 workflow runs for this head completed successfully, including renderer audit 41402543616.
- Full original `r_state.cpp` AArch64 compile still failed at `R_HW_SetCullFace` (`D3DRS_CULLMODE`), then `D3DRS_FILLMODE`, blending and other D3D9 states. Prior renderer suite: 39/39 host tests with mocked graphics.

## Original engine changes
- The genuine `R_HW_SetCullFace` Android path calls `R_AndroidGlesSetCullFace`. Maps IW3 `GFXS0_CULL_NONE=0x4000`, `BACK=0x8000`, `FRONT=0xC000` to GLES3 `glDisable(GL_CULL_FACE)`, `glCullFace(GL_BACK)`, and `glCullFace(GL_FRONT)`. Explicit `glFrontFace(GL_CW)` preserves D3D9's clockwise front-face convention. Rejects invalid bits and missing EGL context. Saves and rolls back prior cull enable/mode/front winding on GL failure.
- The original `R_HW_SetPolygonMode` Android path accepts solid mode but **rejects** `GFXS0_POLYMODE_LINE=0x80000000`, because GLES3 has no fixed-function wireframe `glPolygonMode`. No fake wireframe or silent solid fallback.
- Windows D3D9 paths remain under `#else`. Existing alpha-test-enabled materials still fail closed until original shader discard is implemented.

## Validation
- Added `tests/test_iw3_android_renderer_original_cull_polygon_gles3.py`: host LP64 ASan/UBSan with mocked EGL/GLES, invalid bits/context/error/query, all three original cull modes, rollback on mutation failure, solid and wireframe behavior.
- Renderer CI includes this test in discovery and asserts exported AArch64 GLES3 cull/polygon symbols in the provider link. Green workflow alone does not prove the full original renderer.
- CI results to be recorded in PR #4 after workflow completes. No ARM64 phone runtime, map, frame, or gameplay evidence is claimed.

## Remaining gates
- Full original `r_state.cpp` still requires D3D9 blending, depth/stencil and sampler translations; geometry buffers, materials, shaders, render targets and game-data loading remain incomplete.
- `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`.
- JNI diagnostic APK is NOT a playable game. Do not merge.
