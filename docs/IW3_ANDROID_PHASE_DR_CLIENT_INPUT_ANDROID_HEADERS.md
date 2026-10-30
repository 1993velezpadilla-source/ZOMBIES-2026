# IW3 Android phase DR — original client-input translation unit

**Date:** 2026-10-30  
**Branch:** `feature/iw3-native-android-arm64-20261025`  
**PR:** #4

## Blocker found

The Android touch hook had been audited by extracting the original `CL_CreateCmd()` body, but the complete original `client/cl_input.cpp` translation unit was not part of the Android CMake build. Its include chain reached `win32/win_local.h`, which unconditionally included Win32 DirectInput and Winsock headers and exposed Win32-only window types. That prevented compiling the actual client-input translation unit with the Android NDK.

## Changes

- Guarded DirectInput/Winsock/IPX SDK includes and window-only declarations in `win_local.h` so they remain available to Windows builds but are not required by Android.
- Used ABI-equivalent `int` declarations for the two BOOL-shaped APIs on Android; the Windows declarations are unchanged.
- Added `iw3_sp_client_input_full_compile`, an Android-only OBJECT target compiling the full upstream `client/cl_input.cpp` with the real SP and OpenAL definitions. It is deliberately not linked into JNI.
- Added an ARM64 audit that verifies ELF64/AArch64, the original `CL_CreateCmd(usercmd_s*)` symbol, and its unresolved touch-platform edge.
- Fixed the next compile blocker exposed by that target: DevGui's pointer-bearing runtime structs had Win32-only hard-coded sizes. The header now preserves the original 32-bit sizes and asserts the observed LP64 sizes (`DevMenuChild=8`, `DevMenuItem=0x30`, `devguiGlob_t=0x70E0`). These are process-local structures, not serialized asset records.
- Extended the layout regression set from 8 to 11 assertions.

## Verification

The original full Android ARM64 workflow passed on run [41021851085](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41021851085). Its source preflight reported **359 tests, OK**. The log contains `IW3_ORIGINAL_CLIENT_INPUT_AARCH64_OBJECT_PASS` and the defined `CL_CreateCmd(usercmd_s*)` symbol; the initial attempt failed on the three DevGui size assertions, and the subsequent run passed after the LP64 assertions were corrected.

The workflow now archives the complete client-input object plus its ELF and symbol reports so the next run preserves that evidence as a downloadable artifact.

## Explicit limits

This proves that the original client-input translation unit compiles for ARM64 and that the authentic command builder contains the Android touch hook. It does **not** prove that the client runtime is linked or invoked.

The CI markers remain:

- `IW3_CLIENT_INPUT_RUNTIME_LINKED=false`
- `IW3_CLIENT_RUNTIME_INVOKED=false`
- `IW3_PLAYABLE_APK=false`

No real map load, original renderer frame, physical ARM64 gameplay, weapon firing, or actor simulation has been demonstrated by this pass. The PR remains open and must not be merged as a playable release.
