# IW3 Android phase GB — original renderer display-table capacity guards

Date: 2026-10-31. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Original source change (not a replacement renderer)

In `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`, the original `R_AddValidResolution` and `R_AddValidRefreshRate` functions now stop appending once their caller-owned fixed tables are full. The resolution table has 256 pairs; the refresh table has 257 integers. Previously, direct calls with `resolutionCount == 256` or `rateCount == 257` could write one past the respective arrays. The fix preserves the original insertion and sorting behavior while making the helper functions independently bounds-safe. `R_AddValidRefreshRate` also asserts a nonnegative count.

## Executable regression

Extended `tests/test_iw3_android_renderer_display_modes_lp64.py` to extract and execute the authentic renderer functions with ASan/UBSan. It tests insertion into the last valid resolution and refresh-rate slots, then calls each helper with an already-full table and checks that it returns the unchanged count. The existing mode enumeration and comparator tests remain. This does **not** exercise Direct3D or Android GPU rendering.

Source commit: `705803e7702398a6da5370ae470c69c41d4b7af3`. Test commit: `9f1f985456470ad882d2d1ef9ed214fccc89ae3f`.

## Real blocker and honest status

The latest inspected renderer compile probe for prior head `4a880cf271d9175712677b6e44a3a91f28302fcd`, [GitHub Actions run 41247388711](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41247388711), reports `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`. Its compiler diagnostics identify incomplete D3D9 COM interfaces (`IDirect3DSurface9`, `IDirect3DDevice9`, `IDirect3D9`), Windows API calls, and x86 `__rdtsc`. The workflow's green status indicates successful **audit**, not successful renderer compilation. This table-capacity fix does not address the backend gap. A genuine Android renderer must connect the original material/geometry/scene pipeline to a supported Android graphics API, not replace IW3 with Godot or a diagnostic stub.

`IW3_PLAYABLE_APK=false`. No verified original-renderer frame, real map load, or ARM64 gameplay with touch, weapons and actors. Keep PR #4 open and unmerged. CI result for this new commit should be appended after it completes.
