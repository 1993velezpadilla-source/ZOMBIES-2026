# IW3 Android Phase BD - original FS_ReadFile integration audit

Date: 2026-10-28 (Puerto Rico)

## Implementation

The next unresolved startup edge was the original FS_ReadFile function. This pass stages the exact upstream bodies for FS_CheckFileSystemStarted, FS_FOpenFileRead, FS_ReadFile, FS_AllocMem, FS_FreeFile, FS_FreeMem, FS_ResetFiles, and FS_LoadStack from KisakCOD. No file-read algorithm or allocator was reimplemented.

The original shared state globals com_fileAccessed and fs_loadStack were moved from com_files.cpp into the existing engine-owned com_files_state.cpp, which is already part of the Windows and Android source lists. The public header already declares both as extern. This ensures the original open wrapper and read/free lifecycle use one state definition.

The AArch64 combined-link audit now includes the existing original FS_Read/FS_FCloseFile/FS_FOpenFileReadForThread archive plus the new FS_ReadFile archive and the rooted Android directory/ZIP service archive. It requires FS_ReadFile, FS_FOpenFileRead, FS_CheckFileSystemStarted, FS_AllocMem, FS_FreeFile, FS_FreeMem, FS_LoadStack, FS_ResetFiles, FS_Read, and FS_FCloseFile to be defined and not undefined.

The real Hunk allocator calls remain unresolved: Hunk_AllocateTempMemory and Hunk_FreeTempMemory. SEH_InitLanguage also remains unresolved. These are explicit next dependencies, not stubbed.

## Validation gates

The commit-triggered CI must pass source/provenance tests, host Release and ASan/UBSan tests, original ARM64 compilation, and the combined AArch64 link. The JNI and emulator workflows are separate diagnostics and are not evidence of FS_Startup execution.

## Hard boundary

This does not invoke FS_Startup or FS_InitFilesystem from Android, mount licensed game data, load FastFiles/maps, render a 3D scene, or execute player/weapon/actor gameplay. The JNI APK remains diagnostic. No playable APK is claimed; keep PR #4 open and unmerged.
