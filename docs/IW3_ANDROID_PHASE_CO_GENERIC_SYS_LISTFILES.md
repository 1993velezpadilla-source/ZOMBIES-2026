# IW3 Android Phase CO — generic original filesystem listing

Date: 2026-10-29

## Concrete blocker found

The previous Android Sys_ListFiles platform boundary only accepted the iwd
extension, rejected every non-empty wildcard filter, and rejected directory
queries (wantsubs != 0). That was sufficient for one narrow
FS_AddIwdFilesForGameDirectory call, but not for the broader original
filesystem graph: the vendored com_files.cpp also asks for directory entries
(for example, mod folders) and filtered ordinary files used by the original
filesystem/StringEd search path.

## Changes

- Added z2026_platform_list_directory_entries, a POSIX directory enumerator
  rooted at the retained app-private data directory. It normalizes engine paths,
  rejects traversal/out-of-root paths, skips hidden entries and symlinks, uses
  fstatat(..., AT_SYMLINK_NOFOLLOW), distinguishes regular files from
  directories, and fails atomically when the caller's output buffer is too small.
- Expanded the Sys_ListFiles adapter to handle ordinary extension suffixes,
  the existing id Tech 3 Com_FilterPath wildcard provider, and directory-only
  searches. The original IWD-specific path remains separate so its native
  readdir prefix and 1024-entry cap behavior are preserved exactly.
- Linked the existing filter provider into the diagnostic shared-library target.
- Added native host regression coverage for regular files, directory queries,
  hidden files, symlink exclusion, traversal rejection and capacity overflow,
  plus source guards for the original adapter contract.

## Validation boundary

This makes the Android filesystem platform service less incomplete; it does
not invoke FS_Startup or FS_InitFilesystem from the Activity. The
filesystem/startup and language/dvar service graph is still not a live Android
runtime. No real game data/FastFiles/map load, renderer frame, weapon/actor
simulation or physical ARM64 gameplay is claimed. The JNI package remains a
diagnostic package, not a playable APK. PR #4 must remain unmerged.
