# Phase HB — original IW3 viewport-scoped GLES3 clear semantics (NOT GAME)

Date: 2026-11-01. PR #4, branch `feature/iw3-native-android-arm64-20261025`. Genuine KisakCOD IW3 only; no Godot, substitute engine, main merge, or playable APK claim.

## Starting evidence and concrete blocker

The previous HA head `caff49a17d20e5866b01b96c7974b7e23b836b03` passed the renderer workflow [41363759835](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41363759835), including **32/32** host tests and ARM64 compilation/link of the original `RB_ClearScreenCmd` GLES3 provider. Both jobs completed successfully.

Code review revealed a semantic mismatch in the newly connected original IW3 `RC_CLEAR_SCREEN` consumer: the Windows original `R_ClearScreenInternal` invokes Direct3D9 `device->Clear(0, 0, ...)` with no rectangle list, which clears the **current viewport**. The Android GLES3 bridge instead disabled scissor and called `glClear`, which ignores `glViewport` and could erase outside the active IW3 viewport (split-screen or a smaller render-target viewport). That is not a correct translation of the authentic render command.

## Implemented on original renderer branch

- `third_party/KisakCOD/src/gfx_d3d/r_android_clear.cpp`: query the active GLES3 `GL_VIEWPORT` and existing `GL_SCISSOR_BOX`, reject zero-sized viewport, temporarily enable scissor and set its rectangle to the current viewport for the original `GfxCmdClearScreen` attachment bitmask, then restore the original scissor box and enable state. Preserve the previous color/depth/stencil write masks and clear values. Desktop Direct3D9 is unchanged.
- `tests/test_iw3_android_renderer_original_clear_gles3.py`: extend the existing ASan/UBSan regression executing the actual provider with mocked EGL/GLES to assert viewport-scoped clear, preservation of enabled and disabled scissor states and their rectangles, zero-size rejection, attachment masks and GL-error fail-closed behavior.
- No synthetic frame, shader, map, or replacement renderer is introduced.

Source commit: `941e5d3cc3e781ef787c2e7ab9156de6df3a9901`. Test commit: `a7791c5be2724e31bab10788ceb1ed9622414510`.

## Verification

The source and test changes trigger `.github/workflows/iw3-renderer-init-arm64.yml` for both the host sanitizer suite and Android NDK ELF64/AArch64 compile/link with `--no-undefined -lEGL -lGLESv3`. New run: [41369708793](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41369708793). **Status at document creation: queued/pending; do not call this green until both jobs finish and logs are checked.**

The GLES test uses mocked GL/EGL calls, not an actual ARM64 device or real GPU pixels. Passing compilation and host tests alone does not prove a rendered IW3 frame.

## Remaining hard gates

- Original IW3 `R_InitGraphicsApi` still fails closed; GLES3 material, shader, geometry, FBO/render-target and complete frame execution remain missing.
- No real map loading into a fully running ARM64 client, no proven live touch-to-original-gameplay loop, no actual IW3 weapons/actors rendered on Android.
- The JNI APK remains diagnostic only.

`IW3_ORIGINAL_CLEAR_VIEWPORT_SEMANTICS_SOURCE_WIRED=true` (pending CI validation)  
`IW3_RENDERER_BACKEND_LINKED=false`  
`IW3_RENDERER_FRAME_PROVEN=false`  
`IW3_REAL_MAP_LOADED=false`  
`IW3_TOUCH_GAMEPLAY_PROVEN=false`  
`IW3_PLAYABLE_APK=false`

Keep PR #4 open and unmerged. Next substantive graphics milestone: translate the original lazy viewport/render-target application and real GLES3 draw geometry/material/shader pipeline, then test an authentic map frame on an ARM64 device.
