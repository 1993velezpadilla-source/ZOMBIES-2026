# Phase GK — authentic IW3 renderer accepts narrow Android native-window modes

Status: **portability correction only; IW3_PLAYABLE_APK=false**. This is not a renderer, a playable APK, or proof of on-device graphics.

## Evidence and original-engine changes

The original KisakCOD `gfx_d3d/r_init.cpp` uses a hard-coded Windows minimum of 640x480 in `R_AddValidResolution` and `R_BuildDisplayModeDvars`. The Android JNI provider in `gfx_d3d/r_android_display.cpp` independently rejected any surface narrower than 640 pixels. A real Android native window can be portrait with width 360 and height 800, or landscape 800x360. Both were rejected before the original renderer could register `r_mode`. This was a concrete mobile initialization blocker, independent of the unresolved D3D9 draw backend.

The engine now accepts **actual** Android surface dimensions at least 320x320, in either orientation, while keeping the original Windows desktop 640x480 minimum. No fake D3D9 adapter or hard-coded Android resolution is created. The existing Android provider continues to read the actual `ANativeWindow` and `Display.getRefreshRate()` values and feeds the original `dx.displayModes` and `R_BuildDisplayModeDvars`. Mode values below 320 on either axis and invalid refresh rates remain rejected. Desktop minimum behavior is preserved by conditional compilation.

## Verification gates

- `tests/test_iw3_android_renderer_native_window_modes.py` exercises the **actual provider functions** extracted from the engine with JNI/native-window mocks, now including 360x800, 800x360, 319x800, and 320x319.
- `tests/test_iw3_android_renderer_display_modes_lp64.py` builds the **actual renderer display-mode functions** twice under host ASan/UBSan: Windows-style desktop minimum and `__ANDROID__` narrow-surface acceptance. Neither harness performs actual rendering.
- The existing Android NDK workflow must still compile the native provider and report the separate `r_init.cpp` AArch64 compile result. An Actions job passing is not equivalent to the complete renderer compiling.

## Remaining critical path

`r_init.cpp` still contains Direct3D9/Win32/x86 assumptions. EGL lifecycle support does not translate the original IW3 material, geometry, shader, and draw-command pipeline to GLES3. The original engine must be connected to the Android window, mount real map assets, render a real scene, and run original touch input, weapon and actor gameplay in a real ARM64 APK before any playable claim. Do not merge PR #4 to main or call the JNI diagnostic APK a game.
