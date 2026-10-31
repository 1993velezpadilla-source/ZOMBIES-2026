# Android ARM64 pass DW — complete common.cpp portability blockers

Date: 2026-10-30

## Starting point

Inspected PR #4 at `b95e90dae9cc04d4dd00f6b48ec11101b4358689`, the current native workflow, and the latest ARM64 run [41051209605](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41051209605).

The native host tests and sanitizer step passed. The NDK stopped while compiling the complete original `qcommon/common.cpp` object. The actionable errors were:

- `scrAnimPub_t` and `scrAnimGlob_t` retained Win32-only pointer-layout sizes;
- the SP demo declarations used MSVC's `_iobuf` tag, while Bionic exposes `FILE`;
- original common code used MSVC CRT names `_vsnprintf`, `_time64`, and `_localtime64`;
- the prefetch path referenced the Windows intrinsic constant `PF_NON_TEMPORAL_LEVEL_ALL`;
- the engine build banner referenced `CPUSTRING`, which is only defined by the Win32 platform branch.

## Changes in the original engine source

### Runtime animation-tree layouts

Updated the two pointer-bearing runtime layout assertions in `script/scr_animtree.h`:

- `scrAnimPub_t`: Win32 `0x41C`, LP64 `0x820`. The `xanim_lookup[2][128]` table contains native `scr_animtree_t` handles.
- `scrAnimGlob_t`: Win32 `0x20C`, LP64 `0x218`. The `start` and `pos` members are native pointers.

The fields and order are unchanged. These are live runtime globals, not serialized FastFile records.

### Bionic stdio ABI for original SP demo declarations

On Android, `server.h` now aliases `_iobuf` to Bionic's `FILE` after including `<stdio.h>`. This matches the existing `FILE *` history globals in the original `sv_demo.cpp`; it does not alias the engine's separate `iobuf` filesystem wrapper and adds no implementation.

### Common C runtime and cache prefetch

The original `common.cpp` keeps the MSVC paths on Windows and selects native Android services only under `__ANDROID__`:

- `_vsnprintf` call sites map to Bionic `vsnprintf`; their return values are not used, and the original code already explicitly terminates the destination buffers.
- `Com_OpenLogFile` uses native 64-bit `time_t`, `time()`, and `localtime()` on Android; Windows retains `_time64/_localtime64`.
- `Com_Prefetch` uses Clang/GCC `__builtin_prefetch(s, 0, 0)` on Android ARM64; Windows retains its existing intrinsic/assembly paths.
- The build banner gets an architecture-specific Android `CPUSTRING` without changing the Windows definition.

## Regression coverage

Extended:

- `tests/test_iw3_android_common_full_compile.py` to guard the Bionic CRT, time, prefetch, CPU banner and `FILE` alias boundaries;
- `tests/test_iw3_android_common_lp64_header_layouts.py` to check both Win32 and LP64 animation-tree runtime layouts.

## Verification

The source changes trigger the complete native workflow again. The previous run [41051209605](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41051209605) remains a **failed pre-fix run**, not a passing result.

The follow-up run must confirm the complete original `common.cpp` object compiles for `arm64-v8a`. Any newly exposed compiler errors remain open work; no success is inferred from this source change or from the JNI diagnostic build.

## Boundary

This pass does not link `Com_Init/Com_Frame` into the Android runtime. It does not mount owner-supplied IWD/FastFiles through the live engine, load a BSP, present an original renderer frame, connect touch to the running client command loop, or demonstrate weapon/actor gameplay on physical ARM64 hardware.

The JNI APK remains diagnostic only. PR #4 must remain open and unmerged.

## Preflight follow-up

The first post-change preflight [41052809698](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41052809698) stopped before NDK compilation because the new regression checks encoded literal backslash-n sequences and placed animation-tree layouts in the script-VM header test. The engine changes were not reached by that run.

Corrected the tests to assert the Android CRT and stdio declarations independently, and moved `scrAnimPub_t`/`scrAnimGlob_t` layout checks into a dedicated test that reads `script/scr_animtree.h`. This is a test-harness correction only; it does not alter the engine implementation. A fresh CI run is required before treating the pass as green.

