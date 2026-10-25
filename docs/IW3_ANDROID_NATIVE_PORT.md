# IW3 native Android port — engineering gates

**Objective:** actual **KisakCOD IW3 Single-Player C++ source** running on
Android ARM64, not a replacement Godot game, PC emulator, Android shell,
or CoD4 multiplayer/Steam. Base source:
`third_party/KisakCOD` (upstream `SwagSoftware/KisakCOD`).

## Proven baseline before this branch

Windows x86 native IW3-SP: C++ executable ran a real SP game frame,
spawned NPC actors, equipped an original registered weapon, and dispatched
`FireWeapon` and `Bullet_Fire`. These were direct runtime trace callbacks
in CI [40141908316](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40141908316).
No custom zombie level/gameplay, actual video render, impacts, or ARM64
were confirmed by that test.

## Evidence gates (strict)

| Gate | Status | Proof required |
| --- | --- | --- |
| 0. Real Windows IW3 SP runs and fires | PASS | Native executable traces from 40141908316 |
| A. Genuine IW3 SP C++ on Android ABI | **PASS — [run 40154663973](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40154663973)** | NDK builds ELF64 AArch64 .so directly from vendored `com_math_anglevectors.cpp` (only include shim); same source executes mathematically correct host smoke |
| B. Android entry point / lifecycle | OPEN | JNI/NativeActivity loads engine subsystem and handles native Android input; instrumentation proves actual source callbacks, not mocked |
| C. IW3-SP systems in Android process | OPEN | Serverless original SP actor, weapon, frame update functions execute on ARM64, no Steam |
| D. Portable renderer | OPEN | Direct3D9-specific `gfx_d3d` dependencies replaced by original-engine-adapted GLES/Vulkan backend; draws a correct frame |
| E. Original playable level / touch | OPEN | Licensed/original map loads on device; touch movement, ADS, attack, hit, damage, rounds verified |
| F. First **IW3 engine** Android APK | OPEN | Full Android app actually runs integrated IW3 engine (not Godot) on a physical Android device |

**Do not call Gate A a playable Android IW3 port.** It links only
original IW3 aim/orientation calculations as the first transplanted
translation unit. Other gates remain unproven.

## Why an Android APK cannot be built by simply switching CMake targets

KisakCOD root CMake explicitly sets `KISAK_PLATFORM win32` and the SP
CMake target lists `GFX_D3D`, `WIN32_SRC`, `MSSLIB` and `STEAM_HEADERS`.
`src/win32/win_main.cpp` includes `<Windows.h>`, Windows window/message
APIs and `gfx_d3d/r_init.h`. The codebase was authored for 32-bit MSVC
and DirectX9 and relies on Windows runtime DLLs for Miles/Bink/Steam.
An Android NDK compiler cannot link these libraries or D3D9 into a
native ARM64 game. Source-level platform, renderer, audio, ABI, input and
asset-loader work is required.

Changing Steam startup behavior on Windows is **not** a platform port.

## First verified source-level action

`tools/iw3_android/prepare_real_engine_math.py` takes the **unchanged**
original `src/universal/com_math_anglevectors.cpp` and swaps *only*
its Win32-heavy include headers in a temporary build copy. All original
function bodies (AngleVectors, AnglesToAxis, Vec4Normalize, AnglesToQuat,
Com_SurfaceTypeFromName and Com_SurfaceTypeToName) and the original
60-entry IW3 surface/material table stay exactly as-is. `android/iw3-native/native_math_abi.cpp` provides
a tiny exported C ABI that calls the original `AngleVectors()` and
checks original angles/basis conventions and real IW3 surface class names
(including the engine's original foliage/foilage alias). Unused `AnglesToQuat`
and its `AxisToQuat` dependency are discarded at link time; no stub of
the engine function is used.

The CI **passed** real binary host smoke **and** a NDK cross-compile
in [run 40154663973](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40154663973),
validates AArch64 ELF64 with `llvm-readelf` and publishes only
`libiw3_sp_math.so` with source hashes and symbol evidence.
The binary is `libiw3_sp_math.so` (with math and surface C++ logic).
A shared engine-component library is **NOT an APK**, nor proof of an
entire Android gameplay runtime.

No game archive, assets, data files, proprietary maps or models are
required or redistributed for Gate A. Godot and the earlier misleading
APK are not built or used by this branch.

## Next implementation priorities

Android-native platform services (window lifecycle, monotonic clock,
threads, filesystem, usercmd input); removal of Direct3D and
Windows-only import assumptions; decoder/data-loading and render
backend; then remaining SP gameplay core and final on-device APK.
Each gate must compile, run, and report native code evidence. Never
replace the IW3 engine with a different engine while reporting progress.
