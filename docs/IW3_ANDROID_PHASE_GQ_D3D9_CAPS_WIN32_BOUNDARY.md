# IW3 Android ARM64 — Phase GQ: isolate D3D9 capability and Win32 startup chain

Date: 2026-11-01. Original KisakCOD IW3 source only. PR #4, branch `feature/iw3-native-android-arm64-20261025`. No Godot, replacement engine, or merge to main.

## Verified baseline and blocker

[Prior full renderer compile probe 41303501713](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41303501713) returned `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false (compiler_exit=1)`. First errors in genuine `gfx_d3d/r_init.cpp` were `_D3DDEVTYPE` and incomplete `_D3DCAPS9` in `R_CheckDxCaps`, followed by `R_PickRenderer` and `IDirect3D9::CheckDeviceFormat`. These are genuine D3D9 COM capabilities, **not** GLES capabilities.

## Implementation

- In `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`, the original D3D9 `R_CheckDxCaps` capability bitfield checker is compiled only for non-Android platforms. The platform-neutral `R_DescribeRenderer` remains outside the guard.
- The contiguous original Windows-specific capability selection, D3D9 adapter enumeration, Win32 monitor/window creation, and splash-window startup functions are compiled only for non-Android. The original `R_LoadGraphicsAssets` stays outside the guard.
- No fake `_D3DCAPS9`, dummy GPU capabilities, fake renderer success, or no-op draw calls were added. Android `R_PreCreateWindow` continues to **return failure** while authentic GLES draw-command execution is unavailable. Desktop source bodies remain unchanged.
- Added `tests/test_iw3_android_renderer_d3d_caps_boundary.py`: preprocesses the **actual source region** for Android and desktop, checks that D3D9/Win32 symbols are excluded only on Android, and checks platform-neutral renderer and asset loader code survives. Added its path to the renderer workflow trigger.

Implementation commit `73b7b15f`; regression `1a03bc75` (refinement `6a0929dd`); workflow trigger `b79315f9`.

## Verification and limitations

Latest [renderer workflow 41311397560](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41311397560) is the required verification target for the final source/test revision. **Do not interpret a green workflow as a playable APK**: its compile-probe job intentionally exits successfully even when the authentic renderer TU fails. Inspect the explicit `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED` flag and the actual compiler diagnostics.

The EGL platform provider only manages an Android graphics context; it does not execute original IW3 materials, geometry, textures, shaders, or draw commands.

Acceptance gates remain unproven: `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` until a passing compile probe demonstrates otherwise; `IW3_RENDERER_BACKEND_LINKED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**. No real Android scene/map/weapon/actor gameplay evidence.

## Next engineering step

Inspect the new first compiler errors, continue separating D3D9-only device initialization from portable IW3 state, then implement a **real** GLES3 renderer command backend: original IW3 draw-surface/material dispatch, shader translation, texture and buffer binding, actual `glDrawElements` calls, and GLES GPU synchronization. Only mark renderer, map, and gameplay gates true with device-side proof.
