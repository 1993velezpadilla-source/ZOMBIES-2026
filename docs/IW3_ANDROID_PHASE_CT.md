# Phase CT — fix shared aim-assist state edge on Android ARM64

## Baseline and failure found

Inspected PR #4 at branch head `86cdda61d481bb13d4f386eed037a076f12eca0b` and its CI before changing code. The source preflight and JNI diagnostic build passed, but the original-source ARM64 workflow failed in the step that compiles the generated aim-assist tweakable providers (run [40827860431](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40827860431)).

The compiler error was concrete: `aaGlobArray` was undeclared in the generated `AimAssist_UpdateTweakables` and `AimAssist_UpdateAdsLerp` translation unit. The authentic `AimAssistGlobals aaGlobArray[1] = { 0 };` definition already belongs to the separately generated client-state provider; the tweakables unit must reference that shared state rather than define another copy.

## Correction

- Added the explicit declaration `extern AimAssistGlobals aaGlobArray[1];` to the generated aim-assist provider's include surface.
- Kept the one original definition in `prepare_real_engine_client_state_providers.py` / its generated client-state object.
- Extended the generator's evidence report to record that the array is externally declared and owned by the client-state provider.
- Added regression coverage proving the tweakables translation unit declares but does not define the array.
- Strengthened the NDK link gate: it now requires `aaGlobArray` to be undefined in the helper object, defined by the combined client-state object, and absent from the combined undefined-symbol list.

No function stubs were added and no vendored engine source was overwritten.

## Validation status

The corrective commits have been pushed to `feature/iw3-native-android-arm64-20261025`. CI for this exact new head must finish before this correction is called validated. The prior run's JNI and x86_64 emulator successes do not validate the failed ARM64 aim-assist compile.

## Explicit limits

This resolves a compile/link ownership defect only. Aim-assist dvars are still not registered, CGame state is not initialized by a live Android client, and the object audit is not linked into the diagnostic APK. The original auto-melee, melee-charge, assertion, and screen-placement dependencies remain intentionally unresolved. No authentic map load, original renderer, touch-driven live client frame, combat, physical ARM64 gameplay, or playable APK has been demonstrated.

PR #4 must remain open and unmerged until the original runtime, map, renderer, controls, weapons/actors and physical ARM64 execution are proven.
