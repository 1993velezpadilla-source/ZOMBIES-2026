# IW3 Android Phase CK — filesystem read-service dependencies

This phase resolves two concrete undefined symbols reported by the previous combined ARM64 filesystem audit.

## Changes

- Extracts the original `logfile` global and `Com_LogFileOpen()` body from `third_party/KisakCOD/src/qcommon/common.cpp`, guarded by a source hash and exact body check.
- Ports the original `FastCriticalSection` writer-gate algorithm to Android/POSIX with sequentially-consistent atomics and `sched_yield()`; the upstream 8-byte counter layout is unchanged.
- Adds a native host test for the original logfile query, read-count gating, and writer exclusion under eight-thread contention.
- Adds mandatory CMake source wiring and a CI combined-link assertion for all three symbols.

## Scope boundary

The new sources are in the native dependency-audit archive only. They are not linked into the JNI diagnostic APK, and this pass does not claim that `FS_Startup` or `FS_InitFilesystem` runs in Android. FastFiles, map loading, rendering, touch-driven live simulation, and physical ARM64 gameplay remain open gates.

## Verified CI evidence (29 Oct 2026)

- Preflight: [40793488500](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488500) — PASS.
- Native ARM64 source audit: [40793488539](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488539) — PASS.
- Regression suite: 224 Python tests passed.
- CTest Release: 23/23 passed.
- CTest ASan/UBSan: 23/23 passed.
- The combined ARM64 link defined all three new services and emitted `IW3_ORIGINAL_FS_READFILE_LOGFILE_AND_WRITE_LOCK_AARCH64_LINK_GREEN`.
- Artifact [12862368849](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488539/artifacts/12862368849) is the native audit artifact, **not an APK**.

The same workflow log still states `IW3_PLAYABLE_APK=false`; `FS_Startup/FS_InitFilesystem` has not been invoked by the Android app. Do not merge PR #4 until the complete playable-APK criteria are evidenced.
