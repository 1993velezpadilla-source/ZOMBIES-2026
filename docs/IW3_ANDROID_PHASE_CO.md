# Phase CO — resolve original SP keyboard/button command providers for ARM64

**Scope:** stage and cross-compile the authentic `CL_KeyMove`, `CL_UpdateCmdButton`, and `CL_CmdButtons` functions from KisakCOD's SP `src/client/cl_input.cpp`. This is a client-command dependency-edge audit, not a live client or playable APK.

## Baseline inspected

The latest documented branch revision was `2b209f048194ac4dc472c5244b4aa865537a6b9f` (Phase CN documentation). The latest client/touch ARM64 audit had passed, but its combined object still listed these original input providers as undefined:

- `CL_KeyMove(usercmd_s*)`
- `CL_CmdButtons(usercmd_s*)`

The same object also retained genuine client-state and aim-assist dependencies, including `AimAssist_UpdateMouseInput` and `CG_GetPredictedPlayerState`. The Android diagnostic APK does not link or execute the client command loop.

## Implementation

Added `tools/iw3_android/prepare_real_engine_cl_command_helpers.py`. It selects the original `KISAK_SP` branch, extracts the exact original bodies for `CL_KeyMove`, the three-argument `CL_UpdateCmdButton` helper, and `CL_CmdButtons`, and carries over the original key/button macro block and SP stance-suppression state declarations. It hashes the source and each function body, refuses to overwrite the vendored engine source, and reports runtime/gameplay flags as false.

Added `tests/test_iw3_android_cl_command_helpers.py` for source immutability, SP-branch selection, original macro/state/function preservation, refusal to overwrite upstream, and the CI contract.

The native ARM64 workflow now compiles the generated unit with the Android NDK, verifies ELF64/AArch64, and relocatably combines it with the previously audited original client command and touch-adapter object. The gate requires `CL_KeyMove`, `CL_CmdButtons`, their original helper, `CL_CreateCmd`, `CL_FinishMove`, `CL_MouseMove` and the touch adapter to be defined and absent from the combined undefined-symbol list. It deliberately retains `AimAssist_UpdateMouseInput`, `CG_GetPredictedPlayerState`, `CL_StanceButtonUpdate` and `CL_AddCurrentStanceToCmd` as visible unresolved original services rather than supplying stubs.

The artifact is named `z2026-iw3-client-keymove-cmdbuttons-arm64-NOT-APK`. It must never be described as a playable APK.

## Validation boundary

CI for this revision has been triggered by the source/workflow changes; results are recorded after the run completes. A green relocatable link proves only that these provider edges are resolved at object level. It does not execute `CL_CreateCmd` in a live Android client.

Still unproven: full `FS_Startup/FS_InitFilesystem` invocation in the app, genuine FastFile and map loading, original renderer output, live touch-driven client frames, weapon fire/impacts/damage/actor behavior, and execution on a physical ARM64 device. Keep PR #4 open and unmerged. No Godot, substitute engine, no-op callbacks, or fabricated gameplay were added.
