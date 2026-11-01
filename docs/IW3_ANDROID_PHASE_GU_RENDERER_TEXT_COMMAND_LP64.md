# IW3 Android phase GU — original renderer 2D text command LP64 safety

Date: 2026-11-01. Branch: `feature/iw3-native-android-arm64-20261025`. PR: #4.

## Real defect and fix

In the authentic KisakCOD `gfx_d3d/r_rendercmds.cpp`, both
`AddBaseDrawTextCmd` and `AddBaseDrawConsoleTextCmd` allocated their
`GfxCmdDrawText2D` command using `(textLength + 84) & 0xFFFFFFFC`.
The constant 84 encodes the original 32-bit ABI. The command contains
`Font_s*` and two `Material*` fields, so the `text[]` payload is
later in the 64-bit structure. Copying the text and terminating NUL
could write beyond the reserved command-buffer allocation, corrupting
the next renderer command.

Both original producers now call `R_DrawText2DCommandBytes()`, which
uses `offsetof(GfxCmdDrawText2D, text)` plus the text length and
terminator, preserves 4-byte command alignment, and refuses a size that
cannot fit the original 16-bit `GfxCmdHeader::byteCount`. This
does **not** replace the command producer or renderer with a mock.

The existing Windows 32-bit command layout is preserved by the
offset-based expression; on LP64 the allocation grows with the native
pointer layout. No new GLES backend is claimed.

## Evidence

- GitHub Actions: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41330959401
- Host original-renderer suite: **23/23 passed** with the new
  `test_iw3_android_renderer_text_command_lp64.py` regressions.
- The test compiles the **actual** `GfxCmdDrawText2D` declaration
  and the original source helper in an ASan/UBSan C++20 harness,
  exercises text lengths 0, 1, 2, 3, 4, 255, 4096 and rejection near
  the 65535-byte command limit, and verifies allocation bounds.
- The genuine `r_init.cpp` and `r_rendercmds.cpp` still compile
  as separate Android AArch64 objects. Their unresolved-symbol counts
  remain **75** and **125**, respectively. The Android EGL platform
  provider links separately. None is a linked original renderer.
- Windows SP and killhouse are separate diagnostics; they are not
  evidence of Android gameplay.

## Strict completion gate

`IW3_RENDERER_BACKEND_LINKED=false`,
`IW3_RENDERER_FRAME_PROVEN=false`,
`IW3_PLAYABLE_APK=false`.

The next blockers remain a **real** GLES3 command backend (geometry,
materials, shaders, textures and GPU resources), linking the original
renderer dependencies, loading map assets, connecting touch controls,
and demonstrating gameplay/actors/weapons on a running ARM64 APK.
Compiling original translation units or a JNI diagnostic APK does
not meet the playable-game requirement. Do not merge PR #4 to main.
