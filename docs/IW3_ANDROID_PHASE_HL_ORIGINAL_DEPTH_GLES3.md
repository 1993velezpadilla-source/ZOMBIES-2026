# IW3 Android phase HL — original depth write/test/compare GLES3 (NOT GAME)

Date: 2026-11-02. PR #4 on `feature/iw3-native-android-arm64-20261025`. Do not merge to main.

## Baseline / next observed blocker
After phase HK, [renderer CI 41420787487](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41420787487) had **41/41 host tests passed**, an AArch64 EGL/GLESv3 blend provider linked, and the original full `r_state.cpp` still failed compilation first at line 1521 on `D3DRS_ZWRITEENABLE`. Subsequent errors were `D3DRS_ZENABLE`, `D3DRS_ZFUNC`, then stencil. Green CI is intentionally a partial provider audit.

## Source work
- The authentic `R_HW_SetDepthWriteEnable`, `R_HW_SetDepthTestEnable`, `R_HW_SetDepthTestFunction` in `r_state.cpp` now route Android to a GLES3 provider, preserving the original Windows Direct3D9 branches.
- New `r_android_depth_state.cpp/.h` translates original `GFXS1_DEPTHWRITE` to `glDepthMask`, `GFXS1_DEPTHTEST_DISABLE` to `glEnable/glDisable(GL_DEPTH_TEST)`, and original comparison bits `ALWAYS/LESS/EQUAL/LESSEQUAL` to `glDepthFunc`.
- Each operation validates the current EGL context and GL errors, snapshots the previous state and rolls back on a mutation error. Does not fabricate geometry, depth buffers, shader programs, a scene, or actors.
- New `tests/test_iw3_android_renderer_original_depth_gles3.py` runs an LP64 mocked EGL/GLES regression under AddressSanitizer and UndefinedBehaviorSanitizer; workflow compiles a genuine EGL/GLESv3 ELF64/AArch64 provider with `-Wl,--no-undefined`.

## Local verification
Standalone C++ harness compiled and executed locally with `g++ -std=c++17 -D__ANDROID__ -O1 -g -UNDEBUG -fsanitize=address,undefined -fno-omit-frame-pointer`, printing `IW3_ORIGINAL_DEPTH_GLES3_ASAN_UBSAN_PASS_NOT_FRAME`. Tests cover context/error/query failures, both depth-write and depth-test settings, all four original depth comparison modes, and rollback. EGL/GLES were mocked; this is **not device rendering**.

## CI and remaining work
The new workflow run must be checked for both host and NDK outcomes, and the first remaining original `r_state.cpp` compile diagnostic must be recorded in PR #4. Expected next area: stencil, polygon offset, sampler paths, authentic buffers and materials. `IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false` until explicitly proven otherwise. `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**. The JNI APK remains diagnostic only. No Godot or replacement engine.
