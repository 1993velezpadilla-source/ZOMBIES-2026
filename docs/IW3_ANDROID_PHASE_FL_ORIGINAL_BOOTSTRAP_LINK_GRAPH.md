# Phase FL — authentic IW3 bootstrap dependency-link graph (not gameplay)

Date: 2026-10-31. Repository `1993velezpadilla-source/ZOMBIES-2026`, PR #4, branch `feature/iw3-native-android-arm64-20261025`. **NOT A PLAYABLE APK.**

## What was implemented

Extended `.github/workflows/iw3-command-full-arm64.yml` to compile the complete upstream `third_party/KisakCOD/src/qcommon/common.cpp` with the same Android compatibility header definitions used by its existing CMake compile gate. The complete original `qcommon/cmd.cpp`, `universal/dvar.cpp`, and `universal/com_files.cpp` are compiled as AArch64 objects, then linked together with `common.cpp` using `ld.lld -m aarch64linux -r`. This is a **relocatable dependency link**, not an Android runtime or executable. It introduces no Godot, substitute engine, fake `Com_Init`, or fake renderer.

The new link gate requires genuine definitions for `Com_Init(char*)`, `Com_Frame()`, `Cmd_Init()`, `Dvar_Init()`, `FS_InitFilesystem()`, `FS_Startup(char*)`, and `FS_FOpenFileRead(char const*, int*)`. It checks that those names are not left unresolved in the combined original-code object. `FS_InitFilesystem` and `FS_Startup` are provided by the authentic `universal/com_files.cpp`, not by `qcommon/files.cpp`.

The gate also preserves the **unresolved** `Sys_GetValue(int)` and `CL_InitRenderer()` dependencies. `Com_Init` needs the original per-thread error-context value (used with `setjmp`) and a real client/renderer initialization path. No fake implementations were added to force a link. These are concrete remaining platform/rendering blockers.

Added `tests/test_iw3_android_cmd_bootstrap_graph.py` to assert the four genuine sources, the required link, artifact preservation and non-game markers. Updated `tests/test_iw3_android_cmd_tokenizer.py` so its real-OpenAL requirement applies specifically to the standalone `cmd.cpp` compilation; the separate `common.cpp` gate can use its existing header-only Android compatibility overlay. Added the new regression to workflow path filters.

## CI evidence

- GitHub Actions run **41181569070** at commit **f6d87e08**: **success**; job `124479887762`, step `Link authentic Com_Init with original command, dvar and filesystem units (NOT GAME)` passed.
- The job executed **20 Python tests**, all passing.
- Verified output: `IW3_ORIGINAL_COMMON_CMD_FILES_DVAR_RELOCATABLE_LINK_PASS` and `IW3_ORIGINAL_FS_INITFILESYSTEM_PROVIDER_RESOLVED`.
- Verified unresolved original runtime edges: `U Sys_GetValue(int)` and `U CL_InitRenderer()`, with explicit missing-provider markers.
- Artifact `iw3-original-command-full-aarch64-NOT-APK` (artifact ID **13035376404**) preserves the original ELF objects, combined relocatable object, and symbol reports. This artifact is **not** an APK.
- The separate full ARM64 matrix workflow was still in progress when this report was prepared; do not infer its result from the command workflow.

CI URL: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41181569070

## What is still missing

No `Com_Init` was executed in an Android process. `IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false`, `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_RENDERER_FRAME_PROVEN=false`, `IW3_REAL_MAP_LOADED=false`, `IW3_GAMEPLAY_PROVEN=false`, and `IW3_PLAYABLE_APK=false` remain mandatory.

Next, provide the real Android thread-context/error-jump service that honors the original `Sys_GetValue(2)` contract, then progressively link the original client and renderer dependencies. Validate initialization, imported game data, map loading, touch consumption and weapon/actor frames on an ARM64 device before claiming a playable APK. Keep PR #4 open and do not merge to main.
