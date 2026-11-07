# Phase CN — compile the complete original filesystem translation unit

Date: 2026-10-29

## Baseline inspected

Branch: `feature/iw3-native-android-arm64-20261025`  
PR: #4  
Baseline head before this compile-gate change: `a2b54aa5f1857a6fd14b2f02bbfe98035f329c1f`

The latest ARM64 audit compiled selected authentic functions extracted from
`src/universal/com_files.cpp`, including `FS_RegisterDvars`,
`FS_Startup`, and `FS_InitFilesystem`. The audit report explicitly said
`filesystem_startup_invoked=false`; the JNI library did not contain the full
original translation unit. Selected slices could therefore pass even if
another part of the real filesystem source failed under the Android ABI.

## Implementation

Added an Android-only CMake object target
`iw3_sp_com_files_full_compile` that compiles the vendored original
`third_party/KisakCOD/src/universal/com_files.cpp` directly. It uses the real
SP headers, the Android platform compatibility headers, the native 64-bit ABI,
signed-char behavior, and strict floating-point flags.

This is a compile-only portability gate. The object is not linked into
`libiw3_sp_math.so`; unresolved engine services remain visible and no stubs
were introduced. It does not claim that `FS_Startup` has run or that a game is
playable.

Added `tests/test_iw3_android_full_com_files_compile_gate.py` to prevent the
target from silently reverting to extracted-function-only checks or being
mistaken for runtime integration.

## Validation

The new source and regression are pushed to the feature branch. Final validation
must come from Actions runs for the resulting branch head. Until the ARM64
compile step finishes, the full-TU compile is **pending**; previous passes of
selected function slices do not count as proof for this new target.

## Remaining gates

- Fix any actual portability compile errors reported by the new full-TU target.
- Integrate the canonical dvar registry, command registry, hunk/memory services,
  and platform file APIs so the original filesystem initializes without
  test-only state.
- Invoke `FS_Startup`/`FS_InitFilesystem` from the real Android engine
  bootstrap, then prove mounting of user-owned IWDs and loading of licensed
  FastFiles and a real map.
- Port and connect the original renderer, attach the touch adapter to the live
  client command/frame loop, and demonstrate gameplay on a physical ARM64
  device.

No diagnostic JNI package is a playable APK. PR #4 must remain open and
unmerged until all runtime gates are evidenced.
