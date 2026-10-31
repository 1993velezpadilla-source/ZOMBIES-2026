# IW3 Android ARM64 — Phase DR: complete original BGame dvar translation unit

Date: 2026-10-30

## Baseline inspected

The branch head before this pass was `f46ee60f8eedc22ae6948e5b7af605ea2ff7c23f`. The current native ARM64 workflow completed successfully on that head (run 41088389085), and the Android x86_64 JNI emulator diagnostic completed successfully (run 41088388404). The native workflow already compiled the original `bg_weapons.cpp`, but the melee dvar storage and four original registration blocks were still staged by `prepare_real_engine_melee_dvar_services.py`. That generated slice left the real `Dvar_RegisterFloat` edge unresolved and was not a substitute for the complete BGame source.

## Change

Added an Android object-only target for the complete upstream `third_party/KisakCOD/src/bgame/bg_misc.cpp` translation unit. It is compiled with the original SP/OpenAL definitions and the engine's actual include tree.

The ARM64 workflow now:
1. verifies the full object is ELF64/AArch64;
2. verifies the original `BG_RegisterDvars()` and the four melee dvar globals are defined by `bg_misc.cpp`;
3. verifies that the original BGame object references `Dvar_RegisterFloat`;
4. locates the complete original `universal/dvar.cpp` object from the existing `iw3_sp_full_dvar` target;
5. performs an AArch64 relocatable link and requires the original `Dvar_RegisterFloat` edge to become defined while preserving the other unresolved engine services.

This supersedes the four-variable staged registration slice for the purpose of compile/link evidence. It does not invoke `BG_RegisterDvars()` and does not initialize a live dvar registry.

## Validation

The new regression is `tests/test_iw3_android_bgame_misc_full_compile.py`. The ARM64 workflow emits:

- `IW3_ORIGINAL_BGAME_MISC_DVAR_AARCH64_OBJECT_PASS`
- `IW3_ORIGINAL_BGAME_MISC_DVAR_FLOAT_RELOCATABLE_LINK_PASS`

The artifact is named `z2026-iw3-bgame-misc-full-dvar-arm64-NOT-APK` and contains only ELF objects and symbol reports.

**CI result: PASS** on commit `647ee97f0b7ed6e2e693d79e98eea1ec969a0756`.

- Native Android ARM64 workflow [41091658529](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658529): **SUCCESS**. The complete `bg_misc.cpp` object compiled as ELF64/AArch64, and the relocatable link with the original `universal/dvar.cpp` object resolved `Dvar_RegisterFloat`.
- The log contains `IW3_ORIGINAL_BGAME_MISC_DVAR_AARCH64_OBJECT_PASS` and `IW3_ORIGINAL_BGAME_MISC_DVAR_FLOAT_RELOCATABLE_LINK_PASS`.
- The four melee globals and `BG_RegisterDvars()` are defined by the full BGame object; `Dvar_RegisterFloat` is undefined before the partial link and defined afterward.
- Preflight [41091658499](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658499), FastFile POSIX [41091658568](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658568), mover/trace [41091658528](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658528), and JNI diagnostic build [41091658495](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658495) also passed. The Android x86_64 emulator diagnostic [41091658527](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658527) was still running at this checkpoint.
- Evidence artifact [12993439691](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658529/artifacts/12993439691) contains the AArch64 object, combined relocatable object, and symbol reports. It is **NOT APK**.

The failed first attempt and its `sprintf_s` portability correction are documented above.

## Explicit boundary

- Complete original BGame `bg_misc.cpp` compiled for AArch64: pending CI.
- Original BGame-to-Dvar float registration edge relocatably linked: pending CI.
- `BG_RegisterDvars()` invoked in Android runtime: false.
- Dvars registered in a live Android game runtime: false.
- Client/server runtime linked: false.
- FastFile/BSP loaded by the full engine: false.
- Original renderer frame presented: false.
- Touch-to-live-client/game-frame path executed: false.
- Physical ARM64 gameplay with weapons and actors: false.
- Playable APK: false.

PR #4 remains open and unmerged.

## First compile result and Android correction

The first native workflow attempt for commit `0307ff5ccba37cd7c82192445c6d71624a10c34d` failed during the all-target CMake build before reaching the new link audit. The compiler pinpointed the remaining Windows CRT call at `bg_misc.cpp:218`:

`error: use of undeclared identifier 'sprintf_s'`

The original call formats the bounded `bgShockChannelNames[i]` entry as `bg_shock_volume_%s`. The engine source now retains the secure CRT `sprintf_s` call on Windows and uses Android's `snprintf` with the same destination size on non-Windows platforms. The Android branch checks the returned length and calls the original fatal engine error path instead of registering a truncated dvar name. A regression now protects the platform split and the fail-closed length check.

The failed build is recorded in [run 41091115694](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091115694). The new compile/link validation remains pending on the correction commit.

## Final emulator-diagnostic result for this commit

The x86_64 Android emulator diagnostic [41091658527](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41091658527) subsequently completed with **SUCCESS**. Its evidence validator confirmed execution of the original ZIP32/IWD parser and fixture mount/searchpath/read/close paths, including the imported IWD index, shared `fsh` table, directory fallback, and touch DOWN/UP readback into the diagnostic `usercmd_s` adapter.

The same validator explicitly reported:

- `full_original_com_files_translation_unit_linked=false`
- `original_cl_createcmd_touch_consumption_proven=false`
- `original_client_runtime_linked=false`
- `real_map_loaded=false`
- `renderer_frame_proven=false`
- `arm64_device_execution_proven=false`
- `gameplay_proven=false`
- `playable_apk=false`

This is emulator diagnostic evidence only, not proof of the native ARM64 engine or a playable build. The SP killhouse runtime diagnostic and source-only weapons workflow were cancelled in this run set and are not counted as passes.
