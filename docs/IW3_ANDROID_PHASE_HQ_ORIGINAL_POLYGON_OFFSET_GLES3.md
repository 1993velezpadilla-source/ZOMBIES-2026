# IW3 Android phase HQ — original polygon offset to guarded GLES3 (NOT GAME)

Date: 2026-11-02. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4 remains open/unmerged.

## Baseline from actual GitHub CI logs

- Before edits: commit `52f232deb104d70c57c1e0bd85bea176de68c423`.
- Renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41446915422 — both jobs reported success, **but the original full `r_state.cpp` AArch64 compile probe returned compiler_exit=1**.
- Confirmed in job `125282216587` log: first error at `r_state.cpp:2813`, `device->SetRenderState(D3DRS_SLOPESCALEDEPTHBIAS, ...)`; additional errors at line 2838 (`D3DRS_DEPTHBIAS`) and line 3013 (`D3DRS_ADAPTIVETESS_Y`). Green CI is a diagnostic/partial-provider signal only.
- Previous 45/45 mocked renderer host regressions passed. **No Android scene/frame evidence**.

## Engine changes

- `R_HW_SetPolygonOffset` in the **original** `third_party/KisakCOD/src/gfx_d3d/r_state.cpp` now calls `R_AndroidGlesSetPolygonOffset(scale,bias)` on Android. It retains the original Windows D3D9 path under `#else` and fails via the engine's fatal render-error path on unsupported GLES conditions.
- `r_android_depth_state.cpp/.h`: adds `glPolygonOffset` and `GL_POLYGON_OFFSET_FILL` handling with EGL checks, finite input validation, depth attachment precision query, previous-state capture, GL-error checks and best-effort rollback.
- **Precision limitation:** D3D9 constant depth bias is normalized depth-space, while GLES3 `glPolygonOffset` takes an implementation-dependent minimum resolvable depth unit. For fixed-point depth attachments reporting 16 or 24 bits, we convert using nominal `bias * 2^depthBits`. This is a **portability approximation, not proven pixel-equivalent**. Other formats, missing depth attachment, and non-finite/out-of-range input fail closed. GPU screenshots/tests with real depth materials are required before claiming visual parity.
- New host regression `tests/test_iw3_android_renderer_original_polygon_offset_gles3.py` checks real original callsite, Windows branch preservation, context and query failures, 16/24-bit conversion, no-offset disable and mutation rollback under ASan/UBSan. Mock GLES is **not** Android rendering.
- Renderer workflow now triggers on this test and checks the ARM64 shared-library symbol `R_AndroidGlesSetPolygonOffset`.

## Evidence / remaining gates

- Commits: `5802c16f` original callsite, `ed679ed9` header, `204726e5` provider, `811cfdcd` regression, `3f6a2191` CI.
- Inspect the **new** renderer CI run and its genuine `r_state.cpp` compiler diagnostics. Next expected D3D9 blocker: `R_SetAlphaAntiAliasingState` / `D3DRS_ADAPTIVETESS_Y` (not yet proven advanced).
- Still missing: authentic texture/image upload, GPU buffers, shaders/materials, complete renderer linkage, map loading, Android touch-to-original-client commands, weapon/actor gameplay and real-device execution evidence.
- Do not merge PR #4 or treat the JNI diagnostic APK as playable.

`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=unverified_for_HQ`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`
