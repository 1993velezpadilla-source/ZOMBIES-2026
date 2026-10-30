# IW3 Android Phase EA — original script VM LP64 bookkeeping

Date: 2026-10-30

## Scope

This pass fixes a real 64-bit layout assertion and allocation-tracking bug in the authentic KisakCOD IW3 SP script runtime, then adds a compile gate for the complete original `script/scr_vm.cpp` translation unit.

## Changes

- `scr_main.h`: `scrVarPub_t` is live runtime bookkeeping containing native pointers, not a serialized asset. Its Win32 size remains `0x2007C`; the LP64 layout is asserted as `0x200A0`.
- `scr_vm.cpp`: `TRACK_scr_vm()` now reports `sizeof(scrVmGlob)`, `sizeof(scrVmPub)`, `sizeof(g_script_error)`, and `sizeof(scrVmDebugPub)` instead of hard-coded Win32 byte counts. This prevents static allocation accounting from under-reporting pointer-bearing VM state on Android.
- `script_parser_layout_native_test.cpp`: the NDK fixture asserts the LP64 sizes and key offsets of `scrVarPub_t`, `scrVmGlob_t`, `scrVmPub_t`, and `scrVmDebugPub_t` in addition to the parser layouts.
- `android/iw3-native/CMakeLists.txt`: `iw3_sp_script_vm_full_compile` compiles the full original `scr_vm.cpp` as an Android ARM64 OBJECT target. It is not linked into JNI.

## Validation boundary

The CI build must confirm the asserted LP64 layout and compile the complete original VM translation unit. The object is a portability artifact only. It does not prove that `Scr_RunCurrentThreads()` or `Scr_IncTime()` are invoked by an Android frame.

`IW3_CLIENT_RUNTIME_LINKED=false`

`IW3_FS_STARTUP_RUNTIME_INVOKED=false`

`IW3_REAL_MAP_LOADED=false`

`IW3_GAMEPLAY_PROVEN=false`

`IW3_PLAYABLE_APK=false`

PR #4 must remain open and unmerged until native bootstrap, real filesystem/FastFile/map loading, a real renderer frame, live touch-to-command flow, and ARM64 gameplay with weapons/actors are observed.
