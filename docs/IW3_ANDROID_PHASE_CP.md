# Phase CP — resolve the original ClampChar dependency in the ARM64 client-input audit

**Status at commit time:** implementation pushed to the feature branch; CI must validate the updated tree. This is a dependency-edge fix, not a playable APK.

## Latest code and CI inspected first

PR #4 was open and unmerged. The latest head inspected before this change was `facdb76f50c32a10d81473c35f45878dad74dfa4`. The native ARM64 workflow at run [40812606092](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40812606092) failed in the step that cross-compiles the authentic `CL_KeyMove` and `CL_CmdButtons` helpers.

The job log identified three compile errors at the original `ClampChar(forward/side/up)` calls. The staged unit included `client.h`, `cl_input.h`, `q_shared.h` and `msg.h`, but omitted the original declaration from `universal/com_math.h`. The authentic provider body lives in `src/universal/com_math.cpp`:

```cpp
signed char ClampChar(int i) {
    if (i < -128) return -128;
    if (i > 127) return 127;
    return i;
}
```

The vendored body contains braces/comments/formatting exactly as upstream; the excerpt above is only explanatory, not a replacement implementation.

## Fix implemented

- Added `tools/iw3_android/prepare_real_engine_clamp_char.py`, which extracts the original `signed char ClampChar(int i)` body from `com_math.cpp`, verifies the source contract, records source/body SHA-256 hashes, refuses to overwrite upstream and reports all runtime/gameplay flags as false.
- Updated the staged original client-command unit to include `<universal/com_math.h>`, the authentic declaration header.
- Updated the NDK workflow to compile the extracted original provider as ELF64/AArch64 and combine it with the original client-input/touch objects.
- Made the relocatable-link gate require `ClampChar(int)` to be defined and absent from the combined undefined-symbol list. The original aim-assist, predicted-state and stance services remain visible unresolved; no stubs are added.
- Added `tests/test_iw3_android_clamp_char.py` for exact-body preservation, source immutability, refusal to overwrite upstream, and the CI link-gate contract.

## Evidence boundary

The expected marker `IW3_ORIGINAL_CLAMPCHAR_PROVIDER_EDGE_RESOLVED_AARCH64_GREEN` proves only that the original provider compiles for AArch64 and resolves this symbol in the combined relocatable object. It does **not** prove that the live Android client invokes `CL_CreateCmd`, that FS startup or FastFiles/maps load, or that a renderer/gameplay loop runs.

Still required: full original Android bootstrap, genuine IWD/FastFile/map loading, original scene rendering, live touch-driven frames, weapon/impact/damage/actor evidence, and execution of the complete game on a physical ARM64 device. The JNI diagnostic APK is not a game. Keep PR #4 open and unmerged.
