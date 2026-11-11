# IW3 Android Phase HS — original buffer-storage portability (2026-11-02)

## Scope and verified baseline

Target: PR #4, `feature/iw3-native-android-arm64-20261025`, original
`third_party/KisakCOD/src/gfx_d3d` renderer. No Godot, replacement engine,
synthetic geometry, shader, map, or game frame was introduced.

Previous HR pass compiled the full authentic `r_state.cpp` for AArch64.
This pass first added an explicit AArch64 compile probe for the original
`r_buffers.cpp` translation unit. The probe failed, correctly, at
`r_buffers.cpp:30`: `IDirect3DDevice9` is opaque on Android, and
`D3DPOOL_DEFAULT` is unavailable. Later errors include the original
`CreateVertexBuffer`, `CreateIndexBuffer`, `Lock` and `Unlock` D3D9
methods. The original allocator is **not yet Android-compatible**.

## Concrete implementation

Added `r_android_buffer_storage.h/.cpp` under the genuine KisakCOD renderer
tree. This is an EGL-context-owned GLES3 resource provider for original
vertex/index resource identities. It creates actual VBOs/EBOs using
`glGenBuffers`, `glBindBuffer` and `glBufferData`; it can upload updates
with `glBufferSubData`, unregister resource identities, and delete its GL
objects. It registers successful creations with the existing genuine
`R_ChangeStreamSource` and `R_DrawIndexedPrimitive` GLES3 boundaries.
The provider checks the owning EGL context, nonzero and representable byte
counts, 16-bit index alignment, update bounds, GL errors, and restores
previous target bindings on normal/error paths. It rejects duplicate handles.
Context invalidation does not issue GL calls after context destruction.

**Important limitation:** the original `R_AllocStaticVertexBuffer`,
`R_AllocDynamicVertexBuffer`, `R_AllocStaticIndexBuffer`,
`R_AllocDynamicIndexBuffer`, lock/unlock, and resource shutdown call sites
in `r_buffers.cpp` are **not wired** to this provider. No D3D9 pointer is
fabricated, and this pass does not claim the original allocator compiles.
The next pass must implement a real original-handle lifecycle and CPU staging
contract (including dynamic locks, discard/no-overwrite, index/vertex uploads)
before connecting those call sites, then compile/link the full translation unit.

## Reproducible checks

- Host: `python3 -m unittest discover -s tests -p 'test_iw3_android_renderer_*.py' -v`.
  CI passed **48/48** tests including the new
  `test_iw3_android_renderer_original_buffer_storage_gles3.py` under
  AddressSanitizer and UndefinedBehaviorSanitizer. GL/EGL functions were
  mocked. Cases cover real buffer allocation calls, uploads, updates,
  registration, binding preservation, bounds, duplicates, context loss,
  failed GL operations, and release.
- Android NDK: `aarch64-linux-android26-clang++ -std=c++20 -O2 -fPIC -shared
  -Wl,--no-undefined` successfully linked the new storage provider together
  with the original stream/index GLES3 boundaries against `-lEGL -lGLESv3`.
  ELF target: AArch64. This is a provider-only shared library.
- The full original `r_state.cpp` still compiles AArch64. The diagnostic
  `r_buffers.cpp` compile probe still fails at D3D9 resource methods.
- CI evidence: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41467849396
  (commit `bfef79ec936bf85459087519237928deb709085c`).

## Runtime gate

`IW3_GLES3_ORIGINAL_HANDLE_BUFFER_STORAGE_AARCH64_LINKED=true`

`IW3_ORIGINAL_R_BUFFERS_CALLSITES_WIRED=false`

`IW3_ORIGINAL_R_BUFFERS_AARCH64_COMPILED=false`

`IW3_RENDERER_FRAME_PROVEN=false`

`IW3_REAL_MAP_LOADED=false`

`IW3_GAMEPLAY_PROVEN=false`

`IW3_PLAYABLE_APK=false`

There is no hardware evidence of an authentic IW3 frame or playable Android
APK. JNI diagnostic APKs remain diagnostic only. PR #4 must stay open and
must not be merged into main until actual Android ARM64 gameplay is proven.
