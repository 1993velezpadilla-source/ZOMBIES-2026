# Phase CL — original CL_CreateCmd touch hook, ARM64 compile gate

**Status at code revision `8a8998913a85e485009b871f577583328e8cd37b`: CI started; runtime integration not claimed.**

The latest source review found that KisakCOD's original `src/client/cl_input.cpp` already has the correct Android-only call to `z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles)` inside `CL_CreateCmd`. It runs after the original `CL_MouseMove` processing and before `CL_FinishMove` encodes the view angles into the command. However, that client translation unit is not part of the diagnostic Android shared-library target, so the hook has not been part of a running Android client.

This phase adds `tools/iw3_android/prepare_real_engine_cl_createcmd.py`. It extracts the exact original `CL_CreateCmd(usercmd_s*)` body, hashes the source and function, and fails if the touch call is missing, duplicated, or ordered outside the original input/finish sequence. The generated source includes the original client state and input headers; no replacement command builder is provided.

The native Android workflow now cross-compiles that extracted body with the Android NDK for ELF64/AArch64 and checks that:
- `CL_CreateCmd(usercmd_s*)` is defined in the ARM64 object.
- `z2026_platform_apply_touch_to_usercmd` remains an explicit external dependency.
- `CL_FinishMove(usercmd_s*)` remains an explicit external dependency.
- The report explicitly keeps `client_runtime_invoked=false` and `playable_apk=false`.

The remaining undefined client calls are intentional evidence that this is a compiled original function, not a linked or executed client. This object is not linked into the JNI diagnostic APK.

Regression coverage: `tests/test_iw3_android_cl_createcmd.py`. The test checks exact source extraction, touch-call ordering, no duplicate hook, and the ARM64 CI gate.

## Validation

At documentation time, the workflow triggered by the new generator/test/workflow changes was still queued or running:
- ARM64 source/module audit: [40798821395](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40798821395).
- Android emulator diagnostic: [40798821259](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40798821259).
- Source preflight for the immediately preceding source/test commit: [40798798044](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40798798044) — PASS.
- An earlier ARM64 attempt at the intermediate revision failed: [40798798066](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40798798066); it is not treated as a pass for the final workflow revision.

This phase does not prove that `CL_CreateCmd` is linked into the app, that a real frame consumes touch state, or that maps, rendering, weapons, actors, or physical ARM64 gameplay work. The next integration gate is to resolve the authentic client-state/input dependencies and connect the compiled command builder to the live client frame without adding no-op stubs. PR #4 remains open and unmerged.
