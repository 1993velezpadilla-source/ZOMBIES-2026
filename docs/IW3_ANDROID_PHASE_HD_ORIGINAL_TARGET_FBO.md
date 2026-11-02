# IW3 Android phase HD — authentic render-target selection / GLES3 FBO boundary (NOT GAME)

Date: 2026-11-02 UTC. Branch: `feature/iw3-native-android-arm64-20261025`; PR #4. **No merge to main.**

## Audited first

Phase HC renderer Actions [41377076118](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41377076118) was green with 33 host renderer tests and an ARM64 viewport provider. The genuine `RB_ExecuteBackEndCommands` calls `R_SetRenderTarget(..., R_RENDERTARGET_FRAME_BUFFER)`; the genuine `R_SetRenderTarget` then invokes `R_HW_SetRenderTarget`, which previously unconditionally dereferenced D3D9 `IDirect3DDevice9` and called `SetRenderTarget`/`SetDepthStencilSurface`. This prevents native Android rendering even after viewport/clear commands were ported.

## Code implemented

- `third_party/KisakCOD/src/gfx_d3d/r_state.cpp`: original `R_HW_SetRenderTarget` now routes Android target IDs and **original** `gfxRenderTargets[id]` dimensions through `R_AndroidGlesBindTarget`. It resets the original state viewport and depth-range fields on a successful bind. A failed bind invokes `Com_Error(ERR_FATAL)` and returns; the Windows D3D9 implementation is retained under the other platform branch.
- `r_android_target.cpp/.h`: new GLES3 FBO boundary. Target ID 1 (`R_RENDERTARGET_FRAME_BUFFER`) binds EGL's **real default framebuffer 0**, only when current EGL surface dimensions match the original render target. Offscreen targets require explicitly registered GL texture/renderbuffer attachments and a complete FBO; missing or invalid attachments are rejected, not fabricated. FBO creation preserves the previous binding; failed creation deletes its FBO. Binding restores previous framebuffer/viewport on GL failure. Owned FBOs can be released on the owning EGL context.
- No synthetic frame, fake map, fake material, or substitute game engine was introduced. The registration API is deliberately **not called** until original IW3 image/texture allocation can supply genuine GL attachment IDs.

## Verification

- [GitHub Actions renderer run 41379193140](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41379193140): **success** (both jobs), **34/34 host renderer tests passed**. New `test_iw3_android_renderer_original_target_gles3.py` compiles the actual GLES3 provider under ASan/UBSan with mocked EGL/GLES and checks default-FBO sizing, rejection of unregistered offscreen targets, incomplete FBO cleanup, registration/binding, wrong-context rejection, and cleanup. This is **host mock testing**, not a GPU device run.
- Pinned Android NDK built the new provider as a linked **ELF64/AArch64** shared library against real `-lEGL -lGLESv3` with `-Wl,--no-undefined`: `IW3_ORIGINAL_TARGET_FBO_GLES3_AARCH64_LINKED=true`. This proves the provider's ABI/library link, **not** a complete IW3 renderer link.
- New full authentic `r_state.cpp` ARM64 compilation probe: **failed**, as documented by the CI artifact `iw3-original-r-state-arm64-report.txt`. First blockers include D3D9-only `device->SetIndices` (line ~56), `SetStreamSource` (~95), `SetRenderState` and missing `D3DRS_*` constants, `_D3DVIEWPORT9`, and `DrawIndexedPrimitive`. The probe is intentionally non-gating to preserve this dependency inventory; do not mistake the green workflow for a compiled `r_state.cpp`.

## Remaining hard gates

1. Port/partition the **rest of the original** `r_state.cpp` D3D9 state, geometry, draw and texture paths to GLES3, compile its complete translation unit, and link it with the original backend and provider.
2. Connect genuine IW3 image allocation/upload to `R_AndroidGlesRegisterTarget`, including depth-only formats, texture lifetimes and FBO teardown before EGL context destruction. Offscreen targets are currently **not registered** and correctly fail.
3. Complete shaders/materials, render-target initialization, `R_InitGraphicsApi`, scene/frame presentation, real map assets, touch input and original weapons/actors on ARM64. Test on a real ARM64 device with captured logs/frames.

`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false`; `IW3_ORIGINAL_OFFSCREEN_TEXTURES_REGISTERED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**. Existing JNI APK remains a diagnostic, not a game.
