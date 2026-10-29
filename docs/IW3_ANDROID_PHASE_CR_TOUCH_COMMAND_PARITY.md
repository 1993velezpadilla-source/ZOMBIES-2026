# Phase CR — keep touch command snapshots consistent with the original IW3 hook

Date: 2026-10-29

## Baseline and blocker

Reviewed PR #4 at head `fde73fb89854d4b597049ba39f1ab44d9b2b424c` and the completed CI runs for the original-source ARM64 audit, JNI diagnostic, Android emulator diagnostic, and preflight. Those runs were green, but their own evidence correctly states that the original client runtime is not linked or invoked, no real map is loaded, no renderer frame is proven, and the package is not playable.

A native input-contract inconsistency remained in `android/iw3-native/iw3_android_platform.cpp`:

- `z2026_platform_usercmd_snapshot()` directly ORed both `BUTTON_CROUCH` and `BUTTON_PRONE` if both touches were held.
- `z2026_platform_apply_touch_to_usercmd()`, which is the function the original `CL_CreateCmd` Android hook calls, gives prone precedence and clears crouch.

The diagnostic snapshot could therefore report a command that the real hook would not produce. This matters for trustworthy touch-control verification and could conceal stance-combination regressions.

## Change

The snapshot now accumulates `want_crouch` and `want_prone` exactly like the original-hook adapter, then applies the same precedence rule: prone wins and clears crouch; otherwise crouch wins and clears prone. Slide still sets sprint while requesting crouch, so sprint remains active if prone is simultaneously held.

The host-native platform regression now holds crouch and prone simultaneously and asserts both paths:

1. The diagnostic snapshot has `BUTTON_PRONE` set and `BUTTON_CROUCH` clear.
2. Calling `z2026_platform_apply_touch_to_usercmd()` on the actual upstream `usercmd_s` layout produces the same stance bits.

This test executes the real Android platform adapter and the original `usercmd_s` ABI; it does not claim that the Activity invokes the original `CL_CreateCmd` loop.

## Validation

The source/test changes are on PR #4 branch `feature/iw3-native-android-arm64-20261025`. CI is triggered by changes under `android/iw3-native/**`. The relevant native platform CTest and Android ARM64 audit must complete successfully before this pass is considered validated.

Previously completed baseline evidence on `fde73fb`:

- [Original-source ARM64 audit 40914029829](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40914029829) — passed; audit-only objects and unresolved service boundaries are recorded.
- [JNI diagnostic 40914029822](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40914029822) — passed; not a playable APK.
- [Android x86_64 emulator diagnostic 40914029789](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40914029789) — passed; native input adapter and lifecycle only, not the live client/frame loop.

## Explicit remaining gates

- The Android Activity still calls the diagnostic usercmd snapshot, not original `CL_CreateCmd`.
- The original client/server runtime is not linked and invoked in Android.
- No real licensed FastFiles/map load has been demonstrated.
- No frame from the original renderer has been demonstrated.
- No physical ARM64 gameplay with weapons, damage and actors has been demonstrated.

Do not merge PR #4 while these gates remain open. No diagnostic APK is a playable-game deliverable.
