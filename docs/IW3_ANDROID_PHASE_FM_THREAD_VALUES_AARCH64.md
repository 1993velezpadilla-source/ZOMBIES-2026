# Phase FM — original IW3 thread-value ABI for Android ARM64 (NOT GAME)

Date: 2026-10-31. PR #4, branch `feature/iw3-native-android-arm64-20261025`.

## Observed blocker in authentic engine

The previous relocatable graph joined original `qcommon/common.cpp`, `qcommon/cmd.cpp`, `universal/dvar.cpp` and `universal/com_files.cpp`, but left `Sys_GetValue(int)` unresolved. Original `Com_Init`, `Com_Error` and `Com_Frame` use `Sys_GetValue(2)` as a `jmp_buf*` for `setjmp`/`longjmp`. The original Windows implementation in `qcommon/threads.cpp` uses `thread_local void** g_threadLocals` and `g_threadValues[THREAD_CONTEXT_COUNT][4]`, with a per-context four-slot table. The original module also depends on Win32 thread APIs, so it cannot yet be used as an Android platform provider.

## Implementation

Added `android/iw3-native/iw3_android_thread_values.cpp` and its header as an Android platform-boundary implementation of the **same original C++ `Sys_GetValue(int)` and `Sys_SetValue(int, void*)` symbols**. It preserves the four slots, original `ThreadContext_t` indices and thread-local binding. It rejects invalid slot access or unbound use rather than allowing silent memory corruption. An explicit `IW3_AndroidBindThreadContext` selects the original context table; `IW3_AndroidThreadHasErrorJump` allows the future real bootstrap to reject a missing `jmp_buf` before calling `Com_Init`.

This provider is a port of the OS-specific thread-value service, **not** a substitute engine, a fake `Com_Init`, or a replacement for original `Com_InitThreadData`. The original engine must still initialize its error-jump slot and the platform must bind the main thread before invoking `Com_Init`. Do not compile this provider alongside the original Windows `threads.cpp`, which defines the same global/symbols.

Added `android/iw3-native/tests/thread_values_native_test.cpp` to execute actual `setjmp`/`longjmp`, verify slot 2, and exercise two concurrent distinct IW3 contexts (MAIN and SERVER), plus invalid context rejection. Added `tests/test_iw3_android_cmd_thread_values.py` to guard source, CI and non-game claims.

Extended `.github/workflows/iw3-command-full-arm64.yml` to execute the host fixture under UBSan, cross-compile the provider for Android AArch64, and relocatably link it to the four **complete original engine objects**. The new gate must resolve `Sys_GetValue(int)` and `Sys_SetValue(int, void*)`, while leaving `CL_InitRenderer()` explicitly unresolved. ELF and symbol reports are preserved in the existing NOT-APK artifact.

## Verification and limits

Local host validation of the same provider and fixture: `c++ -std=c++20 -DKISAK_SP=1 -Wall -Wextra -Werror -fsanitize=undefined -pthread ...` executed successfully (`HOST_TEST_PASS`). This local preflight used a header copy matching the original SP `ThreadContext_t`; GitHub CI compiles against the **actual upstream** header.

GitHub Actions run **41184575807**, commit **24cc5e26**, job **124488802668**, finished **success** on 2026-10-31 08:27 UTC: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41184575807. Inspected full job logs: **23 Python tests passed**, the UBSan host fixture passed (`IW3_ANDROID_THREAD_VALUES_HOST_SETJMP_TLS_PASS`), and the original four complete engine objects plus the new AArch64 thread-value provider linked relocatably. `llvm-nm -C` confirmed defined `Sys_GetValue(int)`, `Sys_SetValue(int, void*)` and authentic `Com_Init(char*)`, with no unresolved duplicate for those names. The renderer dependency `U CL_InitRenderer()` remains. CI markers: `IW3_ORIGINAL_SYS_GETVALUE_AARCH64_PROVIDER_RESOLVED`, `IW3_ORIGINAL_RENDERER_RUNTIME_PROVIDER_MISSING`, `IW3_PLAYABLE_APK=false`. Artifact **13036346500** (`iw3-original-command-full-aarch64-NOT-APK`) preserves ELF objects and symbol reports, not an APK.

This is still a **relocatable symbol graph**, not an Android process that runs `Com_Init`. Missing: real main-thread initialization/`Com_InitThreadData`, full Android platform and client services, `CL_InitRenderer` with a working GPU backend, map/zone loading, live touch-to-client processing, gameplay/actors/weapons and ARM64 device evidence. `IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, `IW3_PLAYABLE_APK=false`. Do not merge PR #4.
