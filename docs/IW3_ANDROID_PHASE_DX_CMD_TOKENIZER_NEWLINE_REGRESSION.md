# Phase DX — command-tokenizer generator newline regression

Date: 2026-10-30  
Branch: `feature/iw3-native-android-arm64-20261025`  
PR: #4 — keep open and unmerged

## Baseline inspected

The branch head before this pass was `b65d6b8159bcfd74db98c7703789e0c84e92df1d`
(`Fix tokenizer source generator newline emission`). The generator
`tools/iw3_android/prepare_real_engine_cmd_tokenizer.py` had been corrected
to emit actual LF characters with Python string literals containing
`\\n` and `Path.write_text(..., newline="\\n")`.

The accompanying regression test still asserted that the generated source
contained the two-character sequence backslash + `n` after the include, and
its negative assertion checked a double-escaped sequence. That test encoded
the old bug rather than the intended generated C++ source layout.

## Change

Updated `tests/test_iw3_android_cmd_tokenizer.py` so it now:

- requires the include line followed by an actual newline character;
- rejects a literal backslash-`n` before the next include;
- continues to compare every extracted tokenizer function body against the
  authentic `third_party/KisakCOD/src/qcommon/cmd.cpp` body;
- continues to require one original `CmdArgsPrivate` state declaration and
  forbid extraction of `Cmd_Init` or command registration.

No KisakCOD engine source was rewritten. The generator still extracts the
original tokenizer functions and state verbatim.

## Validation boundary

The update was committed as `04199170de928dfef381229ede04946402fa111a`.
GitHub Actions was triggered by the branch push. The run must complete before
this pass can be called CI-green; this document does not predeclare a pass.

The existing native workflow stages and compiles the generated tokenizer
archive and performs an AArch64 relocatable-link audit with the original
filesystem-startup objects. That is a compile/link audit only. The tokenizer
archive is not linked into the JNI diagnostic APK and `FS_Startup()` is not
invoked by the app.

## Explicit non-claims

This change does not prove:

- live `Cmd_Init()` or command dispatcher initialization;
- `FS_Startup()/FS_InitFilesystem()` running in Android;
- real IWD/FastFile/BSP map loading;
- an original renderer frame;
- touch input consumed by a live client frame;
- weapon/actor gameplay on a physical ARM64 device;
- a playable APK.

The emulator workflow remains x86_64 diagnostic execution. Keep PR #4 open
and unmerged until the real Android bootstrap, map, renderer, live input and
gameplay gates are demonstrated.


## Follow-up — compile the complete original command-system TU

The next filesystem-startup blocker was that the prior audit only staged the original
tokenizer core; it deliberately omitted the original command dispatcher and
`Cmd_Init()`. Added the CMake OBJECT target
`iw3_sp_cmd_full_compile` for the complete upstream
`third_party/KisakCOD/src/qcommon/cmd.cpp`, with the original SP/OpenAL
definitions and the source include graph. The target is not linked into JNI and
does not claim command initialization.

A focused workflow,
`.github/workflows/iw3-command-full-arm64.yml`, now runs the tokenizer
regression, generates the verbatim tokenizer evidence, compiles the entire
original `cmd.cpp` with the pinned Android NDK for `arm64-v8a`, checks
ELF64/AArch64 and the original `Cmd_Init`, registry, dispatch and tokenizer
symbols, and uploads the object plus symbol reports as **NOT APK**.

Code revisions:
- `cad904941245eda4c97e0b68be2092d578162d23` — full command TU CMake OBJECT target.
- `a0fa012ab70355affabd6284a366cc27eae14ad9` — focused ARM64 workflow.
- `8a68d80d5e613c271e382bfcc167efc802fc0054` — regression coverage for the focused workflow.
- `04199170de928dfef381229ede04946402fa111a` — corrected the newline assertions to require real LF characters and reject literal backslash-`n` text.

At the time of this update, focused workflow run
[41103007734](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41103007734)
was queued; no compile result is claimed yet. The original command TU is not
yet linked to the Android runtime, `Cmd_Init()` is not invoked, and the
filesystem startup/map/renderer/gameplay gates remain open.
