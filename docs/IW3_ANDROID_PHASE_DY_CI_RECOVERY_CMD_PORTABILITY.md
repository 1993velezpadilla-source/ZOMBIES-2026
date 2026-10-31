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

## Confirmed full-command ARM64 compilation — PASS, object only

The updated focused command workflow
[run 41104384098](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41104384098)
completed **SUCCESS** at commit `bcfaaed0`. Its logs show:

```text
IW3_OPENAL_HEADERS_REAL_API_STAGED_FOR_COMPILE_ONLY
Class: ELF64
Machine: AArch64
Cmd_Init()
Cmd_AddCommandInternal(char const*, void (*)(), cmd_function_s*)
Cmd_ExecuteSingleCommand(int, int, char*)
Cmd_TokenizeString(char*)
Cmd_EndTokenizedString()
IW3_ORIGINAL_CMD_FULL_TU_AARCH64_OBJECT_PASS
IW3_CMD_INIT_INVOKED=false
IW3_PLAYABLE_APK=false
```

The evidence artifact is
[13001025739 — original command ARM64 object, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41104384098/artifacts/13001025739).
This validates compilation of the **complete authentic original** `cmd.cpp`
and its command symbols, not a linked Android runtime.

## Native monolithic regression audit and repair

The native workflow [run 41104383866](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41104383866)
failed during its Python source tests, before the full native build. Four
assertions were stale: one still demanded Windows `std::format` paths, and
three still demanded the *old* filesystem relocatable-link command without
the now-required original `cmd_tokenizer_archive`. The workflow itself
contains the newer archive and audits `Cmd_TokenizeString` and
`Cmd_EndTokenizedString` in the combined startup graph.

The regressions were updated to require the **stronger current behavior**,
not disabled:

- `08a30535`: require native `std::filesystem::path` output and reject
  `std::format` / `fopen_s` in the original dump function.
- `2c1c62a3`: require the original tokenizer archive in the startup/Dvar/IWD
  relocatable links and tokenizer symbol-resolution checks.
- `88bb717e`: require the original tokenizer provider in the filesystem
  directory link audit.

GitHub read-back confirmed each new assertion matches the actual code.
The next native workflow must rerun all regressions and the NDK build.
Until that CI is complete, **do not claim native workflow PASS**.

The user-facing completion condition remains entirely unmet: no original
bootstrap, real map, rendered frame, live touch/gameplay, or playable APK.

## Subsequent native build failure — tokenizer console declarations

After the regression updates, native run
[41104884361](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41104884361)
passed the source-test stage and reached the Android CMake build, but
failed compiling the generated original tokenizer TU:

```text
iw3_cmd_tokenizer.cpp:174:20: error: 'CON_CHANNEL_SYSTEM' was not declared
iw3_cmd_tokenizer.cpp:174:9: error: 'Com_Printf' was not declared
```

The original `qcommon/cmd.cpp` already includes `qcommon.h` and compiles
successfully as a full ARM64 object in the focused gate. The extracted
tokenizer source omitted this real header while retaining the original
`AssertCmdArgsConsistency` function body. Commit `c56e117` adds
`#include <qcommon/qcommon.h>` to the generated tokenizer TU. This is
a declaration dependency from the authentic engine, **not** a fake console
implementation. Commit `6334711` adds a generator regression requiring
the include. A new native workflow must pass before claiming this fix
CI-green.

No gameplay, real map, renderer, touch-client execution or playable APK
has been demonstrated.
