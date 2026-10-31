# IW3 Android phase DS — original actor/model-pose portability

**Date:** 2026-10-30  
**Branch:** `feature/iw3-native-android-arm64-20261025`  
**PR:** #4

## Why this pass

The latest head (`c9901841b3aadcc02705b8281ebfc3e6b83bfc5f`) had a full ARM64 compile gate for the original client input and SP frame, but the original DObj pose/bounds translation unit used by rendered actors was not yet part of the Android compile graph. This pass adds the complete upstream `gfx_d3d/r_model_pose.cpp` to the NDK audit target and verifies its real exported symbols in an ELF64/AArch64 object.

## What changed

- Ported the scene-entity cull claim in the original `R_UpdateSceneEntBounds`: Android now uses a sequentially-consistent 32-bit atomic compare/exchange on the exact original `cull.state` field. Windows keeps the original `InterlockedCompareExchange` path.
- This is a real synchronization portability fix; it does not replace actor bounds/pose logic.

- Added the Android-only CMake OBJECT target `iw3_sp_renderer_model_pose_full_compile`.
- Compiles the original source with the authentic SP headers and Android ABI, without replacing pose logic.
- Added a CI inspection of ELF architecture and the original `R_DObjCalcPose` and `R_UpdateSceneEntBounds` symbols.
- Added a preflight regression that ensures this object stays outside the JNI diagnostic library.

## Exact limits

This is a source-portability gate only. It does not link the Direct3D 9 renderer, initialize DObj runtime services, load an XModel or BSP, or render an actor. The D3D9 GPU resource/swapchain backend remains the major rendering blocker. CI deliberately prints:

- `IW3_RENDERER_BACKEND_LINKED=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_RENDERER_FRAME_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

The PR must remain unmerged until an Android runtime loads licensed game data, renders a real map with the original engine pipeline and demonstrates touch-driven gameplay on ARM64.
