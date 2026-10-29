# Phase CN — resolve the original Android touch-adapter edge

**Scope:** connect the already-staged, authentic IW3 SP client-command functions to the actual Android platform touch adapter at the AArch64 relocatable-link level. This is a dependency-audit step only; it is not a live client, renderer, map, gameplay, or playable-APK claim.

## Baseline inspected first

The latest documented client-input code revision was `f625778e483edc15e7e5da4a0a96f9af8b4bce2d` (Phase CM). The associated GitHub Actions runs were inspected:

- Native ARM64 audit [40803348938](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40803348938): PASS.
- JNI diagnostic build [40803348823](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40803348823): PASS, diagnostic only.
- Android emulator probe [40803349072](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40803349072): PASS for existing diagnostic path; x86_64 emulator only.
- SP Killhouse smoke [40803348878](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40803348878): smoke test only; weapon-fire, damage, death, and graphics evidence flags remained false.

Phase CM had compiled and relocatably combined the original `CL_CreateCmd`, `CL_FinishMove`, `CL_MouseMove`, and `CL_GetMouseMovement`. The command chain still left `z2026_platform_apply_touch_to_usercmd` unresolved. The implementation already existed in `android/iw3-native/iw3_android_platform.cpp` and the host platform test already exercised its effects on the real IW3 SP `usercmd_s` layout, but that provider had not been included in this ARM64 combined-object audit.

## Change in this phase

The native workflow now compiles the actual `iw3_android_platform.cpp` with the Android NDK, checks its object is ELF64/AArch64, and relocatably combines it with the previously audited original client-command object.

The new gate requires:
- `z2026_platform_apply_touch_to_usercmd(usercmd_s*, float*)` to be defined by the platform object.
- The combined object to define `CL_CreateCmd`, `CL_FinishMove`, `CL_MouseMove`, and the touch adapter.
- The touch-adapter symbol to be absent from the combined object's undefined-symbol list.
- Original unresolved dependencies such as `AimAssist_UpdateMouseInput`, `CG_GetPredictedPlayerState`, `CL_KeyMove`, and `CL_CmdButtons` to remain visible rather than be masked by stubs.

The artifact is named `z2026-iw3-client-touch-edge-arm64-NOT-APK`. The step emits `IW3_ORIGINAL_CLIENT_TOUCH_ADAPTER_EDGE_RESOLVED_AARCH64_GREEN`, followed by explicit false flags for runtime invocation, real-map loading, gameplay, and a playable APK.

A new regression checks that the gate actually compiles and links the provider, and that the existing host test invokes the adapter on the authentic `usercmd_s` and verifies movement/buttons plus one-shot view-angle deltas.

## Validation boundary

This phase does **not** link the client into the JNI APK and does not execute `CL_CreateCmd` inside a live game. The Android emulator remains x86_64 and diagnostic. The real filesystem startup, FastFile/map loading, original renderer, live client frame, and physical ARM64 gameplay remain open gates.

No no-op engine callbacks, substitute renderer, Godot, or fabricated gameplay were added. Keep PR #4 open and unmerged until a complete authentic runtime demonstrates a loaded map, rendered scene, touch-driven movement, weapon fire, impacts/damage, and actor behavior on ARM64.
