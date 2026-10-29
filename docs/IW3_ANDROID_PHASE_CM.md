# Phase CM — resolve the original CL_CreateCmd → CL_FinishMove edge

**Scope:** next incremental integration step for the authentic KisakCOD IW3 client command path. This phase does not claim a live client, map, renderer, gameplay, or playable APK.

## Baseline inspected

The branch's last documented code revision was `d2aa9190c74e21305a0e722fd8561bdd6de2c15d`. The latest native ARM64 audit passed 227 Python tests, CTest Release 23/23, and CTest ASan/UBSan 23/23. The original `CL_CreateCmd(usercmd_s*)` was compiled for AArch64, but its real `CL_FinishMove(usercmd_s*)` call remained unresolved in the relocatable object. The signed JNI package and x86_64 emulator remain diagnostic only.

## Implementation

- Added `tools/iw3_android/prepare_real_engine_cl_finishmove.py`. It extracts the body of the original `CL_FinishMove` from `third_party/KisakCOD/src/client/cl_input.cpp`, hashes the source and body, checks that weapon/offhand/server time/view angles are copied, preserves the original `KEY_FORWARD == 2` angle index, merges and clears extra buttons, and clears forced command state after applying it. It refuses to overwrite the upstream file.
- Added `tests/test_iw3_android_cl_finishmove.py` for source immutability, required original state updates, evidence flags, and the CI gate.
- Extended `.github/workflows/iw3-original-native-android.yml` to compile the extracted original function with the Android NDK, inspect ELF64/AArch64, combine it with the already-compiled original `CL_CreateCmd` using a relocatable link, and require the `CL_FinishMove` edge to resolve.
- The combined object must still show `z2026_platform_apply_touch_to_usercmd` and `CL_MouseMove` as unresolved dependencies. CI prints `IW3_CLIENT_RUNTIME_LINKED=false`, `IW3_CL_CREATECMD_RUNTIME_INVOKED=false`, and `IW3_PLAYABLE_APK=false`. No no-op callbacks were added.

## Validation status

The new preflight, ARM64 compile/link audit, JNI package, and emulator runs were triggered by the workflow update. Their final conclusions are **pending inspection**; no pending run is counted as a pass.

## Remaining gates

The client command chain still has unresolved authentic dependencies such as `CL_MouseMove`, command/key input state, and the live client frame. The app still does not invoke `FS_Startup/FS_InitFilesystem`, mount licensed FastFiles or load a real map, integrate the original renderer, or execute a real frame. A physical ARM64 run with observed movement, weapon fire, hit/damage, and actor behavior remains mandatory before calling the APK playable.
