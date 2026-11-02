# Phase HC — original IW3 RC_SET_VIEWPORT to GLES3 (NOT GAME)

Date: 2026-11-01 (America/Puerto_Rico). PR #4, branch `feature/iw3-native-android-arm64-20261025`. Original KisakCOD IW3 only. No Godot, no substitute renderer, no main merge, no playable APK claim.

## Source/CI audited before editing

Starting head `e1e8e0e9a2052eec78ed734772ae972bc8bcc891`. The renderer CI run [41369749136](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41369749136) completed successfully, with the existing 32 host renderer regressions and ARM64 GLES clear-provider link. This does NOT prove actual GPU pixels. The previous HB clear fix depends on `GL_VIEWPORT`, but original `RB_SetViewportCmd` only called `R_SetViewportStruct` to mutate the IW3 source state, and never applied a GLES3 viewport. That makes the new viewport-scoped clear unsafe for sequences using original `RC_SET_VIEWPORT`.

## Implemented

- `third_party/KisakCOD/src/gfx_d3d/r_android_viewport.h/.cpp`: GLES3 provider for the **original IW3 viewport command**, translating D3D9 top-left coordinates to GLES3 bottom-left using the original render-target height, not EGL window height. Requires current EGL display/context; rejects zero/negative dimensions, out-of-target bounds, signed-overflow candidates and GL errors. No fake pixels or shaders.
- `third_party/KisakCOD/src/gfx_d3d/rb_backend.cpp`: original `RB_SetViewportCmd` still calls `R_SetViewportStruct` and, on Android only, calls the provider with the actual `GfxCmdSetViewport` fields and IW3 `renderTargetWidth/Height`. Fails closed on errors. Windows D3D9 path unchanged.
- `tests/test_iw3_android_renderer_original_viewport_gles3.py`: compiles/executes the actual provider on LP64 host under ASan/UBSan with mocked EGL/GLES. Covers full target, subviewport, offscreen target, invalid dimensions/bounds, INT_MAX overflow, absent context, existing GL errors, failed GL call, and recovery. Asserts original command wiring.
- `.github/workflows/iw3-renderer-init-arm64.yml`: host test discovery plus required Android NDK `--no-undefined` shared-object link of viewport provider against real `-lEGL -lGLESv3`; includes artifact. This is NOT a complete IW3 renderer link.

Implementation commits: `450c05dd`, `076a2cea`, `650661a6`, `1b580fe8`, `a2eba956`.

## Validation status

CI triggered by workflow/source changes; inspect the latest run associated with `a2eba95685ee43cb47b3f6c69e8e55428823be3e` and update this document with verified results only. Host GL/EGL calls are mocks; the Android NDK link does not run a frame.

## Hard blockers

The renderer's `R_InitGraphicsApi`, render-target/FBO creation and switching, material/shader translation, geometry draws, and complete presentation remain unimplemented. The original `R_SetViewportStruct` normally defers D3D9 hardware viewport application until state consumption; Android now eagerly applies the GLES viewport for `RC_SET_VIEWPORT`, so later integration must reconcile lazy state and render-target changes. No real map, touch-driven original game loop, weapons or actors have been demonstrated on an ARM64 Android device. JNI diagnostic APK is NOT playable.

`IW3_RENDERER_BACKEND_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_TOUCH_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

Keep PR #4 open and unmerged.
