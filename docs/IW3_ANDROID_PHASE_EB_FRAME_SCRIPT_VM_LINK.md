# IW3 Android Phase EB — original frame + script VM linkage audit

Date: 2026-10-30

## Starting state inspected

The previous script-VM pass is documented in `IW3_ANDROID_PHASE_EA_SCRIPT_VM_LP64_TRACKING.md`. The original `script/scr_vm.cpp` translation unit now compiles as an ELF64/AArch64 object, and its original `Scr_RunCurrentThreads()` and `Scr_IncTime()` definitions are visible in the object. The original SP frame source `game/g_runframe.cpp` calls both functions.

Baseline CI: [run 41082714011](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41082714011), SUCCESS. That result was compile/symbol evidence, not runtime linkage.

## This pass

The source workflow now performs an actual **relocatable link** of the complete original SP frame object from `iw3_sp_frame` and the complete original script VM object from `iw3_sp_script_vm_full_compile` using the NDK's `ld.lld -r`.

The gate:
1. Proves the frame object had undefined `Scr_RunCurrentThreads()` and `Scr_IncTime()` references before the link.
2. Verifies both original definitions exist in the VM object.
3. Creates a combined AArch64 relocatable object and checks its ELF architecture.
4. Verifies both scheduler symbols are defined and no longer undefined in the combined object.
5. Requires an unrelated gameplay service (`G_UpdatePlayerTriggers(gentity_s*)`) to remain undefined, demonstrating that the combined object is intentionally partial and does **not** claim full engine linkage.
6. Preserves the before/after symbol reports and combined object in the CI artifact.

A source regression test checks that the gate remains present and that the frame/runtime/playable-APK flags stay explicitly false.

## Validation boundary

This is stronger than separate compile-only checks because it verifies that two authentic translation units can resolve the SP frame's script scheduler edges at the object-link level. It is still only a relocatable link audit.

It does **not** link the complete engine executable/shared library, invoke the scheduler on Android, initialize the filesystem in the runtime, load a real FastFile/BSP, render a frame, or prove touch-driven weapon/actor gameplay.

Required evidence remains:

```
IW3_FRAME_SCRIPT_VM_RUNTIME_LINKED=false
IW3_REAL_MAP_LOADED=false
IW3_GAMEPLAY_PROVEN=false
IW3_PLAYABLE_APK=false
```

PR #4 must remain open and unmerged until a real Android ARM64 build boots the original engine, loads a genuine map, renders with a real backend, consumes touch through the live client command loop, and demonstrates gameplay using the original weapon/actor systems.
