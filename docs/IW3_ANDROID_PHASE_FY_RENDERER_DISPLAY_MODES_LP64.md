# IW3 Android Phase FY — authentic D3D display-mode enumeration LP64 repair

Date: 2026-10-31. PR #4. Branch: `feature/iw3-native-android-arm64-20261025`.

## Baseline and verified defect

The previous FX renderer compile probe found that the genuine `gfx_d3d/r_init.cpp` still cannot compile as a full AArch64 unit because it uses Direct3D9, Win32, and x86-specific interfaces. In the same original renderer, `R_EnumDisplayModes` contained a separate LP64 defect: it read height and refresh-rate integers by indexing `dx.resolutionNameTable` with **negative indices** and casting the resulting pointers to `int`. The negative offsets happen to alias the preceding `displayModes[256]` memory on the original 32-bit layout. They do not identify the same fields when pointer widths change to 64 bits, and the access is out of bounds even on 32-bit.

## Source correction

Commit `955e4f50` modifies the **actual** `third_party/KisakCOD/src/gfx_d3d/r_init.cpp`:

- Uses `dx.displayModes[modeIndex].Height` and `.RefreshRate` directly rather than out-of-bounds pointer-table aliases.
- Removes the negative-index write that attempted to set a default refresh rate by corrupting the pointer table's preceding memory.
- Changes `R_AddValidResolution` to use actual `availableResolutions[index][column]` indexing rather than stepping beyond the first two-element subarray.

No substitute renderer, fake engine symbols, or Godot code was added. These changes preserve the original D3D9 enumeration flow on Windows while removing ABI-dependent aliases.

## Executable evidence

The regression `tests/test_iw3_android_renderer_display_modes_lp64.py` extracts the **five genuine renderer functions** (two comparators, resolution/rate accumulation, and full `R_EnumDisplayModes`) and compiles them on a 64-bit Linux host under AddressSanitizer and UndefinedBehaviorSanitizer. Only the D3D adapter enumeration and dvar registration are simulated **inside the test harness**; they are not used in production code.

The test checks sorting, resolution deduplication, refresh-rate deduplication, 256-mode capacity, the 257-entry null terminator, and rejection of an empty mode list. It also explicitly rejects reintroduction of negative pointer-table indexing.

CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41236165675

- Host job: **8/8 renderer regressions passed**, including `test_native_display_fields_and_full_enumeration_under_sanitizers`.
- Full original AArch64 `r_init.cpp` compile probe: **still fails** with `IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false (compiler_exit=1)`. The workflow is green because it is an evidence-gathering audit; it is not a successful renderer compilation.
- Remaining first compiler barriers include incomplete D3D9 interfaces (`IDirect3DSurface9`, `IDirect3DDevice9`, `IDirect3D9`), x86 `__rdtsc`, Win32 window/message functions, `Direct3DCreate9`, and D3D caps/types.

## Outstanding actual-game gates

`IW3_ORIGINAL_RENDERER_R_INIT_AARCH64_COMPILED=false`
`IW3_RENDERER_BACKEND_LINKED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_TOUCH_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

The next critical work is a real Android graphics backend and surface lifecycle preserving the original IW3 material/geometry/command systems, then integrated `Com_Init`, real map loading and gameplay evidence on ARM64. Host regressions and a diagnostic JNI APK cannot satisfy those gates. Keep PR #4 open; do not merge to main.
