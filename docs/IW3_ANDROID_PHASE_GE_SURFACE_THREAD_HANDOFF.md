# IW3 Android phase GE — real Surface capture / original renderer thread handoff

Date: 2026-10-31 (Puerto Rico). PR #4, branch `feature/iw3-native-android-arm64-20261025`. **IW3_PLAYABLE_APK=false.**

## Baseline inspected

At `6cd52bef`, the genuine renderer's `r_init.cpp` failed its AArch64 compile probe. The 2026-11-01 UTC CI run 41257944237 reported `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`, with the first errors including an incomplete `IDirect3DSurface9` in `r_utils.h`, x86-only `__rdtsc`, and Win32 `GetActiveWindow` / `MessageBoxA`. A successful CI wrapper and separately compiled JNI provider **do not** mean a renderer exists.

The phase-GD Android provider called `R_BuildDisplayModeDvars()` immediately after reading `ANativeWindow` and `Display.getRefreshRate()` through JNI. If integrated directly into an Activity Surface callback, this would mutate the original `dx` and dvar renderer globals from the Android UI thread, racing the engine's renderer initialization thread. It also gave no value-only way to hand surface data to the engine.

## Changes in authentic KisakCOD source

- `R_AndroidReadSurfaceMode(JNIEnv*, jobject, jobject, IW3AndroidSurfaceMode*)`: captures real surface width/height and current OS refresh into a plain 3-field struct. It performs no `dx` or dvar writes, owns no references beyond the call, rejects pre-existing JNI exceptions and invalid data, and leaves the output untouched on failure.
- `R_AndroidApplySurfaceMode(const IW3AndroidSurfaceMode&)`: validates the value-only snapshot, populates the **original** `dx.displayModes` and calls the **original** `R_BuildDisplayModeDvars()`. Its contract explicitly requires the original renderer initialization thread.
- `R_AndroidPopulateDisplayMode` remains for same-thread initialization only, composing the above functions; Android Activity lifecycle callbacks must **not** call it directly.
- Updated the LP64 host sanitizer regression to execute all three unchanged authentic source functions. It checks that JNI capture does not mutate renderer globals, that apply changes them, that invalid modes are rejected without changing state, that pre-existing JNI exceptions are rejected, and that failed reads do not overwrite output.
- Updated the Android NDK workflow to require all three symbols in the AArch64 object, not merely a successful host-only test.

This removes a concrete thread-ownership hazard from the eventual native renderer integration. It does not supply an EGL/Vulkan backend, D3D9 compatibility layer, renderer thread, or runnable game.

## Verification and limits

Baseline renderer CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41257944237 (completed, audit success, **full original renderer compile failed**).

Verified at commit `fdf95b623b5957d5cb2190b87e2d23e8b06d377c`: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41264838509 completed **success** on 2026-11-01 UTC. The host job ran **9/9 tests successfully** under the renderer sanitizer harness, including the unchanged genuine capture/apply/wrapper functions. The Android NDK job compiled the authentic Surface provider to an AArch64 object and verified all three exported symbols (`IW3_ORIGINAL_ANDROID_SURFACE_CAPTURE_AND_APPLY_AARCH64_COMPILED=true`). In that same run, the **full original `r_init.cpp` compile still failed** (`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`). A green audit wrapper and an AArch64 object are **not** a linked renderer, frame, or playable APK.

## Remaining gates

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false` (until independently proven otherwise).
`IW3_RENDERER_BACKEND_LINKED=false`.
`IW3_RENDERER_FRAME_PROVEN=false`.
`IW3_REAL_MAP_LOADED=false`.
`IW3_GAMEPLAY_PROVEN=false`.
`IW3_PLAYABLE_APK=false`.

Next: implement a real graphics backend and renderer-thread lifecycle that consumes this captured mode while preserving the authentic IW3 geometry, materials, textures, draw submission and client frame loop. Then prove actual maps, touch commands, weapons and actors on Android ARM64. Do not merge PR #4 while incomplete.
