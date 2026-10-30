# Phase DZ — authentic IW3 command/filesystem/Dvar link audit and IWD checksum fix

Date: 2026-10-30 UTC. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

**INCOMPLETE: no original-engine playable ARM64 APK. Do not merge to main.**

## Baseline inspected

At the beginning of this pass, PR #4 was open and the source head was
`14794c1f892d48471f596b60556e81cbf51fe83e`.
The focused full-original-command ARM64 workflow
[41107990623](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41107990623)
and the source-only native gate
[41107990595](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41107990595)
were both **SUCCESS**. Their evidence was source/object/diagnostic only.

The next integration gap was visible in the actual ELF symbol output: the
complete original `qcommon/cmd.cpp` still had unresolved calls into the
original filesystem (`FS_FOpenFileRead`) and Dvar (`Dvar_FindVar`), while
the Dvar source uses the original command argument API (`Cmd_Argv`).
Successful compilation of each TU alone did not prove these providers link.

## Changes

1. [ab60995c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/ab60995c220d19e63152db318403b371f08e75dd)
   extends `.github/workflows/iw3-command-full-arm64.yml` with an AArch64
   `ld.lld -r` audit of **three complete original KisakCOD TUs**:
   `qcommon/cmd.cpp`, `universal/com_files.cpp`, and
   `universal/dvar.cpp`. The gate checks the actual undefined dependencies
   before link, confirms exact providers after link, verifies ELF64/AArch64,
   retains the remaining undefined platform/server/renderer graph, and
   uploads the object, defined/undefined symbol lists and ELF header.
   **Relocatable object is NOT a running engine or APK.**
2. [37772422](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/37772422b23a65516fd176e8560d8b312a20b6bd)
   adds regression checks that enforce the original source paths, exact
   provider edges, unresolved-service report and non-game markers.
3. [8e76baa](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/8e76baaa78d89f9db2e6d7efd3144633e6cb5015)
   fixes a real repeated-call state bug in **original**
   `universal/com_files.cpp::FS_ReferencedIwdPureChecksums()`.
   The persistent global `info6` was reset at index zero, then appended
   `@` and a space using `strlen` without terminating either write.
   On later calls, stale bytes from the previous checksum could be reused.
   The original function now initializes a terminated `"@ "` prefix on
   every call; checksum and IWD traversal logic remain original.
4. [1a837e3](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/1a837e3f49cba686768f1d2c807c263327113911)
   adds a host regression compiling and **executing the verbatim original
   function body** repeatedly with empty and populated searchpaths.
   [ce5fc79](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/ce5fc79829b0c22bea67d0a3d5fe095c044c2e9e)
   corrects the expected original checksum count XOR in that test.

## CI verification status

- Pre-change source baseline: focused ARM64 command and native source CI GREEN
  as linked above.
- New head `ce5fc79829b0c22bea67d0a3d5fe095c044c2e9e`:
  [focused command/link run 41115250924](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41115250924);
  [native source run 41115250966](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41115250966).
  **Both must be inspected for final conclusion.** No link PASS or runtime
  success is claimed before those jobs complete.
- The host checksum harness is a regression with instrumented services; it
  does not demonstrate a real IWD mounted in an Android process.

## Remaining genuine-engine release gate

`IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`
`IW3_CMD_INIT_INVOKED=false`
`IW3_FS_STARTUP_RUNTIME_INVOKED=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

The next implementation milestone is a real Android startup service graph
with authentic `Cmd_Init`, Dvar and `FS_Startup` executed, followed by
real map/FastFile/BSP loading, a working graphics backend, touch through
live `CL_CreateCmd`, and original weapon/actor frames on ARM64 hardware.
No Godot, no replacement simulation, no diagnostic JNI as game.
