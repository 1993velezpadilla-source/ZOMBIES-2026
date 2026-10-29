# IW3 Android ARM64 phase CV — original filesystem command-registration chain

Date: 2026-10-29

## Review and concrete change

Reviewed PR #4 head `aa208fbef970dc4ab87ca865c1c7b7488c0b0972`, the latest ARM64 audit (run 40842641100), the JNI diagnostic (40842640699), emulator diagnostic (40842640877), and the Windows SP smoke (40842640832). All four workflows completed successfully on that head, but the evidence still explicitly reports `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_GAME_DATA_MOUNTED=false`, and `IW3_PLAYABLE_APK=false`.

The next source-level edge was the original `FS_Startup -> FS_AddCommands -> Cmd_AddCommandInternal` path. The extracted startup body referenced `FS_AddCommands()` and `FS_Path_f()`, but the audit object did not contain the original filesystem command handlers or the original command-list insertion primitive.

This pass extends `prepare_real_engine_fs_startup.py` to stage, with SHA-256 evidence, the original `FS_DisplayPath`, `FS_Path_f`, `FS_FullPath_f`, `FS_Dir_f`, `FS_SortFileList`, `FS_ConvertPath`, `FS_NewDir_f`, `FS_TouchFile`, `FS_TouchFile_f`, and `FS_AddCommands` bodies from `src/universal/com_files.cpp`. It also stages the original `Cmd_AddCommandInternal` and `Cmd_FindCommand` bodies and the original static `cmd_functions` list state from `src/qcommon/cmd.cpp`. The five `cmd_function_s` storage nodes used by the filesystem command handlers are preserved from the upstream source.

The host-only localized-path test excludes this command subsystem under `IW3_FS_STARTUP_HOST_TEST`, retaining its narrow observable test service. The Android ARM64 dependency audit compiles the upstream bodies and requires the filesystem command handlers and command registry primitives to be defined and absent from the combined undefined-symbol list. No command stubs are added.

## Validation status

The first ARM64 build exposed one real compile error in this new slice: `FS_DisplayPath` called the original `FS_IwdIsPure(iwd_t*)` provider without a visible declaration. The follow-up fix adds the exact provider declaration to `iw3_android_fs_startup_compat.h` and a regression that prevents the startup compatibility header from losing it. The provider body itself remains the original body staged by `prepare_real_engine_fs_read.py`; no local replacement is introduced.

Fresh CI for the follow-up commit is required before this phase is considered validated. The expected marker is:

`IW3_ORIGINAL_FS_COMMAND_REGISTRATION_AARCH64_LINK_GREEN`

The generated startup report must continue to state that the command registry has not been invoked by Android runtime and is not linked into the JNI diagnostic library.

## Evidence boundary / next blockers

This closes a source/link dependency edge only. The current Android Activity still calls the diagnostic JNI probes; it does not invoke original `FS_Startup()` or `FS_InitFilesystem()`. Real game IWDs are not mounted through the full upstream searchpath table, licensed FastFiles/maps are not loaded, the original renderer is not active, and touch commands are not driving the live frame loop. Physical ARM64 gameplay, actual weapon fire, damage/death, and actors remain unproven. Keep PR #4 open and unmerged.
