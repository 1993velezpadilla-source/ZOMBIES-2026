# IW3 Android phase IC — genuine D3D9 ps_3_0 COLOR0 → GLSL ES 3.0 subset (NOT GAME)

Date: 2026-11-02. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Baseline and actual blocker
The preceding phase IB commit `f9e2e8526ef352b0cb34b13c0c3f59f74864d3ad` passed the original renderer ARM64 compile/sanitizer workflow [41535314832](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41535314832). The unified visitor could validate and expose a narrow D3D9 instruction stream, but it generated no GLSL. The original Android shader creation/binding paths still fail closed; there is no GLES shader program.

## This pass: implementation in the authentic KisakCOD source tree
- Added `R_AndroidTranslateD3D9PixelColorSubsetToGLSL` to `third_party/KisakCOD/src/gfx_d3d/r_android_shader_bytecode.{h,cpp}`.
- This first intentionally narrow, **source-level** translator consumes the original D3D9 ps_3_0 token stream via the existing validated decoded visitor. It maps an explicit `dcl_color0 v0` declaration, unmodified full-vector MOV/ADD operations, temporary `r0`, and `oC0` into GLSL ES 300 text with explicit input/output variables.
- It rejects every unsupported opcode, declaration, register, swizzle, source/destination modifier, partial write, relative address, missing declaration, read-before-write, wrong shader stage/version, or missing color output. Failure clears the output string; no prefix is published. It never substitutes a fake shader.
- Kept Windows Direct3D9 untouched and did **not** wire this subset into the production shader creation path: the engine's real shader assets will require a much broader D3D9 instruction/constant/sampler/control-flow translator and vertex↔pixel varying linkage.

## Verification and evidence
Implementation commits: `34c2acae` (declaration), `24fa51f8` (source emitter), `305a52e9` (ASan/UBSan regression fixtures). The regression covers a valid D3D9 token fixture and exact generated source fragments; negative fixtures cover missing DCL, uninitialized temp, no color output, partial destination mask, swizzle, source modifier, unsupported late opcode, truncation, stage mismatch, and shader-model mismatch.

The final-head renderer workflow was queued at [41543246903](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41543246903) and [41543237018](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41543237018). **These runs were pending when this document was first written; do not treat them as passed without inspecting their final status and logs.** Host fixture tests and ARM64 compile checks do not constitute a GLES driver compile/link or visual proof.

## Hard remaining gates
This phase emits GLSL **text** for a tiny, authentic D3D9 subset only. It does not create a GPU shader, link a GLES program, connect vertex declarations/VAOs/varyings/uniforms/samplers, render a scene, load a map, consume live touch in gameplay, or execute the full original game on Android ARM64. No actual IW3 map shader has been demonstrated to fit this subset. The JNI diagnostic APK is not a playable game.

`IW3_SHADER_GLSL_SUBSET_SOURCE_EMITTER=true` (pending final CI); `IW3_REAL_ASSET_SHADER_TRANSLATION_PROVEN=false`; `IW3_GLES3_SHADER_PROGRAM_LINKED=false`; `IW3_FULL_RENDERER_LINKED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_TOUCH_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**.

Keep PR #4 open and unmerged. Next: verify the new CI and add genuine asset-backed shader fixtures; extend semantics and prove real GLES compile/link before connecting shader creation to the original renderer.
