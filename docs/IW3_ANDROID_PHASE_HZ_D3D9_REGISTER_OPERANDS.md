# IW3 Android phase HZ — original D3D9 arithmetic register metadata (NOT GAME)

Date: 2026-11-02. PR #4; branch `feature/iw3-native-android-arm64-20261025`.

## Verified baseline

At `c42cb35cc1e8da6a0d80b7735eef3ef31fdaa5fb`, renderer GitHub Actions run [41519976814](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41519976814) completed successfully, including host sanitizers and the AArch64 bytecode preflight link. These are component tests, **not** real rendering or an APK gameplay proof.

## Concrete next blocker and changes

The original D3D9 shader walker exposes only instruction boundaries. Before authentic GLSL ES 3.0 translation, MOV/ADD destination/source registers must be decoded without mistaking D3D9's split register-type bits, source swizzles, destination write masks or register modifiers for GLSL semantics.

Changed the genuine KisakCOD source `third_party/KisakCOD/src/gfx_d3d/r_android_shader_bytecode.h/.cpp`:

- Added `R_AndroidDecodeD3D9Register`, extracting the original 11-bit register number, **split** five-bit register type, destination write mask/shift/modifier, source swizzle/modifier and relative-addressing bit. Invalid register-token prefix, reserved types/modifiers and zero destination masks fail closed.
- Added `R_AndroidVisitD3D9Arithmetic` for a deliberately limited, non-predicated, non-relative **MOV/ADD/NOP** subset. It uses the existing bounded D3D9 structural walker and performs a **full semantic prevalidation pass before callbacks**, so unsupported later instructions cannot leak earlier partial decoded results.
- COMMENT payloads and NOP are not emitted as arithmetic. Unsupported DCL, unknown opcodes, predication and relative addressing are rejected, **not ignored**. There is no GLSL generation, GPU shader creation or fallback shader.
- Extended the existing ASan/UBSan Python/C++ harness to cover split register types, masks, swizzles, bad modifiers, reserved types, relative addressing, MOV/ADD metadata, comments, later invalid instruction with zero callbacks, predication rejection, unsupported opcode and visitor abort.

The original Windows Direct3D9 shader creation and Android fail-closed shader loading/binding remain unchanged. No Godot, replacement engine, fabricated weapon, map or rendering.

## Evidence and honest gates

Source/test commits: `525359a5`, `6c744f52`, `29d6ebed`. The workflow `.github/workflows/iw3-renderer-init-arm64.yml` watches all three modified paths, runs `python3 -m unittest discover -s tests -p 'test_iw3_android_renderer_*.py' -v` with host ASan/UBSan, and links the bytecode provider with Android NDK AArch64 `--no-undefined`.

**This document records source changes, not a CI pass at the new head.** Confirm the workflow run and any sanitizer/compiler failures before marking HZ verified.

`IW3_ORIGINAL_D3D9_MOV_ADD_REGISTER_DECODER_SOURCE=true`
`IW3_ORIGINAL_D3D9_MOV_ADD_REGISTER_DECODER_CI=UNVERIFIED_AT_DOCUMENT_WRITE`
`IW3_ORIGINAL_SHADER_TRANSLATED_TO_GLES3=false`
`IW3_GLES3_SHADER_PROGRAM_LINKED=false`
`IW3_FULL_RENDERER_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_TOUCH_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

## Next

After passing HZ tests, decode DCL and the remaining real D3D9 instruction/register semantics (including predicate, relative addressing, constant registers, outputs and source modifiers) against actual legally supplied IW3 shader assets. Translate validated original shader instructions into GLSL ES 3.0, create and link GLES3 programs, bind original uniforms/samplers and VAO attributes, then connect original material/shade draw paths and prove an Android ARM64 map frame, input and gameplay. JNI remains diagnostic only. Leave PR #4 open and unmerged.
