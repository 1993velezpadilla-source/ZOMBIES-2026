# IW3 Android Phase HU — authentic material vertex declaration metadata (2026-11-02)

## Scope and baseline

PR #4, branch `feature/iw3-native-android-arm64-20261025`.
Phase HT compiled the original `r_buffers.cpp` and its GLES3 storage bridge,
but the original material vertex declaration and shader path was not integrated.
This pass stays inside genuine KisakCOD IW3 source. No Godot, substitute
renderer, synthetic gameplay, or diagnostic APK presented as a game.

## Implemented in original code

- `r_d3d9_opaque.h`: retain the original 8-byte D3D9 vertex-element ABI on
  Android without constructing any fake Direct3D COM object.
- `r_material.cpp::Material_BuildVertexDecl`: preserve the original
  `s_streamSourceInfo` / `s_streamDestInfo` routing and pass the actual
  generated elements to an Android metadata registry. Fields are copied
  individually, avoiding strict-aliasing undefined behavior. The Windows
  `CreateVertexDeclaration` call remains untouched.
- `r_material.cpp::Material_ReleasePassResources`: release Android
  declaration metadata identities instead of calling COM `Release`.
- `rb_shade.cpp::R_SetVertexDecl`: select the registered original declaration
  identity and reject unknown handles. Windows keeps `SetVertexDeclaration`.
- `r_android_vertex_declaration.cpp/.h`: store the original declaration's
  stream, offset, type, method, semantic and usage index. Validation covers
  both streams, FLOAT2/3/4, D3DCOLOR, UBYTE4, SHORT4, POSITION, NORMAL,
  COLOR0/COLOR1 and TEXCOORD0–7; rejects invalid/duplicate shader semantics,
  unknown identities, unsupported types, and invalid offsets. Supports
  selection, copying, release, and explicit invalidation. No GLES VAO is
  created, no shader is translated, and no draw is claimed.
- Added a host ASan/UBSan regression and a pinned NDK ARM64 provider link
  check. New original `r_material.cpp` and `rb_shade.cpp` compile probes
  record their **real next blockers** rather than silently passing.

## Verified evidence

Code commit: `2c4c29bd20566762a0269d10bd22288d435df1ba`.

CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41487945581
(both jobs success).

- Host renderer regression suite: **52/52 tests passed**. The two new
  declaration tests include an executable C++ host harness with
  AddressSanitizer/UndefinedBehaviorSanitizer and leak detection.
- Android NDK 27.2: `r_android_vertex_declaration.cpp` compiled and linked
  into a genuine ELF64/AArch64 shared library using `--no-undefined`.
  `llvm-nm` confirmed the create/select/release symbols.
- Full genuine `r_material.cpp` ARM64 probe: **fails**, first errors at
  lines 298 and 313, `dx.device->CreatePixelShader` and
  `dx.device->CreateVertexShader`. No Android GLSL shader translator exists.
- Full genuine `rb_shade.cpp` ARM64 probe: **fails**, first errors at
  lines 87 and 91, `device->SetPixelShader`. The actual shader binding
  path is not ported. Reports are preserved as CI artifacts.
- These are **not** full material/shade translation-unit compilation passes,
  and the new metadata provider is **not** a VAO, shader, frame, map, or APK.

## Next hard gates

1. Implement a real, validated translation/loading path for original IW3
   shader assets to GLES3; do not interpret D3D9 bytecode as GLSL.
2. Build GLES3 VAOs from the registered original declaration semantics and
   real VBO stream state, including D3DCOLOR/BGRA conversion, stream strides,
   attribute formats and vertex-shader input location agreement.
3. Complete original material/shade TU ARM64 compilation and relocatable link,
   then full renderer and Android EGL engine bootstrap.
4. Verify genuine map data loading, on-device rendered frames, live touch
   input, weapons and actors via the original IW3 gameplay systems.

`IW3_ORIGINAL_VERTEX_DECL_METADATA_ARM64_LINKED=true`

`IW3_ORIGINAL_MATERIAL_AARCH64_COMPILED=false`

`IW3_ORIGINAL_RB_SHADE_AARCH64_COMPILED=false`

`IW3_ORIGINAL_VERTEX_DECL_GLES3_VAO_BOUND=false`

`IW3_FULL_RENDERER_LINKED=false`

`IW3_RENDERER_FRAME_PROVEN=false`

`IW3_REAL_MAP_LOADED=false`

`IW3_TOUCH_GAMEPLAY_PROVEN=false`

`IW3_PLAYABLE_APK=false`

The JNI diagnostic remains diagnostic-only. Keep PR #4 open and unmerged.
