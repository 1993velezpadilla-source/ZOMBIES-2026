# IW3 Android ARM64 — Phase EC: scr_anim_s 32-bit payload preservation

**Scope:** a narrow LP64 correctness fix in the authentic KisakCOD BGame header. This is not runtime integration and not a playable APK.

## Baseline inspection

The latest PR head before this pass was `1ac3c8cb25e42a575d6ddc1e1a3da7aa075f9405`. The original Android ARM64 workflow completed its full source audit successfully in [run 41085736292](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41085736292). While compiling the complete original `bg_weapons.cpp` and actor routines, Clang emitted:

`bg_local.h:227:23: warning: cast to 'const char *' from smaller integer type 'int' [-Wint-to-pointer-cast]`

The source was `linkPointer = (const char *)i; // KISAKHACK`.

`scr_anim_s` overlays two 16-bit fields with a pointer member. Its legacy integer constructor carries a 32-bit value, while the pointer-sized union member is 64 bits on Android ARM64. An implicit int-to-pointer conversion leaves the representation dependent on compiler ABI rules and triggers the warning in every translation unit including this header.

## Engine correction

The original constructor now explicitly converts the input through `std::uint32_t` and then `std::uintptr_t` before the pointer reinterpretation. This preserves the exact 32-bit payload and zero-extends it into the native pointer-width storage on LP64. The constructor signature and union layout are unchanged; no pointer is dereferenced by this conversion.

## Regression and CI

The new C++ fixture includes the actual `bgame/bg_local.h` and executes the original constructor with payloads `0`, `1`, `0x12345678`, `0x7fffffff`, `0x80000000`, and `0xffffffff`. It round-trips the stored value through `uintptr_t`, verifies zero-extension on 64-bit hosts, and never dereferences the encoded value.

The workflow runs the fixture on the host, compiles the same fixture for Android ARM64, verifies ELF64/AArch64, and uploads the object and logs as **NOT APK** evidence. Python preflight guards the exact source conversion and the runtime boundary markers.

Validation results are appended after the workflow for this commit completes.

## Explicit boundary

- This corrects the original BGame animation-handle representation; it does not link the BGame runtime into the Android Activity.
- Weapon definitions are still not loaded by the Android game runtime.
- No FastFile or BSP/map is loaded by the complete engine.
- No original renderer frame is demonstrated.
- The Android touch adapter is not yet proven to feed a running original client/frame loop.
- No Android ARM64 device gameplay is demonstrated.
- `IW3_PLAYABLE_APK=false` remains the required status.

PR #4 remains open and must not be merged until the full native bootstrap, assets, renderer, live input and gameplay gates pass.
