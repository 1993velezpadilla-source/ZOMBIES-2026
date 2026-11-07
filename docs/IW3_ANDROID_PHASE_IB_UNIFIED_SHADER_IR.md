# IW3 Android phase IB — unified original D3D9 declaration/arithmetic IR (NOT GAME)

Date: 2026-11-02. PR #4, `feature/iw3-native-android-arm64-20261025`.
Scope: authentic KisakCOD `third_party/KisakCOD/src/gfx_d3d/r_android_shader_bytecode.{h,cpp}`, and `tests/test_iw3_android_renderer_original_shader_bytecode_preflight.py`.

## Baseline checked before editing

At `b3727693c738902528da80d91ed7ce21f0cb44f9`, renderer CI [41523217979](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41523217979) completed **success** for both jobs. Host log explicitly reported the shader bytecode sanitizer test `ok`; AArch64 compile probe linked the original shader-bytecode provider and compiled original `r_material.cpp`/`rb_shade.cpp`. The separate Android math workflow [41523217938](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41523217938) failed during **Android NDK installation**, not in this shader source; do not conflate its result with renderer CI. No GPU shader program, actual map frame, or playable APK was demonstrated.

## Actual blocker and implementation

The phase HZ arithmetic visitor deliberately rejected DCL instructions. The phase IA declaration visitor allowed MOV/ADD structurally but did not decode their register operands. Therefore neither API could provide a complete, semantically checked, *ordered* instruction sequence for an ordinary mixed DCL+arithmetic shader. A translator consuming either visitor alone could silently miss instructions or validate only a prefix.

Added `R_AndroidVisitD3D9DecodedShader` with `IW3AndroidShaderDecodedInstruction` tagged events. It reuses the existing authentic D3D9 declaration and arithmetic decoders, preserving original DWORD offsets and order. The first complete semantic pass rejects unsupported instructions, invalid declarations, relative addressing, predication, malformed registers and DCL after executable arithmetic **before any user callback**. The second pass emits declarations and arithmetic in source order. NOP has no emitted event. An explicit user callback rejection stops emission; previous callbacks may have been observed. The original D3D9 Windows path and Android fail-closed shader creation/binding are unchanged.

Host ASan/UBSan harness regressions cover a valid mixed shader, arithmetic-only shader, declaration offsets/order, a late malformed MOV after a valid DCL with zero callbacks, late DCL after MOV with zero callbacks, invalid later declaration, predication, unsupported opcode, callback rejection, null callback, and unaligned input.

## Verification and honest limitations

Implementation commits: `7576182c` (header), `23786995` (combined visitor), `10ca9cc2` (regressions). The CI run for the final documentation head must be checked independently; this record does **not** claim unverified tests passed.

This is an IR decoder for a **tiny DCL/MOV/ADD/NOP subset**, not D3D9→GLSL ES 3.0 translation. It does not implement source modifiers, destination shifts, saturation, shader constants, texture instructions, control flow, varying linkage, GLES3 programs, vertex attributes/VAOs, sampler binding or actual rendering. A successful preflight cannot stand in for real original asset shaders. Shader creation remains intentionally fail-closed. The next meaningful implementation gate is a faithful, fail-closed GLSL ES translator with real shader-asset fixtures and GPU compile/link evidence, then full original renderer integration.

`IW3_ORIGINAL_SHADER_TRANSLATED_TO_GLES3=false`; `IW3_GLES3_SHADER_PROGRAM_LINKED=false`; `IW3_FULL_RENDERER_LINKED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_TOUCH_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**. JNI APK is diagnostic only. Keep PR open and unmerged.
