# IW3 Android Phase HW — authentic D3D9 shader token framing (2026-11-02)

## Baseline and scope

PR #4, branch `feature/iw3-native-android-arm64-20261025`.
The preceding HV pass compiled the complete original `r_material.cpp` and
`rb_shade.cpp` for ARM64, but **neither file provides translated GLES3
shaders**. The original `Load_CreateMaterialPixelShader` and
`Load_CreateMaterialVertexShader` still fail closed rather than substituting
unrelated programs. The JNI APK is diagnostic-only.

## Implemented in genuine KisakCOD source

The prior `R_AndroidInspectD3D9Shader` checked the version tag and scanned
**every DWORD** for `0x0000FFFF`. That incorrectly rejected a valid shader
whose D3D9 COMMENT payload contained that value; it also failed to distinguish
instruction operands from opcodes.

- `r_android_shader_bytecode.cpp/.h`: walk SM2/SM3 instruction boundaries
  using the encoded operand count; skip COMMENT payloads by their bounded
  15-bit length; recognize END **only at an instruction boundary and only
  at the end**. Reject truncated instructions, truncated comments, missing
  or premature END, unsupported SM1 PHASE, and incorrect MOV/ADD/DCL/NOP
  operand counts. Preserve the existing 65535-byte IW3 load-def size limit.
- Expose `instructionCount` and `commentCount` in the inspected envelope
  for future authentic shader inventory and translation work.
- Update the existing ASan/UBSan C++ harness to cover valid SM2/SM3 token
  framing, COMMENT payloads containing END, operand DWORDs containing END,
  invalid lengths and malformed termination. The original material/shade
  call sites are unchanged and remain fail-closed.

**Scope limitation:** This is a *structural* decoder, not full D3D9 opcode
or register validation. It is not HLSL, GLSL, a shader compiler, a linked
GLES program, a frame, or an APK.

## Evidence and next gates

Code commits: `5ac7273e`, `56ad5baa`, `b8f0f2fa`.
CI run triggered for this pass:
https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41508499913

CI results must be checked before marking the pass verified; the workflow
builds the actual AArch64 provider with NDK 27.2 and runs host sanitizers.

Next: decode original D3D9 instruction semantics/registers and produce
validated GLSL ES 3.0 equivalents for original IW3 materials, then bind
programs, uniform constants, sampler states, vertex semantics/VAOs, and
render authentic geometry. Complete the real engine bootstrap, map loading,
touch input, weapons and actors on ARM64 hardware.

`IW3_ORIGINAL_SHADER_TRANSLATED_TO_GLES3=false`

`IW3_GLES3_SHADER_PROGRAM_LINKED=false`

`IW3_FULL_RENDERER_LINKED=false`

`IW3_RENDERER_FRAME_PROVEN=false`

`IW3_REAL_MAP_LOADED=false`

`IW3_TOUCH_GAMEPLAY_PROVEN=false`

`IW3_PLAYABLE_APK=false`

Keep PR #4 open and unmerged. No completion notification.
