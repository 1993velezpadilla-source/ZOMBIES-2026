# IW3 Android phase HK — authentic D3D9 blend state to GLES3 (NOT GAME)

Date: 2026-11-02. PR #4, branch `feature/iw3-native-android-arm64-20261025`. Never merge to main before real gameplay.

## Baseline / first blocker
Reviewed current PR head `aafee76076d3878efb233f7dc6e9f47c5aae4d5f`, last renderer CI [41409677431](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41409677431), and original `r_state.cpp`. The prior AArch64 full-translation-unit probe failed first at `R_HW_DisableBlend` on `device->SetRenderState(D3DRS_ALPHABLENDENABLE,0)`, followed by D3D9 RGB/alpha blend operations. A green partial provider build was not a full renderer.

## Source implementation
- In authentic `r_state.cpp`, `R_HW_DisableBlend` and `R_HW_SetBlend` use Android-only GLES3 provider calls; original Windows Direct3D9 bodies remain under `#else`.
- New `r_android_blend.cpp/.h` maps the original IW3 `GFXS0` source/destination RGB/alpha factors and separate equations to `glBlendFuncSeparate`, `glBlendEquationSeparate`, `glEnable/glDisable(GL_BLEND)`. Values correspond to original `s_blendTable_30` and `s_blendOpTable_30`. Unsupported/invalid state is rejected, never silently approximated.
- Validates current EGL display/context, checks GL errors, snapshots blend state and restores it on mutation error. Explicitly preserves the valid `GL_ZERO` factor (numerical zero) rather than mistaking it for an invalid enum.
- The existing original `R_ChangeState_0` normalizes omitted separate-alpha bits before calling the provider. The Android bridge does not fabricate shaders, geometry, materials or a rendered scene.

## Verification
- Locally compiled and ran the new standalone C++ mock harness with `g++ -std=c++17 -D__ANDROID__ -O1 -g -UNDEBUG -fsanitize=address,undefined -fno-omit-frame-pointer`; output: `IW3_ORIGINAL_BLEND_GLES3_ASAN_UBSAN_PASS_NOT_FRAME`. Checks missing context, invalid blend enums, RGB/alpha factors and equations, blend disable, query failure and state rollback. This uses mocked EGL/GLES.
- Added `tests/test_iw3_android_renderer_original_blend_gles3.py` to host regression discovery and an NDK `--no-undefined` ELF64/AArch64 provider-link step to renderer workflow. **CI outcome and the next full `r_state.cpp` compiler diagnostic must be recorded after Actions runs**; do not claim the full renderer compiles on the basis of a provider link.
- Windows D3D9 source retained. No Godot or substitute engine.

## Remaining hard gates
`IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**. Full `r_state.cpp` still needs depth/stencil, samplers, polygon offset and other D3D9 paths. Original buffers, vertex declarations, shader/material pipeline, map data and live touch/gameplay remain incomplete. JNI diagnostic APK is **not** a game.
