# IW3 Android Phase FV — authentic SP client state tracking on LP64 (not gameplay)

Date: 2026-10-31. PR #4; branch `feature/iw3-native-android-arm64-20261025`.
Baseline: `d49d8f45e1c4d57a0f30a82e7ce545175016efba`.

## Original engine change

The genuine `third_party/KisakCOD/src/client/cl_main.cpp` contained four static memory-tracker registrations with literal 32-bit Windows sizes: `clientUIActives` (20), `clients` (633532), `clientConnections` (271392) and `cls` (612). These literals are not portable across the Android ARM64 layout, especially for pointer-bearing client/connection state. The original engine now uses its own `TRACK_STATIC_ARR` and `TRACK_STATIC_DAT` macros from `qcommon/mem_track.h`, which compute native `sizeof` values while preserving the same four addresses, names, registration order and memory type 9. This corrects memory-accounting metadata; it does **not** resize or rewrite the client state itself.

## Executed verification

Added `tests/test_iw3_android_client_static_tracking.py` to extract and execute the **authentic** `TRACK_cl_main()` function body with instrumented memory-tracker services under 64-bit AddressSanitizer and UndefinedBehaviorSanitizer. The fixture asserts all four recorded addresses, names, type codes and actual object sizes, and rejects the legacy hard-coded values. The fixture's stand-in client structs are intentionally *not* evidence of the complete production client layout.

Added `.github/workflows/iw3-client-static-tracking-host.yml` with a narrowly scoped CI gate. GitHub Actions run [41221477747](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41221477747) completed **success** at commit `148d4087c677c1b9de12008b7eb24274b1929a7b`. Inspected job `124596760959`: one Python unittest passed, the native ASan/UBSan executable returned successfully, and the marker `IW3_ORIGINAL_CLIENT_STATIC_TRACKING_LP64_PASS` was emitted. The earlier push run [41221472215](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41221472215) also passed.

Other broad Android/Windows CI jobs for this head were still queued or running when checked. This test does **not** prove that the complete original `cl_main.cpp` compiles or links for ARM64.

## Next actual integration barrier

The original `CL_InitRenderer()` **does exist** in `client/cl_main.cpp`; the bootstrap relocatable link lacks its original client translation unit. `CL_InitRenderer()` calls `R_BeginRegistration(&cls.vidConfig)`, screen placement setup, material and font registration, console initialization and client asset setup. Supplying a dummy `CL_InitRenderer` would conceal the real rendering dependency, not solve it. Next prove the full authentic client translation unit's AArch64 compilation and progressively resolve its genuine `R_BeginRegistration`/graphics backend dependencies against an Android rendering implementation. Real game data, map loading, touch-to-client commands, weapon/actor frames and device rendering still require separate end-to-end proof.

`IW3_CL_INITRENDERER_RUNTIME_LINKED=false`; `IW3_RENDERER_FRAME_PROVEN=false`; `IW3_REAL_MAP_LOADED=false`; `IW3_GAMEPLAY_PROVEN=false`; **`IW3_PLAYABLE_APK=false`**.

No Godot or substitute engine was used. Do not merge PR #4 into main.
