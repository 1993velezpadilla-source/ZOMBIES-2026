# IW3 Android phase HM — original front/back stencil GLES3 (NOT GAME)

Date: 2026-11-02. PR #4; branch `feature/iw3-native-android-arm64-20261025`. Do not merge to main.

## Baseline / observed next blocker
Previous HL run [41421138124](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41421138124) reported 42/42 host renderer tests and a standalone AArch64 depth-state provider. The **full authentic `r_state.cpp` still failed** first at `D3DRS_STENCILENABLE` (line 1638). Passing host/NDK provider tests are not a full renderer or game.

## Authentic source changes
- `third_party/KisakCOD/src/gfx_d3d/r_state.cpp`: six original `R_HW_*` stencil functions now call Android GLES3 only on Android, while preserving their original Direct3D9 branches for Windows: enable/disable, front/back operations, front/back comparison.
- `r_android_stencil_state.cpp/.h`: translates original D3D9 stencil enums (KEEP, ZERO, REPLACE, INCRSAT, DECRSAT, INVERT, INCR, DECR) to GLES3 and all eight original comparisons. `glStencilOpSeparate` uses D3D pass/fail/zfail in the correct GLES fail/zfail/pass order. Front/back orientation matches the earlier clockwise front-face GLES3 port.
- Validates EGL context, existing GL errors and operation indices; snapshots/restores previous GL state after mutation failure. Comparison updates preserve existing reference and read mask. No fabricated shader, map, actor or frame.
- `tests/test_iw3_android_renderer_original_stencil_gles3.py`: mocked EGL/GLES LP64 regression under ASan/UBSan; checks front/back separation, operation mapping, all comparisons, reference/mask retention, invalid indices, context/query failures and rollback.
- Renderer workflow includes new paths and an NDK `-Wl,--no-undefined` shared-library link of the real GLES3 provider, in addition to the existing negative full-`r_state.cpp` compile probe.

## Evidence and remaining gates
Implementation commits: `788192e2` (original functions), `65fcbec8` and `b5ebd3a4` (GLES3 provider), `a6d8a462` (sanitizer regression), `3a1b53ae` (CI wiring). The associated renderer workflow is [41422923776](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41422923776). **Its final outcome must be inspected before declaring any test passed.**

Still missing: complete original renderer compilation/link, original buffer allocator/VAO/shaders/materials and sampler paths, real map load, live touch consumption by the genuine IW3 client, and observed Android ARM64 gameplay. The JNI APK is diagnostic only. `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; `IW3_PLAYABLE_APK=false`.
