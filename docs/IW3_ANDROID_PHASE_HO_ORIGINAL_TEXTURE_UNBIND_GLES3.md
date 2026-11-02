# IW3 Android phase HO — original R_HW_DisableSampler texture unbind via GLES3

Date: 2026-11-02. **Port incomplete — NOT A GAME.**

## Baseline verified before changes
- PR #4 was open and unmerged at `cf2095cf`.
- Original renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41431735414
  - Both jobs passed; 44/44 host tests.
  - The **full original** `gfx_d3d/r_state.cpp` AArch64 compile probe failed (`compiler_exit=1`) at line 2446, `R_HW_DisableSampler -> device->SetTexture(samplerIndex, 0)`, because `IDirect3DDevice9` is incomplete on Android. A green workflow here is NOT a compiled renderer.
- Genuine sampler state provider existed, but `IW3_ORIGINAL_TEXTURE_RESOURCE_BINDING_WIRED=false`.

## Implementation
- Original KisakCOD `third_party/KisakCOD/src/gfx_d3d/r_state.cpp` now routes the **actual** `R_HW_DisableSampler` Android path through `R_AndroidGlesDisableSamplerTexture(samplerIndex)`, preserving the Windows Direct3D9 call and existing `R_DisableSampler` / `R_UnbindImage` control flow.
- New `r_android_texture_unbind.cpp/.h` validates a current EGL display/context, GL error state, original sampler index bounds and GLES3 combined texture unit count.
- D3D9 `SetTexture(unit, nullptr)` can detach 2D, cube and volume textures. GLES3 has separate per-target bindings; the provider snapshots and unbinds all three targets for the selected texture unit, preserving the previously active texture unit and existing GLES3 sampler object state.
- It fails closed on invalid context, invalid units and GL errors. On a partial binding mutation error, it attempts to restore the original texture bindings; it never manufactures a texture, image, shader, mesh or frame.
- New `tests/test_iw3_android_renderer_original_texture_unbind_gles3.py` checks the original source callsite and runs a mocked GLES3/EGL C++ harness with ASan/UBSan. Adversarial cases: missing context, out-of-range unit, pre-existing GL error, failed state query, mid-unbind error with rollback, all three target unbinds, other-unit isolation, active-unit restoration and no sampler-object mutation.
- `.github/workflows/iw3-renderer-init-arm64.yml` now compiles/links the provider against **real** Android NDK EGL/GLESv3 with `-Wl,--no-undefined`, verifies ELF64/AArch64 and the exported symbol, and uploads the provider artifact. The host regression is included in the renderer test discovery.

## Evidence and limitations
- Local host mock ASan/UBSan regression executed **3 times successfully** before pushing.
- **Verified GitHub Actions:** https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41438686579 — both jobs **success**, 45/45 renderer host tests (including the new ASan/UBSan unbind regression), and NDK ELF64/AArch64 provider linked against real EGL/GLESv3 with `-Wl,--no-undefined` and exported `R_AndroidGlesDisableSamplerTexture` (`IW3_ORIGINAL_TEXTURE_UNBIND_GLES3_AARCH64_LINKED=true`).
- **Negative authentic engine probe preserved:** full original `r_state.cpp` ARM64 compile still **fails** (`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false`, compiler exit 1), but its first error moved from line 2446 `SetTexture` to **line 2725 `device->Clear`**. Subsequent errors remain at lines 2800/2825 (D3D9 depth-bias states) and 3000 (adaptive tessellation). The workflow's green status only certifies its partial tests and evidence collection, NOT a linked renderer.
- The provider is not a texture **upload/register/bind** path. Authentic `GfxImage` resource creation and shader/material binding remain unimplemented. Other original D3D9 calls remain, including `device->Clear`, depth bias and adaptive tessellation.
- Host EGL/GLES functions are mocked. An AArch64 provider link does not prove execution on an ARM64 phone.

## Hard gates
`IW3_ORIGINAL_TEXTURE_RESOURCE_BINDING_WIRED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

The JNI diagnostic APK is NOT the requested game. Do not merge PR #4 or announce completion until a real ARM64 IW3 engine APK loads a map, renders real geometry, handles touch, and runs actual weapon/actor gameplay with runtime evidence.
