# IW3 Android Phase HN — original sampler-state GLES3 bridge (NOT GAME)

Date: 2026-11-02. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4 remains unmerged.

## Baseline and actual blocker
Before this pass, renderer CI run [41423332251](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41423332251) passed its two **audit** jobs, but the genuine `r_state.cpp` ARM64 compilation probe returned exit code 1. Its first error was the D3D9 `SetSamplerState(D3DSAMP_MINFILTER)` path at lines 1990–1992. Further errors involved MAGFILTER, MAXANISOTROPY, MIPFILTER, ADDRESSU/V/W, and original texture binding at line 2432. A green audit workflow is not a complete renderer.

## Implementation on authentic KisakCOD
- `r_state.cpp::R_HW_SetSamplerState` now routes only Android to `R_AndroidGlesSetSamplerState`; Windows D3D9 logic is unchanged.
- `r_android_sampler_state.cpp/.h` translate original decoded min/mag/mipmap filter values and D3D9 WRAP/MIRROR/CLAMP address modes into real GLES3 **sampler objects**, bound per texture unit. This avoids accidentally changing a texture shared by multiple IW3 stages.
- The provider validates EGL context, unit count, decoded state, GLES errors and anisotropic extension capability. Unsupported D3D9 BORDER/MIRRORONCE and anisotropy without a suitable extension are rejected rather than misrendered. The original D3D9 low-byte anisotropy retention rule is preserved.
- On failure, the previous sampler binding is restored and the candidate object is deleted. On success, the previous bridge-owned sampler is deleted. `R_AndroidGlesReleaseSamplerStates` is provided for future EGL teardown integration.
- `tests/test_iw3_android_renderer_original_sampler_gles3.py` compiles and runs the real provider with mocked GLES/EGL and ASan/UBSan. It checks filter translation, binding, invalid values, missing extension, failure rollback and cleanup.
- Renderer CI adds a real Android NDK AArch64 provider compile/link check against `libEGL` and `libGLESv3`, plus an artifact.

## Hard limits
This bridge does **not** bind authentic IW3 texture allocations, integrate the original `R_HW_SetSamplerTexture`, hook sampler teardown into EGL shutdown, configure original shader/material declarations, or render a frame. GLES calls in host regression are mocked; NDK shared-library linking does not demonstrate Android execution. The JNI diagnostic APK is **not** a game.

Pending: verify the new CI on its final commit, inspect the next genuine `r_state.cpp` compiler failure (expected texture binding at line ~2432), and then connect original texture allocation/binding and full renderer dependencies. Do not merge.

`IW3_ORIGINAL_TEXTURE_RESOURCE_BINDING_WIRED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`
