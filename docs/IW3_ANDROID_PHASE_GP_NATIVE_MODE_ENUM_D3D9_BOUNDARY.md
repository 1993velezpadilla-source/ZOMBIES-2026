# IW3 Android ARM64 — phase GP: native Surface mode / D3D9 boundary

Date: 2026-11-01. Branch: `feature/iw3-native-android-arm64-20261025`. PR #4. Engine: original KisakCOD IW3 only. No Godot, replacement engine, or merge to main.

## Source change

The genuine `third_party/KisakCOD/src/gfx_d3d/r_init.cpp` now keeps Windows D3D9 adapter enumeration in the desktop branch of `R_EnumDisplayModes`. Android checks the existing original `dx.displayModes` and renderer dvars supplied by `R_AndroidApplySurfaceMode` on the renderer thread, without calling `IDirect3D9::GetAdapterModeCount` or `EnumAdapterModes`. Missing/invalid Surface state fails closed. The original Android mode provider already builds/registers the dvars; `R_EnumDisplayModes` does not register them a second time.

The original `R_PreCreateWindow` now rejects the unsupported desktop D3D9 startup path on Android (return 0, explanatory renderer log) rather than pretending that an EGL context is an integrated IW3 GLES renderer. Windows D3D9 behavior remains in the original desktop conditional.

Source commits: `809ffdf8`, `28c7403e`. Regression commits: `57e086a3`, `66138bec`, `9d71f5d2`, `8389deb1`, `1090bf2d`.

## Verification

- [GitHub Actions renderer run 41303392505](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41303392505): both jobs completed successfully on `1090bf2d3a82e04b92c93f24a8198b71049f1d83`.
- Host original-renderer regression suite: **13/13 passed** under AddressSanitizer/UndefinedBehaviorSanitizer. The updated original display-mode harness executes Android and desktop paths, checks no duplicate Android dvar registration, rejects missing native modes, and executes the genuine `R_PreCreateWindow` Android fail-closed branch.
- Android NDK: original Android Surface capture/apply provider compiled for AArch64; Android EGL3 platform context provider linked for ARM64. **Neither proves IW3 rendering.**
- AArch64 compile probe of the full authentic `r_init.cpp`: **`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`**. The first prior errors in `R_EnumDisplayModes` / `R_PreCreateWindow` (D3D9 adapter enumeration, `Direct3DCreate9`) are absent from the first diagnostic block. New first diagnostics start at `R_CheckDxCaps` (`_D3DDEVTYPE`, incomplete `_D3DCAPS9`), followed by D3D9 device-format checks. The probe job intentionally succeeds as an audit even when the original TU fails compilation.

## Remaining acceptance gates

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`
`IW3_RENDERER_BACKEND_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

No authentic ARM64 playable APK and no device evidence of a real map, touch input, weapons, or actors. A JNI diagnostic APK is **not** a playable build.

## Next blocker

Continue isolating desktop-only `_D3DCAPS9`/device-format capability paths from Android, without fake capability success; integrate genuine GLES material, geometry, and draw-command execution into the original renderer and verify on a real device before changing any playable gate.
