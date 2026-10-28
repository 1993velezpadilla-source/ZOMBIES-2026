# IW3 Android Phase BE — native-width Hunk temporary allocator

Date: 2026-10-27 (Puerto Rico)

## Source correction

The next dependency left by the original FS_ReadFile audit was Hunk_AllocateTempMemory / Hunk_FreeTempMemory. Inspection of the authentic vendored com_memory.cpp found a real LP64 defect: the page-boundary calculations cast addresses to uint32_t, and the legacy hunkHeader_t included a 32-bit padding word even though its name field becomes an eight-byte pointer on ARM64. That made the allocation header larger than the fixed 16-byte offset used by the original allocator.

This pass moves hunk_high, hunk_low, s_hunkData, s_origHunkData and s_hunkTotal to one engine-owned com_memory_state.cpp, included by the original common source list. It moves hunkUsed_t and hunkHeader_t to com_memory_state.h; the 32-bit dummy word exists only on 32-bit ABIs, and a static assertion keeps the allocator header at 16 bytes on both 32-bit and 64-bit builds. The original Hunk temp allocator's page-base calculations now use uintptr_t through Hunk_PageBase. The corrected allocator bodies are staged into an ARM64 static dependency-audit archive; memory-tracker, virtual commit/decommit and language-init services are not stubbed.

## Validation

Fresh source-preflight, host Release/ASan/UBSan and Android NDK ARM64 workflows are triggered by this update. Do not treat this phase as CI-green until those exact runs finish. The combined link gate will require Hunk_AllocateTempMemory and Hunk_FreeTempMemory to be defined; SEH_InitLanguage remains an explicit unresolved engine dependency. The allocator archive is an audit gate, not the runtime and not linked into the diagnostic APK.

## Hard boundary

This does not call FS_Startup or FS_InitFilesystem in the Android runtime, mount licensed FastFiles/maps, render an original 3D scene, or execute weapon/actor gameplay. No playable APK is claimed. PR #4 remains open and unmerged.


## Phase BE follow-up — correct the vendored Hunk allocator source itself (2026-10-28; CI pending)

A source-to-runtime audit found that the earlier Phase BE extraction had fixed only the staged temporary allocator slice. The vendored com_memory.cpp still contained 32-bit pointer masks in Hunk_ClearToMarkLow, Hunk_AllocAlign, Hunk_AllocateTempMemoryHigh, Hunk_ClearTempMemoryHigh, Hunk_AllocLowAlign, and Hunk_ClearTempMemory; the original HunkUser bodies also stored native pointers in int32_t locals/fields. Those defects would remain if the full original memory translation unit were used by a real runtime.

This follow-up fixes the original source, not only the generated audit copy:

- Page-boundary calculations use the shared Hunk_PageBase() helper, which masks uintptr_t addresses.
- Allocation alignment checks use native-width pointer values and page commit/decommit lengths use pointer differences.
- Hunk_AllocateTempMemoryHigh now returns uint8_t* rather than a 32-bit integer, with the public declaration updated to match.
- Original HunkUser allocation/reset state uses uintptr_t, and reset/decommit boundaries derive from the native user address and the actual offsetof(HunkUser, buf) layout.
- The Hunk temp audit generator now stages all affected original allocator bodies, and the HunkUser generator accepts already-corrected upstream bodies idempotently rather than applying the same transform twice.
- Regression tests inspect both the generated audit sources and the vendored original com_memory.cpp for the old pointer-truncating expressions.

Code changes: [77a2b3e](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/77a2b3e86d71894b0db1553bb4563eb37a61d871), [e3e4835](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/e3e483566b2aa7a356add849fee38151ef4f4bfd), [999345b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/999345bace4630044979f8f0fe4837b8fd97d3c9), [58747ef](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/58747ef0b3b1742da29fc3c3cbd08acb16708058), [60e8fb8](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/60e8fb8fcfc11f76c394990d647734f0824dd206), [219fcd9](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/219fcd9d9dc39c2f1ea5a87d1558abea8b1787a5), [4427e27](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4427e27553ce2a82120782823c5131b44befdd3a), [21d57b5](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/21d57b54c33ad9338f2f955738a703d2a4dc2976), [9c6124c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/9c6124c37a9bcbb57c2005387cc4197ab277bb37).

Validation for the new head is running in the native ARM64 source workflow, source preflight, JNI diagnostic build, and emulator diagnostic. Do not mark this follow-up green until the exact new-head runs complete. The Windows SP compile/runtime checks are also in progress and are important because the allocator signature changed while preserving the 32-bit ABI.

**Scope boundary:** this repairs the authentic allocator's native-width arithmetic but does not link the full memory/runtime service graph into the Android activity. FS_Startup()/FS_InitFilesystem() are still not invoked by the game runtime; no licensed FastFile/map, original renderer scene, or physical ARM64 gameplay is proven. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.


### Phase BE follow-up CI feedback (2026-10-28)

The first expanded archive build, native run [40659823034](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40659823034), correctly failed at compile time because the newly staged core allocator bodies needed declarations for the real engine services Sys_IsMainThread, Hunk_CheckTempMemoryClear, Hunk_CheckTempMemoryHighClear, and Hunk_ClearData. No fake implementations were added. The generator now emits declaration-only prototypes so those service edges remain unresolved in the audit object until their real providers are integrated.

On the follow-up code head [ffbffdf](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/ffbffdf68e3ce5135e118851679da6913f883d22), the source-preparation step and all Python regressions passed, and the host build/CTest step completed successfully. The full ARM64 sanitizer/NDK/link sequence is still running in [40659946153](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40659946153); JNI diagnostic packaging and emulator runs [40659946140](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40659946140) and [40659946128](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40659946128) are not yet green and are not counted as passed. The previous Windows SP runs were cancelled before full compile/runtime evidence, so they do not validate the changed high-temp allocator return type.
