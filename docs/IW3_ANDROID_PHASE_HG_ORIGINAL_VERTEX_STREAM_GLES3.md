# Phase HG — authentic IW3 vertex-stream GLES3 boundary (2026-11-02)

## Baseline (verified before edits)
- PR #4 open/unmerged; baseline head `45d7e2a79523eb6faa2c7bdeaf98c76c46d31dd1`.
- Renderer workflow `41385452013` completed successfully at the HF baseline. This was a host sanitizer + AArch64 *partial* provider link, not a running renderer.
- The original `r_state.cpp` still called Direct3D9 `device->SetStreamSource` unconditionally, blocking full ARM64 translation-unit compilation. The prior indexed-draw GLES3 bridge did not supply original stream bindings.
- `R_InitGraphicsApi`, original vertex-buffer allocator, vertex declarations, shader/material translation, and map/gameplay runtime are still incomplete.

## Implementation
- Preserve the original Windows D3D9 `R_ChangeStreamSource` path; on Android route the same original function to `R_AndroidGlesChangeStreamSource`, fail fatally on invalid binding.
- Add `r_android_vertex_stream.cpp/.h`: map an **existing** original opaque IW3 vertex-buffer handle to a **real, already allocated** GLES3 buffer. Verify `glIsBuffer`, `GL_BUFFER_SIZE`, EGL display/context ownership, byte offset and stride; track the two original stream slots independently.
- Temporarily bind `GL_ARRAY_BUFFER` only to inspect the actual GL buffer size and restore the previous binding even on GL errors. Binding `GL_ARRAY_BUFFER` does not itself configure a VAO or vertex attributes.
- Support explicit unbind, unregister, and context-loss invalidation without fabricating or deleting GPU resources owned elsewhere.
- Add `test_iw3_android_renderer_original_vertex_stream_gles3.py`: mocked EGL/GLES host regression with ASan/UBSan covering registration, offsets, strides, stream separation, invalid context, GL failure and state preservation.
- Update renderer workflow to run this host test and compile/link the provider as an AArch64 ELF shared object against genuine Android EGL/GLESv3. This is not a full-engine link.

## Verified CI after implementation
- **GitHub Actions run [41394106079](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41394106079)** (head `aa7362a77a315a53189c09af785d417c3f8cd37c`): both jobs completed **success** on 2026-11-02.
- Host `renderer-tracking-host`: **37/37 tests passed** including the new vertex stream mock-EGL/GLES regression with AddressSanitizer/UndefinedBehaviorSanitizer. No device execution.
- NDK `original-renderer-compile-probe`: ELF64/AArch64 shared provider linked against real EGL/GLESv3, `IW3_ORIGINAL_VERTEX_STREAM_GLES3_AARCH64_LINKED=true`; this is a provider-only link.
- Full original `r_state.cpp` compile **still fails** (`IW3_ORIGINAL_R_STATE_AARCH64_COMPILED=false`), now first observed at line 295: `IDirect3DDevice9::SetRenderState` and missing `D3DRS_SEPARATEALPHABLENDENABLE`, then two-sided stencil, depth, alpha test, cull, etc. This confirms the stream-source D3D call is no longer the first compile blocker, but **does not** imply the whole file is portable.
- CI explicitly prints `IW3_PLAYABLE_APK=false`.

## Evidence and next gate
- Initial commits: `2fc0fa3d`, `29e2346d`, `98132dd0`, `c035bb5c`, `98e83555`.
- Verified post-fix CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41394106079.
- The original `r_state.cpp` **still** has additional Direct3D9 render-state calls. A green provider build cannot imply this entire translation unit compiles.
- Next: wire the *actual* original IW3 VBO allocator to register/unregister resources; connect original vertex declarations to `glVertexAttribPointer` and VAO state; resolve render-state D3D9 operations and full engine link. Then verify actual rendering, map loading, touch input and gameplay on device.
- `IW3_ORIGINAL_VERTEX_BUFFER_ALLOCATOR_WIRED=false`
- `IW3_ORIGINAL_VERTEX_DECLARATION_VAO_WIRED=false`
- `IW3_RENDERER_FRAME_PROVEN=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

**This is a portability seam on the authentic KisakCOD IW3 engine, NOT a game or playable APK.** Do not merge to main until real on-device evidence exists.
