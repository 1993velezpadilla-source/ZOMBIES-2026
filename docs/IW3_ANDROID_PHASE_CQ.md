# Phase CQ — stage original SP stance helpers for ARM64 client input

## Baseline

Phase CP fixed the ClampChar compile/link edge. The native ARM64 workflow passed at commit `e3fec5a74fbc1f5cc5030a3748b1be93db14ca20`, including the original client-input/touch relocatable link and artifact [12871915693](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40813868507/artifacts/12871915693). That combined object still left CL_StanceButtonUpdate and CL_AddCurrentStanceToCmd unresolved even though the staged CL_KeyMove calls both.

## Implementation

Extended `tools/iw3_android/prepare_real_engine_cl_command_helpers.py` to extract the original `IN_IsTempStanceKeyActive`, `CL_StanceButtonUpdate`, and `CL_AddCurrentStanceToCmd` bodies from the vendored SP `src/client/cl_input.cpp`. The source and each function body are hashed; the generator refuses to overwrite the vendored file. The original key/button macros, stance suppression state, CL_KeyMove, CL_CmdButtons, and CL_UpdateCmdButton remain preserved verbatim.

Updated the NDK workflow to require those three functions as defined symbols and absent from the combined undefined-symbol list. The test now checks that the source bodies are staged and the workflow enforces their resolution. Aim-assist and predicted-player-state remain unresolved original dependencies; no stubs were added.

## Evidence boundary

The expected marker is `IW3_ORIGINAL_CL_STANCE_HELPERS_EDGE_RESOLVED_AARCH64_GREEN`. It proves only that these authentic functions compile into and resolve within the ARM64 relocatable audit object. It does not prove the live client invokes CL_CreateCmd, nor does it prove filesystem startup, FastFile/map loading, renderer output, weapon fire, actor damage, or a playable APK.

## Validation result (2026-10-29)

The follow-up passed CI at commit `42c802a71197508e46fc9cfb3ddad134e37c2c9f`:

- [Source preflight run 40814218610](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40814218610) — success; the regression suite includes the ClampChar and stance-helper checks.
- [Original-source ARM64 audit run 40814218722](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40814218722) — success. Its log contains `IW3_ORIGINAL_CLAMPCHAR_PROVIDER_EDGE_RESOLVED_AARCH64_GREEN` and `IW3_ORIGINAL_CL_STANCE_HELPERS_EDGE_RESOLVED_AARCH64_GREEN`; the required symbols are defined in the combined AArch64 relocatable object and absent from its undefined-symbol list.
- [Artifact 12871831429 — client input/stance object evidence, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40814218722/artifacts/12871831429).

The remaining unresolved client services (including aim-assist and predicted player state) are deliberately visible. The workflow reports client runtime not linked/invoked, real map not loaded, gameplay not proven and playable APK false. Keep PR #4 open and unmerged.