A second preflight attempt [41052971190](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41052971190) reduced the suite to one remaining matcher error: the original declaration is spelled `_iobuf *__cdecl SV_DemoOpenFile`, not `_iobuf *SV_DemoOpenFile`. Updated the regression to match the exact upstream calling-convention declaration. No engine source changed in this follow-up; the latest full ARM64 run must still complete before this phase can be marked green.

## Additional NDK errors exposed after the preflight fix

The next full compile [41053087448](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41053087448) passed the corrected 376-test preflight and host ASan/UBSan, then advanced the complete original `common.cpp` compile to two remaining errors:

- `_snprintf` was another MSVC-only bounded formatting name. Android now maps it to Bionic `snprintf`; the original call explicitly terminates `buffer[maxlen - 1]`.
- `Com_CheckError` cast the `Sys_GetValue(2)` jump-buffer pointer to `int *`. Bionic's `jmp_buf` has a different native representation. The original routine now uses the same `jmp_buf *` + `longjmp(*value, -1)` form already used by other `common.cpp` call sites.

Regression coverage now checks the `_snprintf` mapping and requires the typed jump-buffer call. A fresh full ARM64 workflow must confirm this correction; run 41053087448 remains a failed pre-fix compile, not a pass.

## Final validation on the corrected source revision

The complete native Android source workflow [41053424641](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41053424641) completed **SUCCESS** on source revision `c450b7e2e0ed6a6386607c8e53a3798f95185a72`.

Verified results:

- Source preflight: **376 Python tests passed**.
- Host CTest: **25/25 passed**.
- Host AddressSanitizer + UndefinedBehaviorSanitizer CTest: **25/25 passed**, with leak detection enabled.
- Original KisakCOD common/bootstrap translation unit `common.cpp`: **ELF64/AArch64 object compile PASS**, marker `IW3_ORIGINAL_COMMON_BOOTSTRAP_AARCH64_OBJECT_PASS`.
- Original complete `G_RunFrame` frame archive: **PASS** with authentic SP state headers; archive SHA-256 `d05b274b62f20f16554d83f266b0d3921dac3dbfe141991dd51106b968e0abed`.
- Original client input/touch hook, client movement helpers, aim-assist/melee providers, FastFile loader, DB registry, IWD indexer, filtered file list, actor pointer-width routines, mover/trace chain and BGame weapon loader: all their AArch64 compile/link audit steps passed in this run.
- The original frame's dependency report still lists unported runtime services: `G_UpdatePlayer`, `G_UpdatePlayerTriggers`, `G_RunFrameForEntity`, `Scr_RunCurrentThreads`, `Scr_IncTime`, `ClientEndFrame`, `G_UpdateActorCorpses`, `Actor_DumpEventListners`, and `Path_RunBadPlaces`.

The separate JNI integration [41053424705](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41053424705) also passed packaging/signature validation. Its artifact [12976116291](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41053424705/artifacts/12976116291) is explicitly **`NOT-A-GAME`** and is not a playable engine package.

## Remaining hard gates

This successful source build is still not a game runtime:

- `IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`
- `IW3_CLIENT_INPUT_RUNTIME_LINKED=false`
- `IW3_RENDERER_BACKEND_LINKED=false`
- `IW3_RENDERER_FRAME_PROVEN=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`

The original D3D9 renderer is still not backed by a native Android graphics implementation. The Android process has not yet linked and invoked the full original bootstrap, database/filesystem service graph, client frame and SP frame together. No owner-supplied IWD/FastFile has been mounted by that complete runtime, no BSP scene has been presented, and no physical ARM64 device has demonstrated touch-driven weapon/actor gameplay.

**Conclusion:** the compile/ABI blockers in this pass are fixed and verified; the next engineering gate is actual runtime linkage and a real Android renderer/map frame, not another diagnostic APK. PR #4 remains open and unmerged.
