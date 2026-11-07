# IW3 Android phase HY — prevalidated authentic D3D9 instruction boundaries (NOT GAME)

Date: 2026-11-02. PR #4; branch `feature/iw3-native-android-arm64-20261025`.

## Baseline and blocker

At baseline `d81be6f4`, GitHub Actions renderer run 41509512662 completed successfully (54/54 host tests, ARM64 shader preflight compile/link), but the original IW3 renderer still has **no D3D9-to-GLSL ES 3.0 translator**, GPU shader program, map frame, or playable APK. The preflight could only return aggregate counts, so a later translator could not consume validated instruction boundaries or distinguish COMMENT payloads from opcodes without reimplementing the walker.

## Changes

- Added `IW3AndroidShaderInstruction` and `R_AndroidVisitD3D9Shader` in the existing original-engine Android shader-bytecode provider. The API exposes DWORD instruction offset, raw instruction token, opcode, encoded operand count and predicate bit; COMMENT and END are not emitted.
- **Two-pass fail-closed behavior**: fully validate the serialized stream before delivering any instruction callback. Malformed/truncated bytecode yields no callback; explicit callback rejection aborts traversal. Reads use `memcpy` to avoid unaligned/aliasing undefined behavior.
- Reject invalid stage enum values rather than treating them as pixel shaders.
- Extended existing ASan/UBSan host regression for boundaries, comments, predication, malformed input, callback abort, invalid stage and unaligned source bytes.
- Original Windows Direct3D9 shader loading and Android fail-closed shader paths remain unchanged. No replacement engine, fake shader or synthetic map.

## Verification gates

The host test is `tests/test_iw3_android_renderer_original_shader_bytecode_preflight.py`; the existing renderer GitHub Actions workflow also runs Android NDK AArch64 compile/link probes. **Do not mark green until the workflow at this commit actually finishes.** All host shader tests use synthetic D3D9 token arrays, not production shader assets or device GPU execution.

`IW3_ORIGINAL_D3D9_INSTRUCTION_BOUNDARIES_AVAILABLE=true` (source/API)
`IW3_ORIGINAL_SHADER_TRANSLATED_TO_GLES3=false`
`IW3_GLES3_SHADER_PROGRAM_LINKED=false`
`IW3_FULL_RENDERER_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_TOUCH_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

## Next implementation

Decode genuine D3D9 register types, swizzles, write masks, relative addressing and opcode semantics into a validated IR, then translate the real asset shaders to GLSL ES 3.0 and link GLES3 programs with the original materials, uniforms, samplers, VBO/EBO and vertex attributes. Only then attempt full engine bootstrap/map/device gameplay proof. The JNI APK remains diagnostic only. Leave PR #4 open and unmerged.
