# IW3 ARM64 strict-link blocker — 2026-11-07

Scope: genuine KisakCOD IW3 single-player engine only. This is a blocker report, **not** a playable APK report.

## Reproduced on branch head

- Commit: `d8293bd3826c728f3bb545e567a5519540565b3a`.
- CI: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42361390712
- Job: `original-bootstrap-aggregate` (128370348868).
- Fifteen original translation units compiled. Strict `ld.lld` link fails; workflow marks this *expected failure* and reports success. The job prints `IW3_BOOTSTRAP_UNRESOLVED_UNIQUE=653` and `IW3_PLAYABLE_APK=false`.
- Evidence artifact: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/42361390712/artifacts/13569651681 (compile log, strict-link probe, defined and undefined symbol sets).

## Next integration priority: original service providers, not more BSP-size edits

The linker errors include the following **real unresolved dependencies**:

| Service family | Examples from strict link | Required action |
| --- | --- | --- |
| Filesystem / platform | `Sys_Cwd`, `Sys_ListFiles`, `Sys_DirectoryHasContents`, `Sys_CountFileList`, `z2026_platform_rename_engine_path` | Include existing genuine POSIX/Android providers in the aggregate link, checking C++/C ABI and duplicate definitions. |
| ZIP/IWD | `unzOpen`, `unzGetGlobalInfo`, `unzGoToFirstFile`, `unzGetCurrentFileInfo`, `unzGoToNextFile` | Include the existing original ZIP implementation and verify native-width structures. |
| Hunk allocator | `Hunk_UserAlloc`, `Hunk_CopyString` | Include original shared allocator implementation; do not stub allocation. |
| Core / dvars | `Com_FilterPath`, `Com_BlockChecksumKey32`, `Dvar_ClearModified`, `Dvar_SetDomainFunc` | Bring in authentic core services and their transitive dependencies. |
| Localization | `SEH_InitLanguage`, `SEH_Shutdown_StringEd`, `SEH_GetLanguageName`, `SEH_GetLanguageIndexForName` | Link genuine localization providers or preserve explicit supported feature configuration. |
| Assets / renderer | `DB_GetXAssetHeaderName`, `DB_GetXAssetTypeName`, `Image_Free`, `Material_ReleaseTechniqueSet`, `comWorld`, `gameWorldSp` | Integrate original DB/render/world services; verify Android graphics backend separately. |

The 653 count measures the **current isolated aggregate**, not the number of functions that must be reimplemented. Before changing code, expand the link inputs using existing genuine source providers and compare unresolved-symbol sets. A reduction in this count alone does **not** establish runtime viability.

## Hard acceptance gates

1. AArch64 strict link completes without undefined symbols or synthetic stubs.
2. ARM64 APK boots authentic engine initialization and loads actual game/map data.
3. Original renderer displays a real map scene on Android.
4. Touch input reaches the original client command/game loop.
5. Original gameplay, weapons, and actors run on an ARM64 Android device, with captured runtime evidence.

**Current result: `IW3_PLAYABLE_APK=false`.** Diagnostic JNI APK and green partial CI jobs are not game evidence. Keep PR #4 unmerged.
