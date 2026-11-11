# IW3 Android Phase HT — original r_buffers.cpp GPU storage and lock lifecycle (2026-11-02)

## Baseline, source and scope

PR #4, branch `feature/iw3-native-android-arm64-20261025`. Only the genuine
`third_party/KisakCOD/src/gfx_d3d` renderer was modified; no Godot, substitute
engine, synthetic scene or diagnostic-as-game claim.

Phase HS had a genuine GLES3 VBO/EBO storage provider, but the original
`r_buffers.cpp` did **not** compile for Android ARM64: its first blocker was
`IDirect3DDevice9::CreateVertexBuffer` / `D3DPOOL_DEFAULT` (line 30).
The initial HT integration compile exposed a remaining unguarded
`R_FinishStaticVertexBuffer -> vb->Unlock` call; this was corrected before
claiming the compilation gate.

## Implementation

- Added `r_android_buffer_handles.h/.cpp`: opaque, stable identity tokens for
  the original IW3 vertex/index pointer slots (not D3D9 COM objects), CPU
  staging for locks, bounds and 16-bit index alignment checks, single active
  lock per buffer, static/dynamic creation, DISCARD/NOOVERWRITE flag validation,
  partial GPU uploads on unlock, explicit release and post-context-loss
  invalidation. GPU storage remains in the existing GLES3 VBO/EBO provider.
- Routed the **original** `R_AllocStaticVertexBuffer`,
  `R_AllocDynamicVertexBuffer`, `R_AllocStaticIndexBuffer`,
  `R_AllocDynamicIndexBuffer`, lock/unlock, static finish/free and dynamic
  shutdown paths in `r_buffers.cpp` through this provider on Android.
  Preserved the original Windows D3D9 branches. The original
  `Load_VertexBuffer` behavior was restored and guarded by a regression.
- Added host ASan/UBSan tests for real GL storage calls under **mocked**
  EGL/GLES: static full upload, dynamic partial upload, alignment, invalid
  flags, duplicate lock, upload failure/retry, release while locked, context
  absence and cleanup.
- Extended the pinned Android NDK workflow to compile the complete original
  `r_buffers.cpp` as AArch64 and **relocatable-link** its object with the
  new handle lifecycle, GLES3 storage, original vertex-stream and indexed-draw
  bridge objects. The unresolved Android bridge symbols are checked. This is
  not a complete renderer link.

The dynamic DISCARD/NOOVERWRITE path currently uses staging plus
`glBufferSubData`; it does **not** guarantee D3D9-style GPU buffer renaming or
non-stalling performance. EGL context invalidation must be coordinated with
the original engine lifecycle. Rendering and gameplay are not demonstrated.

## Reproducible evidence

- CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41481388988
  at code commit `e992e8135bc9b130f09957dff332744576459755`, both jobs success.
- `python3 -m unittest discover -s tests -p 'test_iw3_android_renderer_*.py' -v`:
  **50/50** host tests passed (including two new buffer-handle tests);
  the GPU tests use mocked EGL/GLES with ASan/UBSan, not hardware.
- NDK `aarch64-linux-android26-clang++`: complete genuine
  `r_buffers.cpp` **compiled** as ELF64/AArch64. The GLES3 provider linked
  with `-Wl,--no-undefined -lEGL -lGLESv3`. A separate
  `ld.lld -r` pass combined the original `r_buffers.o` and all four
  Android buffer bridge objects, with no unresolved `R_Android*` symbols.
  Other engine and graphics symbols remain unresolved; **not** a full engine.
- Intermediate failure was observed in
  https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41480662708
  at `r_buffers.cpp:391` (`vb->Unlock`). The static-vertex-finish split was
  fixed, then verified in the later successful run.

## Hard gates

`IW3_ORIGINAL_R_BUFFERS_AARCH64_COMPILED=true`

`IW3_ORIGINAL_BUFFER_ALLOCATOR_RELOCATABLE_LINKED=true`

`IW3_ORIGINAL_BUFFER_ALLOCATOR_GLES3_RUNTIME_PROVEN=false`

`IW3_FULL_RENDERER_LINKED=false`

`IW3_RENDERER_FRAME_PROVEN=false`

`IW3_REAL_MAP_LOADED=false`

`IW3_TOUCH_GAMEPLAY_PROVEN=false`

`IW3_PLAYABLE_APK=false`

The next real engineering gates are original vertex declarations/VAOs, shaders,
materials, textures, complete renderer link and Android EGL engine startup;
then genuine map assets and touch-driven original weapon/actor gameplay on an
ARM64 device. The JNI diagnostic APK is not a playable IW3 APK. Keep PR #4
open and unmerged.
