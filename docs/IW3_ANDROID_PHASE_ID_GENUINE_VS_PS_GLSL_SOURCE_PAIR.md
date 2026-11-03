# Phase ID — original IW3 D3D9 VS/PS GLSL ES 3.0 source pair (NOT GAME)

Date: 2026-11-02 (Puerto Rico). Target: PR #4, `feature/iw3-native-android-arm64-20261025`.

## Prior verified baseline

Commit `31ade9774f0dd93b145682492db07c1fdced4cb4` passed renderer workflow [41543505013](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41543505013) (two successful jobs). The prior translator emitted only a tiny ps_3_0 COLOR0 MOV/ADD source string, **not** a GPU shader. No authentic Android IW3 scene was rendered.

## Next portability gap and changes

The existing ps_3_0 GLSL ES 3.00 source incorrectly used `layout(location = 0) in vec4 iw3_color_in0;` for a fragment shader input. GLSL ES 3.00 does not permit location qualifiers on fragment inputs. Changed this to `in vec4 iw3_color_in0;`, allowing varying linkage by matching the vertex output name.

Added `R_AndroidTranslateD3D9VertexPositionColorSubsetToGLSL` to the **original KisakCOD IW3 renderer's Android shader bytecode bridge**. It accepts a narrowly defined authentic `vs_3_0` stream only: `dcl_position0 v0`, `dcl_color0 v1`, `dcl_position0 o0`, `dcl_color0 o1`, `mov o0, v0`, `mov o1, v1`. It uses the existing bounded D3D9 token inspector and two-pass decoded visitor, not a surrogate engine or geometry. The emitted vertex source has legal ES3 vertex attribute locations and a name-matched `out vec4 iw3_color_in0` compatible with the pixel subset. D3D [0,w] clip-depth is remapped to GLES [-w,w] as `2*z-w`.

The implementation deliberately fails closed for missing/duplicate declarations, unsupported semantics or registers, wrong shader stage/model, modified/swizzled operands, partial masks, ADD or other unsupported instructions, and truncated streams. On failure, output GLSL is empty. No fallback shader or fake gameplay was introduced. The Windows Direct3D9 implementation was not replaced.

## Regression coverage

Expanded `tests/test_iw3_android_renderer_original_shader_bytecode_preflight.py` with genuine D3D9 token fixtures for the vertex+pixel source pair and negative cases. The harness is compiled with `-D__ANDROID__ -fsanitize=address,undefined -fno-omit-frame-pointer`. The regression checks name-matched varyings, vertex clip-depth conversion, the removal of the illegal fragment input location qualifier, fail-closed behavior and absence of partial output.

**Verification must be evaluated on the CI run associated with the final test commit, not earlier green runs.** This pass does not claim successful GLSL GPU compilation or linked execution until demonstrated. The renderer workflow is the "IW3 authentic renderer LP64 tracking and AArch64 compile probe (NOT GAME)" workflow.

## Unmet playable-APK gates

The VS/PS subset is source text only and covers very few actual IW3 shader programs. There is no GLES3 GPU compile/link, uniform/sampler binding, VAO attribute binding, texture/material translation, integrated original render loop, authentic map loading or demonstrated Android ARM64 touch/gameplay/weapon/actor execution. JNI diagnostic artifacts are not playable games. Keep `IW3_PLAYABLE_APK=false` and PR #4 open/unmerged.

Next work: validate generated source with an actual GLES3 shader compiler and program linker; map D3D shader input/output semantics and registers against real material shaders, then connect original `r_material.cpp` and `rb_shade.cpp` shader bind paths without pretending this narrow subset supports arbitrary IW3 materials.
