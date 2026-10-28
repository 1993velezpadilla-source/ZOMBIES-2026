# IW3 Android Phase BE — native-width Hunk temporary allocator

Date: 2026-10-27 (Puerto Rico)

## Source correction

The next dependency left by the original FS_ReadFile audit was Hunk_AllocateTempMemory / Hunk_FreeTempMemory. Inspection of the authentic vendored com_memory.cpp found a real LP64 defect: the page-boundary calculations cast addresses to uint32_t, and the legacy hunkHeader_t included a 32-bit padding word even though its name field becomes an eight-byte pointer on ARM64. That made the allocation header larger than the fixed 16-byte offset used by the original allocator.

This pass moves hunk_high, hunk_low, s_hunkData, s_origHunkData and s_hunkTotal to one engine-owned com_memory_state.cpp, included by the original common source list. It moves hunkUsed_t and hunkHeader_t to com_memory_state.h; the 32-bit dummy word exists only on 32-bit ABIs, and a static assertion keeps the allocator header at 16 bytes on both 32-bit and 64-bit builds. The original Hunk temp allocator's page-base calculations now use uintptr_t through Hunk_PageBase. The corrected allocator bodies are staged into an ARM64 static dependency-audit archive; memory-tracker, virtual commit/decommit and language-init services are not stubbed.

## Validation

Fresh source-preflight, host Release/ASan/UBSan and Android NDK ARM64 workflows are triggered by this update. Do not treat this phase as CI-green until those exact runs finish. The combined link gate will require Hunk_AllocateTempMemory and Hunk_FreeTempMemory to be defined; SEH_InitLanguage remains an explicit unresolved engine dependency. The allocator archive is an audit gate, not the runtime and not linked into the diagnostic APK.

## Hard boundary

This does not call FS_Startup or FS_InitFilesystem in the Android runtime, mount licensed FastFiles/maps, render an original 3D scene, or execute weapon/actor gameplay. No playable APK is claimed. PR #4 remains open and unmerged.
