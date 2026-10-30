# IW3 Android Phase ED — root-confined original filesystem mutations

Date: 2026-10-30

## Baseline inspected

- Repository: `1993velezpadilla-source/ZOMBIES-2026`
- PR: #4
- Branch: `feature/iw3-native-android-arm64-20261025`
- Baseline head: `86b0e34178b0956611d785fa603fae52fb9e4a81`
- PR remained open and unmerged.

The current Android port compiled the complete original `universal/com_files.cpp`, but its mutation paths still used desktop-style raw `remove()` and `rename()` calls on paths built by `FS_BuildOSPath`. In particular, `FS_Delete` and `FS_DeleteInDir` did not pass through the retained filesDir root adapter. The existing `FS_CreatePath` traversal check only guarded directory creation; it did not confine delete/rename operations.

## Implemented in the authentic engine

### Original `com_files.cpp`

Android branches of these original functions now use rooted platform services:

- `FS_Delete`
- `FS_DeleteInDir`
- `FS_Remove`
- `FS_Rename`
- `FS_SV_Rename`

Windows keeps the original CRT `remove()` / `rename()` paths and the original copy fallback. Android fails closed if the rooted operation cannot be performed. The Android rename path uses `renameat` within the retained app-private filesystem; no absolute-path fallback or unrooted copy fallback is used.

### Native Android platform boundary

Added:

- `z2026_platform_remove_engine_path`
- `z2026_platform_rename_engine_path`

Both normalize the engine path against the retained filesDir root and resolve parent directories with `open_parent_beneath_root`, which rejects traversal and symlinked parent components.

Removal uses `fstatat(..., AT_SYMLINK_NOFOLLOW)` plus `unlinkat`. A symlink leaf is removed as a link, never followed. Empty-directory removal preserves the original `remove()` behavior.

Rename opens both parent directories beneath the root and calls `renameat`; the original `FS_SV_Rename` directory-move behavior is retained. A symlink source is rejected, and parent symlinks cannot redirect either side of the operation.

## Verification added

- Host runtime regression exercises absolute and Windows-style engine paths, file removal, empty-directory removal, file rename, directory rename, sibling-prefix/traversal rejection, symlink-parent rejection, and symlink-leaf removal.
- Source regression ensures all five original filesystem functions use the rooted services only on Android while preserving the Windows CRT calls.
- NDK workflow performs an `ld.lld -r` link of the complete original filesystem TU, its canonical state/handle-table TUs, and the Android platform provider. It requires both new services to resolve and checks that `fs_searchpaths`, `fs_gamedir`, and `fsh` each have one definition.
- The combined object deliberately retains `Sys_ListFiles` as an unresolved engine service, proving this is still a partial dependency audit rather than a complete filesystem runtime.

The artifact is named `iw3-original-filesystem-rooted-mutations-aarch64-NOT-APK`.

## Explicit completion boundary

This pass fixes path-mutation confinement and resolves those platform service edges at relocatable-object level. It does **not** invoke `FS_Startup` or `FS_InitFilesystem` in an Android game runtime, mount licensed IWD/FastFiles, load a BSP, render a frame, connect touch to a live client loop, or prove ARM64 gameplay.

Required status remains:

```
IW3_FULL_FILESYSTEM_RUNTIME_LINKED=false
IW3_FS_STARTUP_RUNTIME_INVOKED=false
IW3_REAL_MAP_LOADED=false
IW3_GAMEPLAY_PROVEN=false
IW3_PLAYABLE_APK=false
```

PR #4 must remain open and unmerged.
