# IW3 Android phase HF — authentic indexed-draw GLES3 boundary (2026-11-02 UTC)

**Completion gate: IW3_PLAYABLE_APK=false.** This change is not a playable APK, not a frame capture, and not proof of an Android device render. Godot and replacement engines are not involved.

## Verified starting point

PR #4 head before this pass: `e5149103f771a72734b06f058caa78a9f0e3f977`. The previous HE renderer tests passed 35/35 and the full authentic `r_state.cpp` still failed Android AArch64 compilation due to Direct3D9 methods, including `SetIndices`, `SetStreamSource`, `SetRenderState`, and `DrawIndexedPrimitive`. An ELF64 relocatable link with unresolved external symbols is **not** a complete renderer.

## Concrete implementation

- `r_state.cpp` keeps Windows Direct3D9 calls unchanged, while its **original** `R_ChangeIndices` and `R_DrawIndexedPrimitive` call a new Android GLES3 boundary. IW3 draw-count filtering, skip-draw option, and `RB_TrackDrawPrimCall` remain in the original function.
- `r_android_indexed_draw.cpp/.h` maps the original opaque index-buffer handle to a real GLES3 `GLuint` registered by the future original resource allocator; it never creates placeholder buffers or geometry. `R_AndroidGlesBindIndexBuffer` binds `GL_ELEMENT_ARRAY_BUFFER` and rolls back a failed bind.
- The draw checks a live matching EGL context, registered original index-buffer identity, nonzero shader program, VAO, enabled vertex attribute zero with VBO, bound index buffer, real GPU buffer size, triangle count, base-index arithmetic and index bounds. Only then does it issue **real** `glDrawElements(GL_TRIANGLES, ..., GL_UNSIGNED_SHORT, ...)`. Any missing dependency is a hard failure in the original IW3 call site, not a simulated successful draw.
- `R_AndroidGlesInvalidateIndexBuffers` drops identity mappings without stealing ownership of GPU objects. The EGL shutdown and original index-buffer allocator are **not yet wired** to it.
- `tests/test_iw3_android_renderer_original_indexed_draw_gles3.py` exercises positive/negative behavior with mocked EGL/GLES under ASan/UBSan and statically verifies the original call sites and preserved Windows code. **Mocks do not prove device execution.**
- `.github/workflows/iw3-renderer-init-arm64.yml` includes the new regression and a real NDK AArch64 `-Wl,--no-undefined` link against `-lEGL -lGLESv3`. It continues reporting `IW3_PLAYABLE_APK=false`.

## Actual remaining gates

1. Port original `r_buffers.cpp` index allocation/lock/upload/free (its original index format is `D3DFMT_INDEX16`, matching `GL_UNSIGNED_SHORT`), and call the registration/unregistration API only for genuine engine buffers.
2. Port `R_ChangeStreamSource`, vertex-buffer allocation, attribute formats/offsets and VAO ownership; an index draw cannot execute until a genuine vertex layout is bound.
3. Complete remaining `r_state.cpp` Direct3D9 render-state calls, shader/material backend, target creation and presentation; obtain a **fully linked** executable engine, not just `ld.lld -r` objects.
4. Prove actual IW3 map loading, real touch consumption, actors/weapons and rendered frames on an ARM64 Android device. The JNI diagnostic package does not satisfy this.

## CI evidence

New renderer workflow: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41385393195

At documentation creation the run was **pending**. Do not claim its host sanitizer or ARM64 link jobs passed until the completed run and logs are inspected. A green test workflow still would not prove a playable game.
