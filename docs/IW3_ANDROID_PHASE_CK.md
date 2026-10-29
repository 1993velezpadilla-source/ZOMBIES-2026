# IW3 Android Phase CK — filesystem read-service dependencies

This phase resolves two concrete undefined symbols reported by the previous combined ARM64 filesystem audit.

## Changes

- Extracts the original `logfile` global and `Com_LogFileOpen()` body from `third_party/KisakCOD/src/qcommon/common.cpp`, guarded by a source hash and exact body check.
- Ports the original `FastCriticalSection` writer-gate algorithm to Android/POSIX with sequentially-consistent atomics and `sched_yield()`; the upstream 8-byte counter layout is unchanged.
- Adds a native host test for the original logfile query, read-count gating, and writer exclusion under eight-thread contention.
- Adds mandatory CMake source wiring and a CI combined-link assertion for all three symbols.

## Scope boundary

The new sources are in the native dependency-audit archive only. They are not linked into the JNI diagnostic APK, and this pass does not claim that `FS_Startup` or `FS_InitFilesystem` runs in Android. FastFiles, map loading, rendering, touch-driven live simulation, and physical ARM64 gameplay remain open gates.

CI results should be appended after inspecting the run for this commit. Do not merge PR #4 until the full playable-APK criteria are evidenced.
