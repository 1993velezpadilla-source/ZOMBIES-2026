# IW3 Android phase HE — original hardware viewport / depth range and outdoor matrix LP64

Date: 2026-11-02 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`. **NOT GAME. Do not merge to main.**

## Audited before changes

The latest phase-HD renderer CI [41379193140](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41379193140) passed 34 host tests and linked the standalone GLES3 FBO provider. Its genuine `r_state.cpp` compile probe **failed**: direct D3D9 calls `SetIndices`, `SetStreamSource`, `SetRenderState`, `SetViewport`, `DrawIndexedPrimitive`, and related D3D types remain. In particular, original `R_HW_SetViewport` still dereferenced a D3D9 device even though `RB_SetViewportCmd` had a separate GLES3 implementation. The compiler also warned that the original outdoor matrix lookup indexed `(*outMatrix)[12]` beyond the first `float[4]` row.

## Implemented on original engine

- `r_state.cpp`: Android branch of **original `R_HW_SetViewport`** calls `R_AndroidGlesHardwareViewport`, with explicit `Com_Error(ERR_FATAL)` on failure; Windows D3D9 code remains intact. The original outdoor lookup `Vec4Add` now uses `outMatrix[3]`, the actual fourth matrix row, instead of an out-of-bounds index through the first row.
- `r_android_target.cpp/.h`: track dimensions only after a successful bind of a genuine IW3 target (default EGL framebuffer or registered offscreen FBO). The query rejects missing targets, null outputs, and foreign/lost EGL contexts. Successful release resets the dimensions; no guessed screen size.
- `r_android_hw_viewport.cpp/.h`: GLES3 bridge uses the existing validated top-left-to-bottom-left IW3 viewport conversion, sets `glDepthRangef` for the genuine hardware viewport path, rejects invalid/nonfinite depth ranges, and restores previous viewport and depth range when the depth operation fails.
- `tests/test_iw3_android_renderer_hw_viewport_depth_gles3.py`: LP64 host ASan/UBSan harness with mocked EGL/GLES covering unbound target, default/offscreen target dimensions, depth range, coordinate conversion, context loss, invalid inputs, and rollback. This is **not** a GPU device test.
- `.github/workflows/iw3-renderer-init-arm64.yml`: add the test to existing discovery, plus pinned-NDK `--no-undefined` AArch64 shared-library link for all three providers. The full original `r_state.cpp` compile probe remains non-gating and reports remaining errors honestly.

## Verification / hard gates

Phase-HE renderer CI [41380717675](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41380717675) **completed successfully in both jobs**. Inspected the host job log: **35/35 tests passed**, including `test_original_hardware_viewport_depth_and_context` with ASan/UBSan and mocked EGL/GLES. Inspected the NDK job log: `IW3_ORIGINAL_HW_VIEWPORT_DEPTH_GLES3_AARCH64_LINKED=true` with `-Wl,--no-undefined` against real Android EGL/GLESv3. The full authentic `r_state.cpp` ARM64 compile probe still reports **`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false (compiler_exit=1)`**. Its first blockers remain D3D9 `SetIndices`, `SetStreamSource`, `SetRenderState` and `DrawIndexedPrimitive`; the previous `_D3DVIEWPORT9`/`SetViewport` compiler errors no longer appear in the first diagnostic set. The original four-unit renderer relocatable link still has **278 unresolved external symbols**. This is partial provider/link evidence, not a full renderer or frame. The earlier phase-HE run [41380653257](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41380653257) was superseded by the documentation commit.

Next: finish genuine `r_state.cpp` D3D9-to-GLES3 state/index/stream/draw translation; connect original image/texture allocation and FBO lifetimes; link original renderer into an Android bootstrap; demonstrate real map data, touch input, weapons, actors and rendered frames on an ARM64 device.

`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false` (until proven otherwise);
`IW3_ORIGINAL_OFFSCREEN_TEXTURES_REGISTERED=false`;
`IW3_RENDERER_FRAME_PROVEN=false`;
`IW3_REAL_MAP_LOADED=false`;
`IW3_GAMEPLAY_PROVEN=false`;
**`IW3_PLAYABLE_APK=false`**. The existing JNI APK is diagnostic only.
