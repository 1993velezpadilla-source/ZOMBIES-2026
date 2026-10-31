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

## Follow-up correction: real renderer mode-text bounds and cinematic compile isolation

The first full `r_init.cpp` AArch64 probe at https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41230860366 found the first concrete Android header barrier: original `gfx_d3d/r_cinematic.h` unconditionally includes Windows `d3d9.h`. The original renderer initializer only calls four cinematic functions and does not use Bink structures. The Android path now includes a **declarations-only** compatibility header with the original four external function signatures; Windows retains its original header and behavior. No cinematic implementation or fake backend was added. Commits: `dc71f26b`, `7e204f59`.

The next AArch64 probe exposed two undeclared `ARRAYSIZE(dx.modeText)` uses in `R_EnumDisplayModes`. More importantly, the old code passed the **entire 5,120-byte buffer size** to `snprintf` after advancing its output pointer, and the refresh loop subtracted only the previous string length rather than total bytes used. This could write beyond `dx.modeText`. The genuine renderer now computes remaining capacity from the current pointer for **every** resolution and refresh-rate string, checks the `snprintf` return against that remaining capacity, and fails initialization on truncation instead of advancing past the end. Engine commit: `0e72dfbc`. The exact original formatting blocks are executed under ASan/UBSan for 256 ordinary resolutions and 256 deliberately oversized resolutions. Test commit: `5aee849f`; workflow update: `267b4b09`.

**Verified at workflow https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41231158360:** the host sanitizer job passed **7/7 tests**, including the new original renderer tracking and mode-text regressions. The AArch64 compile-probe job completed its evidence capture and explicitly reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false (compiler_exit=1)`. Its first remaining compiler diagnostics are genuine Windows/Direct3D API dependencies: incomplete `IDirect3DSurface9` in `r_utils.h`, x86-only `__rdtsc`, Win32 window/message APIs, and incomplete `IDirect3DDevice9`/`IDirect3D9` types, constants and `Direct3DCreate9`. The earlier `d3d9.h` fatal include and both `ARRAYSIZE` errors are absent from this latest probe.

The audit workflow's green result means the diagnostic procedure ran successfully, **not** that the renderer compiled. No renderer object, executable Android engine, rendered frame, map or gameplay was demonstrated. The full graphics backend and window/surface adaptation remain the dominant blocker.

Do not equate this source progress with a playable APK. Keep PR #4 open and unmerged.
