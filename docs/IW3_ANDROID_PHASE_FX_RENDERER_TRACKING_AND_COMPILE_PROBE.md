# IW3 Android Phase FX — authentic renderer LP64 tracking and first AArch64 renderer compile probe

Date: 2026-10-31. Branch: `feature/iw3-native-android-arm64-20261025`.
PR: https://github.com/1993velezpadilla-source/ZOMBIES-2026/pull/4

## Baseline and actual next blocker

At `686e4ffc`, the complete original `client/cl_main.cpp` and `qcommon/common.cpp` compiled and linked **relocatably** for AArch64. The client entry `CL_InitRenderer` is defined, but its authentic renderer dependency `R_BeginRegistration(vidConfig_t*)` remains unresolved in that partial link. This does **not** demonstrate Android renderer operation.

The genuine definition of `R_BeginRegistration` is in `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`. It calls `R_Init`, which calls `R_InitGraphicsApi` and requires the original Direct3D 9 device/backend. Merely adding the symbol to an object link would not create a usable Android graphics backend. Android needs a real surface and a working translation of the original renderer's device, materials, shaders, textures, draw commands and frame submission; no stub can count as a rendered scene.

## Source correction (real engine)

`gfx_d3d/r_init.cpp::TRACK_r_init` used Windows/32-bit literal static allocation sizes for `rgp` (8576), `rg` (33552) and `vidConfig` (48), while already using `sizeof(dx)` for the fourth entry. All four now use the native `sizeof` of the actual original engine globals, preserving the four names, addresses, memory category 18 and order. This prevents invalid memory-accounting sizes on LP64 and retains the original 32-bit behavior when structure sizes match.

## Executable regression

`tests/test_iw3_android_renderer_static_tracking.py` extracts the genuine `TRACK_r_init` function and executes it on a 64-bit host with AddressSanitizer and UndefinedBehaviorSanitizer, checking the four native allocation sizes and identities. The test-only structures are **not** a graphics backend. A standalone local reproduction of the extracted function's current body passed with g++ ASan/UBSan and marker `IW3_ORIGINAL_RENDERER_STATIC_TRACKING_LP64_PASS`; this local reproduction is supplemental, not CI evidence.

`.github/workflows/iw3-renderer-init-arm64.yml` runs the original-function regression and attempts a full Android NDK AArch64 compile of **the actual** `gfx_d3d/r_init.cpp`, with the same pinned NDK 27.2 and include flags used by the full-client audit. It captures the first compiler diagnostics and explicitly records `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` if blocked. The probe job can succeed as an **audit** even when compilation fails; the marker, not the job color, is the compiler result. The probe does not provide substitute renderer symbols or link fake implementations.

## Evidence and remaining gates

Source commit `54055faa`; host regression `f70a1db0`; workflow `b3fff8fe`; workflow discovery fix `f994eecc`.

The new CI runs were still executing when this record was created. Consult the latest `IW3 authentic renderer LP64 tracking and AArch64 compile probe (NOT GAME)` workflow logs and uploaded `iw3-renderer-compile-report.txt` for the actual AArch64 compiler outcome before claiming that translation unit compiles.

Remaining: resolve real Android renderer compile barriers; implement genuine graphics backend and native surface; execute `Com_Init`/renderer startup in a loadable ARM64 process; load original map/weapon data; verify live touch input and gameplay on a real ARM64 Android device with logcat and frames.

`IW3_ORIGINAL_RENDERER_BACKEND_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

No Godot, replacement engine, JNI diagnostic success claim, or merge to main.
