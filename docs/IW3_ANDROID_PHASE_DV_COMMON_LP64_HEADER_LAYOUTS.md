# Android ARM64 pass DV — original bootstrap LP64 header layouts

Date: 2026-10-30

## Starting point and CI finding

Inspected the actual branch head `a25cf99083b8398f93be0a5212cc406d5ae8d059`, PR #4, the current native workflow and its failed Android NDK job before editing.

The latest full ARM64 source workflow was [run 41039245161](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41039245161). Preflight, host tests, and host ASan/UBSan completed successfully. The NDK failed while compiling the complete original `qcommon/common.cpp` bootstrap TU.

The first failure set contained:
- one Win32 scalar alias collision: `snd_public.h` declared `DWORD` as `unsigned long` (64-bit on Android LP64), while `threads.h` correctly declared it as `std::uint32_t`;
- seven original script VM runtime structures whose fixed-size assertions encoded 32-bit pointer layouts;
- eleven original FX runtime structures whose fixed-size assertions encoded 32-bit pointer layouts.

The compiler reported the actual AArch64-compatible sizes, including `function_stack_t=0x20`, `function_frame_t=0x28`, `scrVmPub_t=0x8540`, `MarkInfo=0x770`, `FxDrawState=0xC8`, and `FxBeamInfo=0x1508`.

## Changes

### Win32 scalar ABI compatibility in the shared sound header

In the Android/OpenAL fallback block of `sound/snd_public.h`:
- `LONG` now uses `std::int32_t`;
- `DWORD` and `UINT` use `std::uint32_t`;
- `WORD` uses `std::uint16_t`;
- `ULONG_PTR` uses `std::uintptr_t`.

Added Android compile-time checks that DWORD/LONG remain 32-bit and ULONG_PTR remains pointer-sized. This resolves the conflicting alias without changing the Windows SDK path.

### Original script VM runtime structures

Updated the seven pointer-bearing runtime layout assertions in `script/scr_vm.h` to select the original Win32 sizes for 32-bit builds and the NDK-observed LP64 sizes for 64-bit builds. No field order, pointer type, or script bytecode encoding was changed.

### Original FX runtime structures

Updated the eleven pointer-bearing runtime layout assertions in `EffectsCore/fx_system.h` for the two native pointer widths. The changes cover runtime mark collision state, mark contexts, FX draw state, beams and post-light state. They do not rewrite FastFile asset records or introduce serialized pointer values.

### Regression

Added `tests/test_iw3_android_common_lp64_header_layouts.py`. It requires each Win32 size to remain present alongside its explicit LP64 counterpart and checks the fixed-width Android scalar aliases.

## Validation status

The code changes are committed on `feature/iw3-native-android-arm64-20261025`. The workflow is triggered by the modified original source headers and the new test. A fresh CI result must be inspected before calling the full `common.cpp` ARM64 compile green.

The pre-existing run [41039245161](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41039245161) remains **FAIL** for the pre-change revision and is retained as the evidence that identified these errors. It is not evidence that this pass has passed.

## Boundary

This is header/ABI portability work only:
- `Com_Init/Com_Frame` is not yet linked into the Android game runtime;
- the script VM and FX runtime are not initialized in the app;
- no user-owned IWD/FastFile was mounted through the live engine;
- no BSP/map was loaded;
- no original renderer frame was presented;
- touch has not been proven to drive the live client frame loop;
- weapon fire, actor AI, damage/death and physical ARM64 gameplay are not proven;
- no playable APK exists.

The JNI diagnostic APK remains diagnostic only. PR #4 stays open and unmerged.
