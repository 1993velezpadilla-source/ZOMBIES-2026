# IW3 Android ARM64 phase CW — single-owner filesystem path helper

Date: 2026-10-29

## Review and reproduced blocker

Reviewed PR #4 at head `d7b2959dade9839072c58a8648879f04dc9368d3` before changing the source generator. The latest native ARM64 workflow, [run 40846018333](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40846018333), reached the combined original filesystem link and failed with a real duplicate definition:

`ld.lld: error: duplicate symbol: FS_ConvertPath(char*)`

The linker identified both owners: `iw3_fs_startup.cpp.o` inside `libiw3_sp_fs_startup.a` and `iw3_iwd_names.cpp.o` inside `libiw3_sp_iwd_services.a`. This is an integration defect in the staged original-source slices, not a compiler or NDK installation failure.

At this head, source preflight [40846018198](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40846018198) passed; JNI packaging [40846018236](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40846018236), the x86_64 diagnostic emulator [40846018209](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40846018209), and the Windows SP diagnostic [40846018219](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40846018219) succeeded in their stated scopes. None proves Android gameplay.

## Correction

The original `FS_ConvertPath(char*)` body remains owned by `prepare_real_engine_iwd_names.py`, because the existing native IWD filename/path test executes it and the combined filesystem graph needs that exact upstream provider. The startup generator no longer emits a second body. Original `FS_NewDir_f` call sites are preserved and resolve through the shared IWD-name provider.

Added regression coverage in `tests/test_iw3_android_fs_startup.py` to generate both source slices and verify:
- the startup slice contains the original call site but not a second definition;
- the IWD-name slice contains exactly one original definition;
- generator evidence records the single-owner contract;
- the ARM64 workflow checks exactly one defined symbol and no unresolved reference after the combined link.

The vendored `third_party/KisakCOD/src/universal/com_files.cpp` was not rewritten and no no-op provider was added.

## Validation status

The correction and regression are committed together. A fresh ARM64 run must reach the combined filesystem link and emit:

`IW3_ORIGINAL_FS_CONVERT_PATH_SINGLE_PROVIDER_AARCH64_LINK_GREEN`

Until that fresh run finishes, this phase is **not** considered CI-green. The prior failed run remains evidence of the reproduced defect and is not counted as a pass.



### CI correction checkpoint

The first push after adding the gate, [40854900260](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40854900260), had zero jobs because the first JavaScript replacement inserted a malformed workflow block. The workflow was rebuilt from the clean prior revision and the fixed-string count gate was inserted by exact position in commit `cdf6da9`.

The next native audit, [40856323890](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40856323890), then stopped in source preflight: the new regression read generated files after its `TemporaryDirectory` context had already deleted them. The test now reads both generated files before leaving the context. No ARM64 link success is claimed from either failed run; the next fresh workflow must pass preflight and reach the combined link.

## Scope boundary

Even a successful combined relocatable link does not mean the full Android runtime invokes `FS_Startup`. The diagnostic APK still does not prove a licensed IWD/FastFile/map load, original renderer output, live touch-to-usercmd gameplay, or physical ARM64 execution. No playable APK is claimed. Keep PR #4 open and unmerged.
