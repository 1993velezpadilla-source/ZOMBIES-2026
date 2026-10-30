# Phase DY — recover native ARM64 CI and port authentic IW3 command file output

Date: 2026-10-30 (UTC)  
Repository: `1993velezpadilla-source/ZOMBIES-2026`  
PR: #4, branch `feature/iw3-native-android-arm64-20261025`  
**Status: CI pending. Not a playable APK. Do not merge.**

## Baseline and reproducible blocker

The PR head before this pass was `1c303d511a6bf554a5224de4498b95b06d230ae6`.
GitHub Actions run [41103229047](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41103229047)
failed at workflow ingestion, with no runnable jobs. The native workflow contained
6,218 lines: an otherwise complete workflow was followed by an unindented,
truncated shell fragment after the final upload-artifact step and repeated
copies of the same CI steps. Inside the first copy, the
`cmd_argsPrivate` symbol-audit shell command was itself truncated.
This blocked validation before compilation.

## Fix 1 — restore one genuine-engine ARM64 workflow

Commit `80c52f335bee23d61908f755b8c6aeb29accaf48`:

- Removed the corrupt appended duplicate fragments and retained the first,
  complete native build workflow (38 uniquely named steps).
- Repaired the original command tokenizer's `cmd_argsPrivate` defined/undefined
  symbol checks, preserving the strict fail-on-unresolved behavior.
- Restored the tokenizer and filesystem relocatable-link artifacts to the final
  evidence upload. The output is explicitly **NOT APK**.
- Did not disable ABI, symbol, build, or gameplay checks.

New regression: `tests/test_iw3_android_workflow_integrity.py`
(commits `fd53592`, `c19b5cc`) guards against duplicate step names, truncated
symbol checks, malformed trailing content, and missing evidence paths.

## Fix 2 — genuine KisakCOD `qcommon/cmd.cpp` portability

Commits `6546897` and `7e20f74` edit
`third_party/KisakCOD/src/qcommon/cmd.cpp`, not a surrogate engine:

- Replaced the four Windows-only `fopen_s` calls in `Cmd_Dumpraw_f()` with
  standard `fopen` plus explicit failure checks before `fwrite`.
- Replaced Windows backslash-concatenated `std::format` paths with native
  `std::filesystem::path` joins for raw output and `zone/english`.
- Fixed the string-table directory to derive from the string-table name,
  not a rawfile union field.
- Preserved the complete output filenames for sound dumps; only parent
  directories are created before opening files.
- Preserved the original `Cmd_Init`, command registry, dispatcher, and tokenizer.

The command tokenizer regression now checks these portability invariants.
The focused workflow `.github/workflows/iw3-command-full-arm64.yml`
must still compile the complete original `cmd.cpp` to ELF64/AArch64 and
inspect the real symbols before the compilation is marked PASS.

## Verification actually performed

Read back the updated branch from GitHub and checked:

- Native workflow: exactly one `jobs:` block, 38 distinct named steps,
  complete `cmd_argsPrivate` audit, and one terminal evidence upload.
- Original `cmd.cpp`: `Cmd_Init()` still present, zero `fopen_s`,
  zero `std::format`, four checked `fopen` calls, two sound parent-directory
  creations, no filename-stripping `remove_filename()`.
- PR #4 remained OPEN and unmerged at the read-back.
- The previous no-job CI failure was confirmed. The newly queued CI runs
  were **not** reported as green; GitHub runners had not completed them.

These are source/read-back checks. They are not substitutes for a successful
NDK compile or Android runtime execution. Do not infer gameplay.

## Remaining work and hard release gate

1. Wait for the latest focused command full-TU ARM64 CI and native workflow
   to finish; inspect compiler output, symbols and the integrity regressions.
2. Fix any real Android compilation errors in the original engine, retaining
   the original command behavior.
3. Link and execute the complete command, filesystem, Dvar and bootstrap
   services in an Android process; demonstrate real `Cmd_Init`,
   `FS_Startup` and `FS_InitFilesystem` calls.
4. Mount authentic game data, load a real FastFile/BSP, render a real
   scene with an Android graphics backend, feed touch into live
   `CL_CreateCmd`, and run original weapon/actor gameplay.
5. Record on-device ARM64 execution evidence and provide the **playable**
   APK only when every gate passes.

No Godot, no replacement engine, no diagnostic-JNI-as-game claim.

## CI observation and follow-up — real OpenAL header dependency

Focused full-command run
[41103747583](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41103747583)
completed **FAILURE**. The job logs confirm the tokenizer preparation ran and
the Android NDK began compiling the **complete original** `cmd.cpp`, but the
compiler stopped at `third_party/KisakCOD/src/sound/snd_local.h:14`:

```text
fatal error: 'AL/al.h' file not found
23 warnings and 1 error generated.
```

This is a real external OpenAL API header dependency, not a successful object
build and not evidence of a runnable audio subsystem.

Commit `54e204c` updates the focused workflow to install `libopenal-dev`
on the Linux runner, stage its **real** `AL/al.h`, `AL/alc.h` and `AL/efx.h`
API headers in an isolated temporary include directory, and provide that
include root to the Android NDK compiler. It does **not** enable the
`IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL` substitute declarations or
pretend OpenAL runtime libraries have been linked into Android.

Commit `b5a2322` adds a regression requiring the real header staging.
The next focused workflow execution must be inspected for the next compiler
error or a real ELF64/AArch64 `cmd.cpp` object. No PASS is claimed while
the updated run remains queued or in progress.

The full original command system, `Cmd_Init()`, filesystem startup,
renderer and gameplay are still **not** executing in an Android APK.

## CMake default-build isolation

The newly added full `cmd.cpp` OBJECT target would otherwise be built by
every default Android CMake build, including the separate math/JNI diagnostic,
before real OpenAL headers were supplied. Commit `ef48a307` marks only
`iw3_sp_cmd_full_compile` as `EXCLUDE_FROM_ALL`, preserving the explicitly
invoked focused ARM64 command gate. Optional `IW3_OPENAL_HEADERS_ROOT` is
validated against real `AL/al.h`, `AL/alc.h`, and `AL/efx.h` if supplied
for an explicit CMake build. Commit `8480422` adds regression assertions.

This does not hide the full-TU portability gate: its dedicated workflow
still compiles the authentic `cmd.cpp` with real OpenAL API headers. It does
prevent an unrelated diagnostic default build from failing on an optional
compile-only target. No command system runtime execution is claimed.
