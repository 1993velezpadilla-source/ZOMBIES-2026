# IW3 Android Phase BC - combine authentic IWD directory services

Date: 2026-10-27 (Puerto Rico)

## Concrete change

The prior ARM64 audit linked the original FS startup + Dvar + ZIP/IWD mount/parser archives, but left the directory boundary visible even though the Android rooted directory adapter already existed in the diagnostic library. This pass adds a separate static audit target containing:

- Verbatim upstream helper bodies I_strncmp, FS_PathCmp, and iwdsort, extracted from KisakCOD.
- The existing Android rooted Sys_ListFiles / FS_FreeFileList adapter and platform enumeration provider.
- The original FS startup archive remains the sole owner of FS_AddIwdFilesForGameDirectory, FS_AddGameDirectory, and FS_AddSearchPath; the new helper slice intentionally excludes these bodies to prevent duplicate definitions.
- The Android directory adapter's Com_Printf diagnostic provider is disabled only in this link-audit target; the separately compiled Dvar Android log provider is the single Com_Printf definition in the combined object.

The native workflow now includes this archive in the AArch64 relocatable link and requires the directory/mount symbols to be defined with no remaining undefined reference for each one. It continues to require FS_ReadFile and SEH_InitLanguage to remain visible as unresolved next dependencies. This is an ABI/link audit, not a runtime claim.

## Validation gates

The CI run triggered by the code commit must pass all of the following before this phase is called green:

- Python source/provenance regression for the three helper bodies and no duplicate FS startup definitions.
- Host Release CTest and ASan/UBSan CTest.
- Android NDK ARM64 compile of iw3_sp_iwd_directory_services.
- Combined AArch64 relocatable link resolves Sys_ListFiles, FS_FreeFileList, FS_PathCmp, iwdsort, I_strncmp, SEH_GetLanguageName, SEH_GetLanguageIndexForName, Com_PrintWarning, FS_AddSearchPath, FS_AddGameDirectory, FS_AddIwdFilesForGameDirectory, FS_LoadZipFile, and the original ZIP reader entry points.
- FS_ReadFile and SEH_InitLanguage remain explicit unresolved runtime gates.

## Hard boundary

No code here calls FS_Startup() or FS_InitFilesystem() from the Android activity. No licensed IWD/FastFile or map is loaded by this audit. No original renderer scene, physical ARM64 execution, touch-driven weapon/actor combat, or playable APK is proven. The JNI package remains diagnostic only. Keep PR #4 open and unmerged.
