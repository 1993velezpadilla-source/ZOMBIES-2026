# IW3 Android phase IA — bounded authentic D3D9 DCL declarations (NOT GAME)

Date: 2026-11-02. PR #4; branch `feature/iw3-native-android-arm64-20261025`.

## Baseline and next portability blocker

The authentic KisakCOD `r_material.cpp` and `rb_shade.cpp` compile for Android ARM64 but deliberately reject D3D9 shader execution. The prior HZ pass decoded a restricted MOV/ADD arithmetic subset, but original shader DCL declarations (input/output semantics and sampler texture classes) were still opaque. Without decoding these original declarations there is no defensible mapping to GLES3 vertex attributes, shader IO or samplers.

## Implemented in the original engine source

- `third_party/KisakCOD/src/gfx_d3d/r_android_shader_bytecode.h/.cpp`: `R_AndroidVisitD3D9Declarations` reads DCL opcode 31 from the **original D3D9 bytecode**, exposing raw declaration token, usage, usage index, texture class and split-bit register metadata.
- Validates stage-appropriate input/output register classes, SM2 pixel texture coordinates, sampler type 2D/cube/volume, defined usage indices and reserved declaration bits. Rejects relative addressing, nonzero register modifiers/shifts, unsupported opcodes and predication.
- Performs structural validation and a full semantic prevalidation pass before any callback, preventing partial DCL results from malformed later declarations.
- `tests/test_iw3_android_renderer_original_shader_bytecode_preflight.py`: host ASan/UBSan regression for vertex input/output declarations, pixel SM2 texture-coordinate input, 2D/cube samplers, late invalid usage with zero callbacks, invalid sampler class, relative-addressed register, wrong shader stage, unsupported opcode and visitor abort.

No GLSL ES 3.0 shader generation, program linking, VAO binding, authentic map rendering or Android gameplay is claimed. No replacement engine or fake shader was introduced. Windows D3D9 remains untouched.

## Validation and evidence

Commits: `3f85d513` (declarations API), `283d9430` (original engine DCL decoder), `000ce837` (sanitizer regression).

The existing `.github/workflows/iw3-renderer-init-arm64.yml` monitors all three edited paths. Its host test step runs `python3 -m unittest discover -s tests -p 'test_iw3_android_renderer_*.py' -v` with an ASan/UBSan C++ harness. Its Android NDK step probes the authentic AArch64 shader provider. **CI for this new head must be inspected before claiming the new regression passed**; workflow queued/pending at documentation time. This is source implementation evidence, not runtime gameplay evidence.

`IW3_D3D9_DCL_DECODER_SOURCE=true`
`IW3_D3D9_DCL_DECODER_CI=UNVERIFIED_AT_DOCUMENT_WRITE`
`IW3_GLSL_ES3_TRANSLATION=false`
`IW3_GLES3_PROGRAM_LINKED=false`
`IW3_FULL_RENDERER_LINKED=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_TOUCH_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

## Next authentic-engine gate

Confirm the renderer CI at the new head. Decode D3D9 shader input/output semantics and real instruction operands against genuine IW3 shader assets; implement fail-closed GLSL ES 3.0 generation and compile/link real GPU programs; connect original material/shader samplers, uniforms and vertex declarations to GLES3; then prove original IW3 map loading, a real rendered frame, touch input and gameplay/actors/weapons on ARM64 Android. The JNI APK is diagnostic only. Do not merge PR #4.
