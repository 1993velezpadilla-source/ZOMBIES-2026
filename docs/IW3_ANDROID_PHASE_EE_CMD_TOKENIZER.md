# Phase EE — original command tokenizer dependency on Android ARM64

**Date:** 2026-10-30  
**PR:** #4  
**Branch:** `feature/iw3-native-android-arm64-20261025`  
**Baseline inspected:** `a75d0ca617ed96c2ef6b44871433ee6ce76aeaa0`

## Baseline and next blocker

The latest native-source workflow on the inspected head was cancelled before its filesystem link audit completed. The latest preflight, FastFile POSIX, mover/trace, JNI diagnostic and emulator diagnostic runs were successful, but the JNI/emulator packages remain diagnostic. The Windows offline SP killhouse diagnostic still reported no real graphics frame or confirmed weapon shot.

The filesystem-startup link graph already included the original `Cmd_Argc`/`Cmd_Argv` accessors and the canonical `cmd_args` storage. The original command parser entry points were still absent from that graph: `Cmd_TokenizeString(char*)` and `Cmd_EndTokenizedString()`. The earlier complete source audit showed both as undefined. These are required by the original command path used around filesystem/startup command execution; merely linking argument accessors is not a command tokenizer.

## Implemented

A new generator, `tools/iw3_android/prepare_real_engine_cmd_tokenizer.py`, stages eight original function bodies from `third_party/KisakCOD/src/qcommon/cmd.cpp` without rewriting their algorithms:

- `Cmd_TokenizeStringWithLimit`
- `Cmd_TokenizeStringKernel`
- `Cmd_TokenizeStringInternal`
- `Cmd_IsWhiteSpaceChar`
- `AssertCmdArgsConsistency`
- `Cmd_TokenizeString`
- `Cmd_EndTokenizedString`
- `Cmd_EndTokenizedStringKernel`

It also stages the single original `CmdArgsPrivate cmd_argsPrivate;` declaration. The existing `cmd_args` state and `Cmd_Argc`/`Cmd_Argv` archive remain separate, avoiding duplicate ownership.

The NDK CMake build creates `iw3_sp_cmd_tokenizer` as a static audit archive. The native-source workflow includes it in the `ld.lld -r` filesystem-startup, Dvar/startup, and full FS/IWD graphs. It requires the two public tokenizer entry points and `cmd_argsPrivate` to be defined and absent from the resulting undefined-symbol list.

A Python regression executes the generator against the vendored source, compares every extracted body with the original function extractor, checks the single private-state declaration, and checks the CMake/workflow link gates.

## Deliberate boundaries

This is **not** a complete command runtime:

- `Cmd_Init` is not extracted or invoked. The original engine initialization must reset `cmd_args.nesting` and the pool counters before tokenization.
- Command registration, command-buffer dispatch, and the full `cmd.cpp` translation unit are not included.
- The tokenizer archive is not linked into the JNI diagnostic shared library.
- The relocatable link audits do not invoke `FS_Startup` or `FS_InitFilesystem`.
- No FastFile, BSP, renderer frame, touch-driven gameplay, weapon shot, actor update, or playable APK is claimed.

The purpose of this pass is to close the next authentic command-parser edge in the filesystem/startup dependency graph without introducing a stub or pretending that the graph is a running engine.

## CI evidence

The code commit triggers the source preflight and the original Android NDK source workflow. The generated tokenizer source, JSON provenance report, static archive, and combined filesystem symbol reports are retained in the existing source-only artifact. Final run IDs and conclusions are recorded in the PR conversation after the workflows finish.

**Completion flags remain false:** `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_GAME_DATA_MOUNTED=false`, `IW3_PLAYABLE_APK=false`.
