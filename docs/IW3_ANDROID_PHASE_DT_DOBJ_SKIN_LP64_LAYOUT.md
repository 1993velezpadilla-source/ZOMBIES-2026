# IW3 Android pass DT — DObj skin surface LP64 layout

## Initial evidence

At commit `34235e81a498e779fc3601d4b2b589ba8cd39ce4`, GitHub Actions run [41027325204](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41027325204) failed while compiling the complete original `gfx_d3d/r_model_pose.cpp` translation unit with Android NDK 27.2.12479018.

Clang reported:
- `sizeof(GfxModelSkinnedSurface)`: actual LP64 size 40, assertion expected 24.
- `sizeof(GfxModelRigidSurface)`: actual LP64 size 72, assertion expected 56.

The source declarations contain native pointers (`XSurface*`, `GfxPackedVertex*`, and `DObjAnimMat*`). The old assertions represented the original Win32 layout and incorrectly rejected the natural 64-bit layout.

## Change

The original `r_dobj_skin.h` now explicitly records both layouts:
- `GfxModelSurfaceInfo`: Win32 12 bytes; LP64 16 bytes.
- `GfxModelSkinnedSurface`: Win32 24 bytes; LP64 40 bytes.
- `GfxModelRigidSurface`: Win32 56 bytes; LP64 72 bytes.

Conditional static assertions check both ABI widths at compile time. No fields were reordered, no pointers were narrowed, and no assertion was removed. These are in-memory renderer command/surface structures, not serialized asset records; the change does not claim that D3D9 rendering is ported.

The existing header-layout regression was extended from 11 to 14 explicit pointer-width assertions.

## Validation boundary

The source change addresses the exact compiler failure seen in run 41027325204. The new CI result must confirm that the full original model-pose translation unit now compiles for AArch64. This is still a compile-only gate: it does not link the renderer into the Android runtime, load a BSP, draw a frame, or prove actor animation/gameplay.

The JNI package remains diagnostic and must not be treated as a playable APK. PR #4 must remain unmerged until original filesystem/map loading, a real renderer frame, touch-to-client command consumption, and weapon/actor gameplay are demonstrated on ARM64.
