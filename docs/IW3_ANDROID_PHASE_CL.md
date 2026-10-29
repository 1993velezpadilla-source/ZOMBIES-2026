# Phase CL — original CL_CreateCmd touch hook, ARM64 compile gate

**Validated code revision: `d2aa9190c74e21305a0e722fd8561bdd6de2c15d`. The original CL_CreateCmd body now cross-compiles for Android ARM64; it is still not linked into or invoked by a live client runtime.**

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

The final source revision `d2aa9190c74e21305a0e722fd8561bdd6de2c15d` passed the native ARM64 workflow:
- Source preflight: [40799653535](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653535) — PASS.
- ARM64 native audit: [40799653566](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653566) — PASS; 227 Python tests, CTest Release 23/23, CTest ASan/UBSan 23/23.
- JNI Android diagnostic build: [40799653491](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653491) — PASS, diagnostic only.
- Native artifact [12864594953](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653566/artifacts/12864594953) contains the ELF64/AArch64 object and reports. It is **not an APK**.
- JNI artifact [12865720936](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653491/artifacts/12865720936) is the signed diagnostic package, **not a playable game**.

The first cross-compile attempt exposed two real header portability blockers: Win32-only Direct3D resource layout assertions were pulled in through `client.h`, and after isolating that include the original `clientStatic_t` declaration still needed the authentic `clientDebug_t` field types. The Android-only client-header path now avoids importing the Win32 renderer ABI while preserving the original debug-state member order and native pointer-bearing fields needed to declare the real client state. The generated original command builder now compiles; the earlier failed attempts are not counted as passes.

The passing object defines `CL_CreateCmd(usercmd_s*)` and retains `z2026_platform_apply_touch_to_usercmd` and `CL_FinishMove(usercmd_s*)` as external dependencies. CI explicitly emits `IW3_CL_CREATECMD_RUNTIME_INVOKED=false` and `IW3_PLAYABLE_APK=false`.

This phase does not prove that `CL_CreateCmd` is linked into the app, that a real frame consumes touch state, or that maps, rendering, weapons, actors, or physical ARM64 gameplay work. The next integration gate is to resolve the authentic client-state/input dependencies and connect the compiled command builder to the live client frame without adding no-op stubs. PR #4 remains open and unmerged.
