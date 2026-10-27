undefined

### Phase O — share original file-system globals (26 Oct 2026; native ARM64 and JNI builds passed)

The next duplication after Phase N was the global state used by the authentic search-path, game-directory and IWD-index functions: `fs_searchpaths`, `fs_gamedir`, `fs_iwdFileCount`, `fs_checksumFeed`, and `bLanguagesListed`. The original `com_files.cpp` defined these, while the Android staging generators also emitted private copies. Phase O moves the single zero-initialized definitions to `src/universal/com_files_state.cpp`, declares the missing externs in the original `com_files.h`, and includes the state source in both the common KisakCOD source list and the Android diagnostic targets.

The search-path, directory and IWD-service generators now validate the shared state source and no longer emit duplicate definitions. Their function bodies are still extracted verbatim from the vendored engine. Tests assert one definition, the original declarations, both build-system inclusions and the absence of diagnostic-owned copies.

This is still not the complete filesystem runtime: Android continues to compile selected original function bodies with narrow platform adapters rather than the entire `com_files.cpp` translation unit. It does not prove loading licensed FastFiles/maps, renderer output, physical ARM64 execution or gameplay. On code commit `e58ed58b6e9a4050a9e7a02633bbbc7e21a1d0ca`, source preflight `40360710511` passed; native ARM64 build `40360710429` passed host/ASAN/UBSAN tests, AArch64 ELF compilation, IWD indexer audit and the original frame-entity compile; JNI integration `40360710592` passed ARM64 compilation, packaging and signature validation (artifact `12668021667`, explicitly NOT A GAME). The x86_64 emulator runtime proof `40360710674` and Windows dedicated compilation `40360710464` were still running when this note was updated. The emulator is not physical ARM64 gameplay evidence; PR #4 remains open and unmerged.

### Phase P — native-width string dvar pointers in the original filesystem (26 Oct 2026; validation pending)

A source audit found a genuine 32-bit-to-64-bit portability defect in the vendored `src/universal/com_files.cpp`: string-valued dvars (`fs_homepath`, `fs_basepath`, `fs_cdpath`, `fs_basegame`, `fs_gameDirVar`) were repeatedly read through `current.integer` and cast to `char *`. On a 64-bit ABI, `integer` is not the pointer-bearing union member and can truncate the path pointer. This affects `FS_Startup`, `FS_InitFilesystem`, the original `FS_FOpenFileReadForThread` copy path, and filesystem write/delete/rename helpers.

The original engine source now reads these values through `current.string`; startup's first-character tests use explicit `current.string[0] != '\0'`. Numeric uses such as `fs_debug->current.integer` remain numeric. No replacement filesystem implementation was introduced.

- Engine fix: `631a556db54131f6748a605320ce93709ab2343f`.
- Explicit string-presence check cleanup: `931e58f2971cb3541c263cb7c28c879ed90b4d74`.
- Regression coverage: `tests/test_iw3_android_string_dvar_abi.py` (added in `9667606ba766c57900395e2671171f21770f9e80`, expression corrections through `3ff3437f170314c9758c80093f112144cce7f2c9`). It forbids all five string dvars from being read via `current.integer`, checks the original startup/open/init code, and ensures numeric `fs_debug` remains numeric.

**Validation status at documentation time:** the new regression and the platform build workflows have been triggered by the branch updates; their final results have not yet been inspected. Do not count this pass as CI-green until the relevant Actions runs finish.

**Scope boundary:** this fixes pointer-width correctness in the authentic filesystem source, but it does not itself execute `FS_Startup` in the Android runtime. The JNI app still stages selected original function bodies with narrow platform adapters; it does not link the full original `com_files.cpp`, load licensed FastFiles/maps, render a game scene, or execute complete player/weapon/actor gameplay. No playable APK is claimed; PR #4 remains open and unmerged.

### Phase Q — preserve the filesystem base-path reset string on 64-bit Android (26 Oct 2026; CI pending)

A follow-up audit after Phase P found one remaining pointer-width defect in the original `FS_InitFilesystem`/dvar-registration path: `homePath = (char *)fs_basepath->reset.integer;`. Unlike the already-corrected `current.string` accesses, this cast reads the reset value through the 32-bit integer union member. On a 64-bit ABI it can truncate the default base path before `fs_homepath` is registered. The original engine now reads `fs_basepath->reset.string`; no replacement filesystem path logic was added.

- Engine fix: commit 8300729462798cc9ff5dfd006ac753e1b0e24784.
- Regression extension: commit 2d5391e6dfeef04cd52364e8717f1bf879375d6f; the ABI test now rejects both `current.integer` and `reset.integer` pointer reads for the five string-valued filesystem dvars, and explicitly asserts that the home-path default uses `reset.string`.

**Validation update (26 Oct 2026):** source/RotU preflight [40378477849](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378477849) passed on the current branch head. The Android ARM64 source/module workflow [40378464214](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464214) passed its host tests/sanitizer checks, original math ELF64/AArch64 link, original `G_RunFrame` compile and IWD-indexer archive checks. JNI integration [40378464250](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464250) passed ARM64 native compilation, APK packaging/signature validation and uploaded artifact [12677006919](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464250/artifacts/12677006919), explicitly a diagnostic APK, not a game. The x86_64 emulator runtime [40378464077](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464077), Windows SP compile [40378477542](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378477542), and Windows SP runtime [40378477580](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378477580) were still in progress at the time of this update. The emulator is x86_64 and diagnostic-only.

**Scope boundary:** the pointer fix is in the authentic KisakCOD source, but `FS_Startup`/the full `com_files.cpp` is still not linked into the Android game runtime. No real FastFiles/map load, renderer scene, touch-driven player combat, or physical ARM64 gameplay is proven. Keep PR #4 open and unmerged.


### Phase Q runtime follow-up — original IWD read lifecycle and touch adapter observed (26 Oct 2026)

The Android x86_64 emulator workflow [40378464077](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464077) completed successfully after the source/test revision. Its log reports the original IWD parser, mount, search-path insertion, game-directory scan/registration, search-path lookup, IWD read branch, open/read/close lifecycle, cloned-handle path, and directory fallback read as executed. It also records real Android touch DOWN/UP events translated to the original `usercmd_s` adapter, plus activity pause/resume. The evidence archive is [12678395538](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378464077/artifacts/12678395538).

**Hard limits in that same validator:** `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. The runtime is x86_64 and uses synthetic IWD fixtures; it is not a map-rendering or gameplay test. The Windows SP compile/runtime workflows [40378477542](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378477542) and [40378477580](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40378477580) were cancelled by workflow concurrency and are not counted as passing for Phase Q. No playable APK is claimed; keep PR #4 open and unmerged.


### Phase R — native-width temporary searchpath allocation (26 Oct 2026; CI pending)

A follow-up ABI audit found two hard-coded allocations in the original `FS_ListFilteredFilesInLocation()` body: `Hunk_UserAlloc(user, 0x1Cu, 4)`. The value `0x1C` is the Win32 `searchpath_s` size (28 bytes). On a 64-bit ABI, `searchpath_s` is 40 bytes and requires 8-byte alignment. These temporary nodes could therefore be undersized and under-aligned on Android ARM64.

The authentic engine source now allocates both nodes with `sizeof(searchpath_s)` and `alignof(searchpath_s)`. No replacement list/filter implementation was introduced. The shared layout gate now asserts native and Win32 sizes/offsets for `fileInIwd_s`, `iwd_t`, and `searchpath_s`, alongside the existing file-handle ABI checks. The corresponding structure comments in `com_files.h` now label the old hexadecimal sizes explicitly as Win32-only.

Regression coverage: `tests/test_iw3_android_native_struct_allocations.py` verifies both allocation sites use native size/alignment and that the expected 32/64-bit structure layouts remain guarded.

**Validation status:** the source changes and new tests have been pushed to the feature branch; the Android ARM64 compile, JNI packaging, x86_64 diagnostic runtime and Windows source/runtime workflows have been triggered by the engine-source update. Do not count this pass as green until the new runs finish.

**Scope boundary:** this corrects a real 32/64-bit heap-layout bug in the original filesystem source and makes the relevant structure layouts explicit. It does not integrate the complete `com_files.cpp` translation unit into the Android game runtime, load licensed FastFiles/maps, render a real scene, or prove touch-driven gameplay on a physical ARM64 device. The JNI package remains diagnostic only. Keep PR #4 open and unmerged.


### Phase S — compile the original location-filter function for native 64-bit ABI (26 Oct 2026)

The next portability gate now compiles the complete vendored `FS_ListFilteredFilesInLocation()` body from `com_files.cpp` into a separate static audit archive for both host and Android ARM64. The extractor preserves the original function body verbatim and checks that both temporary `searchpath_s` nodes use `sizeof(searchpath_s)` and `alignof(searchpath_s)`, not the historical Win32 allocation size.

The archive is deliberately not linked into JNI. Its original `Hunk_UserCreate`, `Hunk_UserAlloc`, `Hunk_UserDestroy`, `FS_CheckLocation`, `FS_ListFilteredFiles`, and `MyAssertHandler` dependencies remain unresolved and are checked with `llvm-nm`. This provides a real compiler/ABI check for the corrected function rather than only a source-regex test.

New files:
- `tools/iw3_android/prepare_real_engine_filtered_files.py`
- `android/iw3-native/iw3_android_filtered_files_compat.h`
- `tests/test_iw3_android_filtered_files_compile.py`

The native ARM64 workflow generates the original source slice, compiles the archive in host and AArch64 configurations, checks the defined function and required unresolved engine services, and uploads the archive plus extraction report.

**Scope boundary:** compilation does not mean the function has run against the real shared searchpath list. The complete filesystem startup, licensed FastFiles/map loading, renderer output, physical ARM64 execution, and touch-driven gameplay remain unproven. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.


### Phase S runtime follow-up — make the diagnostic touch surface accessibility-visible (26 Oct 2026)

The new native ARM64 compile audit passed, but the concurrently triggered x86_64 emulator diagnostic failed after the original JNI functions had passed: `run_emulator_probe.sh` could not find the full-screen TextView in UIAutomator's accessibility hierarchy. The failure occurred in the touch-target discovery step, after the log had already reported the ZIP parser, IWD searchpath, directory scan, file-read lifecycle and JNI activity pass markers; it is not evidence of gameplay.

The diagnostic activity now explicitly sets a stable content description, focusability, clickability and `IMPORTANT_FOR_ACCESSIBILITY_YES` on its actual full-screen TextView. The probe selector accepts that stable content-description node as well as the TextView class. This keeps the test tied to the visible application view rather than silently falling back to an arbitrary coordinate.

The retry is pending. Even if the diagnostic passes, it remains an x86_64 emulator test of original component slices, not physical ARM64 gameplay or a playable APK.

### Phase T — make the filtered-files ARM64 audit fail closed (26 Oct 2026; CI pending)

The previous pass staged and compiled the original `FS_ListFilteredFilesInLocation()` body into `libiw3_sp_filtered_files.a`, but the ARM64 workflow did not inspect that archive's symbol table. That meant the source could theoretically stop being built or lose the intended unresolved engine-service boundary without the explicit post-build audit catching it.

The native ARM64 workflow now requires the archive to exist, verifies that it defines the original `FS_ListFilteredFilesInLocation` symbol, and verifies that the authentic Hunk allocation and file-list services remain unresolved. This makes the compile evidence fail closed while also making clear that this is still a component audit, not a linked filesystem runtime.

- CI workflow change: commit `10425f7553e63392359cde8c931e1583692de9f0`.
- Expected marker: `IW3_ORIGINAL_FILTERED_FILES_AARCH64_SYMBOL_AND_SERVICE_AUDIT_GREEN`.
- Validation update (26 Oct 2026): native ARM64 run [40400263349](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40400263349) passed the fail-closed symbol/service audit, including the defined original location-filter symbol and unresolved Hunk/file-list services. The later run [40401446714](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446714) passed the same audit after adding the base `FS_ListFilteredFiles()` function to the archive.

**Scope boundary:** this change adds no gameplay implementation and does not link `FS_Startup()`, the full `com_files.cpp`, FastFile/map loading, renderer output, or player/weapon/actor simulation into Android. It only strengthens verification of the original filtered-files function's AArch64 object archive. The diagnostic APK remains not a game; PR #4 remains open and unmerged.


### Phase U — preserve native-width pointers in the original game-directory validator (26 Oct 2026; CI pending)

A further 64-bit defect was found in the authentic `FS_GameDirDomainFunc()` callback in `src/universal/com_files.cpp`. It read the string-valued `DvarValue` through `newValue.integer`, dereferenced the pointer via the 32-bit integer member, and cast `strstr()` results back to `int`. On Android ARM64 those operations can truncate a valid path pointer and misclassify a game-directory value.

The original callback now consistently uses `newValue.string` for its first-character check, separator validation, and traversal-token checks. The `strstr()` results are tested as pointers, not narrowed integers. The existing validation policy is preserved: an empty value is allowed; non-empty values must start with `mods`, contain a slash or backslash after the prefix, and contain neither `..` nor `::`. No replacement validator was added.

- Engine fix: commit `0605df9ff811905330bee3fcb705db0812dd958f`.
- The original callback body is now included in the exact-source extraction used by the Android native build, so it is compiled with the 64-bit Android ABI alongside the original file lifecycle helpers: `34676d682ee63830e90bc4f95f105cca6f067ced`.
- Regression coverage rejects any `newValue.integer` access or `(int)strstr` narrowing in this callback and checks that the staging generator preserves it: `a04170e71c12ce7a1191410e5efb417349ba016a`, `0d6742e769860feeb957a526101dee669a4984a4`.

**Validation update (26 Oct 2026):** native ARM64 run [40400263349](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40400263349) passed 65 Python regressions, host checks/sanitizers and the AArch64 compile audit containing the original callback. JNI integration [40400263060](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40400263060) passed ARM64 compilation, APK packaging and signature verification; its artifact is explicitly named `NOT-A-GAME`. The x86_64 diagnostic emulator run [40400263231](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40400263231) completed successfully on the preceding source revision, but it uses selected original function slices and synthetic fixtures, not real map loading or gameplay. The callback itself is compiled but not runtime-executed by that probe. Full `FS_Startup()`/`com_files.cpp`, real FastFiles/maps, renderer output, and physical ARM64 player/weapon/actor gameplay remain unproven. PR #4 stays open and unmerged.


### Phase V — native-width allocation for the original filtered-file pointer list (26 Oct 2026; CI pending)

The next filesystem blocker was a hard-coded allocation in the authentic `FS_ListFilteredFiles()`: `Hunk_UserAlloc(user, 0x8004u, 4)`. The value `0x8004` reserves 8193 four-byte pointer slots, matching the original `0x1FFF` result cap plus the sentinel and final null entry. On ARM64, those slots require 8193 eight-byte pointers (65544 bytes, `0x10008`), with pointer alignment. Leaving the Win32 byte count unchanged would let the real file-list builder overrun its allocation.

The original function now computes the same slot count using `(0x1FFFu + 2u) * sizeof(*list)` and `alignof(const char *)`. On Win32 this retains the original `0x8004` allocation; on ARM64 it grows to `0x10008`. The result cap and original duplicate-filtering/list behavior are unchanged.

The filtered-files ARM64 audit now compiles both original `FS_ListFilteredFiles()` and `FS_ListFilteredFilesInLocation()` from the vendored source into the same static audit archive. The fail-closed symbol audit expects the list function to be defined in that archive and checks that its real Hunk, filename-sanitization, path-return, and OS-directory-listing services remain unresolved. The archive is still deliberately not linked into JNI.

Regression coverage:
- `tests/test_iw3_android_native_struct_allocations.py` checks the native allocation expression and proves the old result capacity maps to 32772 bytes on 32-bit and 65544 bytes on 64-bit.
- `tests/test_iw3_android_filtered_files_compile.py` checks that both original function bodies are preserved in the generated source, that the new pointer-array allocation is present exactly once, and that the fixed `0x8004u` allocation is absent.

**Validation update (26 Oct 2026):** native ARM64 run [40401446714](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446714) passed 66 Python regressions, host checks/sanitizers and the AArch64 archive audit. The archive defines both `FS_ListFilteredFiles()` and `FS_ListFilteredFilesInLocation()`; original Hunk, sanitizer, path and OS-listing services remain unresolved by design. Audit evidence: [12688218194](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446714/artifacts/12688218194), not an APK. JNI integration [40401446845](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446845) passed the 66-test suite, ARM64 compilation, packaging and signature verification; its artifact [12688817886](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446845/artifacts/12688817886) is explicitly NOT A GAME. The x86_64 diagnostic emulator run [40401446788](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446788) also passed and recorded original component slices executing, touch DOWN/UP reaching the original `usercmd_s` adapter, and pause/resume; evidence [12689507711](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446788/artifacts/12689507711). That emulator still reports `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. The real list function itself remains compile-audited rather than executed against a mounted game filesystem. Full `FS_Startup()`, FastFile/map loading, renderer scene, touch-driven combat and physical ARM64 gameplay remain unproven. No playable APK is claimed; PR #4 remains open and unmerged.


### Phase U — native touch mapping for sprint and slide chord (26 Oct 2026; CI pending)

The Android touch adapter previously had no touch role that emitted the original `BUTTON_SPRINT` bit, even though the original `usercmd_s` layout and the Android-only `CL_CreateCmd` hook already existed in vendored `cl_input.cpp`. Added two dedicated lower-left touch zones to the adapter: sprint at `x < 0.18, y >= 0.76`, and a slide chord at `0.18 <= x < 0.38, y >= 0.76`. The slide chord emits sprint plus crouch; it does **not** claim that the stock IW3 game logic already implements a slide mechanic.

Both `z2026_platform_usercmd_snapshot()` and `z2026_platform_apply_touch_to_usercmd()` now map these roles to the original `usercmd_s` bits. The host C++ platform test now verifies simultaneous sprint/slide/jump, verifies that releasing slide leaves a still-held sprint active, and exercises the actual original-layout `usercmd_s` mutation path rather than only reading the side snapshot.

- Adapter change: `55d7d6d11a3ac2b81d9f853e740e1b93cbf5f6cf`.
- Host regression and final touch-release assertion: `6fdd4270a4b883cf4dcff405eb8f3c2181424e88`.
- Native ARM64 workflow [40407719927](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407719927) passed source preflight, host CTest, ASan/UBSan and AArch64 source/archive checks. Its artifact [12691831689](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407719927/artifacts/12691831689) is a compiled native module, **not an APK**.
- JNI ARM64 compile/package/signature workflow [40407720076](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407720076) passed. Its artifact [12690894283](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407720076/artifacts/12690894283) is the **diagnostic APK, not a playable game**.
- Android x86_64 emulator runtime workflow [40407719931](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407719931) passed; runtime logs are in artifact [12692016585](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40407719931/artifacts/12692016585). This proves execution on an x86_64 emulator only, not ARM64 device gameplay.

**Scope boundary:** the touch bridge is still not called by a live game frame in the Android APK. The vendored original `cl_input.cpp` hook is not yet integrated into the Android shared-library target; the current APK remains a JNI diagnostic. This change does not prove `FS_Startup()`, FastFile/map loading, rendering, weapons/actors in gameplay, or physical ARM64 gameplay. PR #4 remains open and unmerged.


### Phase V — real Android emulator proof for sprint/slide touch commands (26 Oct 2026)

Extended the emulator probe to inject real Android touchscreen taps into the lower-left sprint zone and slide-chord zone, then inspect the native `usercmd_s` snapshot logged by `MainActivity`. The runtime verifier now fails unless it observes all three distinct command states: attack (`buttons=1`), sprint (`buttons=2`), and sprint+crouch slide chord (`buttons=514`). The Python evidence fixture was updated to use the new native coordinates; the first run caught a stale-coordinate test replacement, which was corrected before the green run.

Final verification on code commit `88b1383ac9aff85528a573bcb5fa44df179afc0e`:
- Native ARM64 source workflow [40408851760](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851760): **67 Python tests passed; 8/8 host CTest tests passed in Release and again under ASan/UBSan; AArch64 source/archive checks passed.** Artifact [12691578771](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851760/artifacts/12691578771) is a native module, not an APK.
- Android x86_64 emulator runtime [40408851767](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851767): **passed**. Its log contains `IW3_JNI_USERCMD attack=0 buttons=2`, `IW3_JNI_USERCMD attack=0 buttons=514`, and `IW3_JNI_USERCMD attack=1 buttons=1`; evidence artifact [12692287332](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851767/artifacts/12692287332).
- Android ARM64 JNI build/package/signature [40408851800](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851800): **passed**. Artifact [12691908671](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408851800/artifacts/12691908671) remains a diagnostic APK, explicitly not a playable game.
- Source preflight [40408861841](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40408861841): passed.

**Interpretation limit:** this proves Android touch coordinates reach the native adapter and produce the expected original-layout command bits. It does not prove that a live original client frame consumes them: `cl_input.cpp` is still absent from the Android shared-library target, and the JNI activity does not run `CL_CreateCmd`/`Com_Frame`. The stock engine's slide gameplay is also not implemented merely by emitting the sprint+crouch chord. No real FastFile/map, renderer, weapon/actor combat, or physical ARM64 gameplay is proven. PR #4 remains open and unmerged.


### Phase W — native-width client command queue and original input TU on Android (26 Oct 2026; CI pending)

The next client-side portability seam is the original `CL_CreateNewCommands()` path. It copied each `usercmd_s` through a hard-coded `_BYTE v1[56]` stack buffer, then copied that buffer into the command ring. The command record is a typed engine structure; the temporary Win32-sized byte array is unnecessary and can silently truncate a future/native-width layout.

The authentic `third_party/KisakCOD/src/client/cl_input.cpp` now constructs the command in a `usercmd_s` object and copies `sizeof(command)` into the selected original `clients[0].cmds` slot under the existing client-command critical section. The command index is evaluated once into `nextCommand`. This preserves the original command creation, ring index, and lock ordering while removing the fixed 56-byte intermediate copy.

An experimental Android CMake target was added to compile the original SP `cl_input.cpp` as `libiw3_sp_client_input.a` with the NDK ABI and audit the `CL_CreateCmd(usercmd_s*)` / `CL_CreateNewCommands()` symbols. The experiment exposed the Win32/D3D header boundary described in Phases X–Y; the target and archive audit were subsequently removed from the default Android workflow rather than leave CI red. The current workflow does not claim this translation unit is built or linked.

Regression coverage in `tests/test_iw3_android_client_input_abi.py` checks the native-size queue copy, original call ordering, and build/audit scope boundary.

- Engine fix: `58ff84f2658c1ce21dd9d5719dd3cdf04a260ff7`.
- Android CMake client-input target: `0db9a79eac3e67a998bd66b42ac08802969510f7`.
- ARM64 symbol-audit workflow: `bcbedfa66cc061f45599f6f77190b1929a6f7baf`.
- Regression test: `c41d1f684e6ec2e01f4a9ae8b2de439008f01087`.

**Validation status at documentation time:** the ARM64 source workflow, JNI build and emulator diagnostic have been triggered for the new head; their final conclusions have not yet been inspected. Do not count this phase as green until those runs complete.

**Scope boundary:** compiling the original client input translation unit and correcting the command queue's typed copy does not make the touch bridge live in the APK. The archive is not linked into the diagnostic, and this phase does not execute `CL_CreateCmd` from an Android game frame. Full `Com_Frame`, `FS_Startup`, licensed FastFile/map loading, renderer output, weapon/actor gameplay and physical ARM64 execution remain unproven. No playable APK is claimed; PR #4 remains open and unmerged.


### Phase X — first native-layout blockers exposed by compiling original client input (26 Oct 2026; ARM64 CI pending)

The first Android NDK compile of the original `client/cl_input.cpp` did not reach the symbol audit. It exposed real Win32-only assumptions in headers that the client module pulls in:

- MSVC-only `__declspec(align(...))` declarations in script-memory, script-string and UI parser structures prevented Clang/NDK parsing.
- Several engine structures that contain native pointers still asserted their 32-bit Win32 sizes. The compiler reported the actual 64-bit sizes for animation/script and combat/view structures, including `scr_anim_s`, `loadAnim_t`, `animStringItem_t`, `animConditionTable_t`, `shellshock_t`, `animScriptCommand_t`, `CEntPlayerInfo`, `CEntFx`, `BulletTraceResults`, `viewState_t`, and `weaponState_t`.

Corrections made in the authentic KisakCOD headers:
- Replaced the affected alignment spellings with standard C++ `alignas`, preserving the required 8-byte/128-byte alignment.
- Kept the original Win32 layout assertions on 32-bit builds and added explicit LP64 assertions for the pointer-bearing layouts measured by the Android compiler. These checks do not change the 32-bit game layout.
- During this experiment the temporary Android target attempted to compile the actual original `cl_input.cpp`; it was later removed after the D3D/client-header dependencies proved to require a broader port. No replacement input or game loop was added.

Related commits:
- `6599d6be1e777b1dd8d037589549e6ac758571cb` — standard alignment for script memory tree.
- `9e40adf6c236c553d2a39393164d744ae8fbe43b` — standard alignment for script string table.
- `f976be672b418ec49f23b67a352e6ffc18d250df` and `901c5bb950c1039242b8eb08a325b352bb357e84` — LP64 animation/script layout assertions.
- `b8bb2bda311f576c247f7384d6918a3d233f4bad` — LP64 entity/weapon result layouts.
- `696fbc7cef24110ffcd8512fc20715e3bc131ff0` — LP64 font pointer layout.
- `29794fc46586dc0110d3e855a505d0c0f15b1f9f` — standard alignment for UI parser structures.

**Validation update (26 Oct 2026; code commit `c835c01aed938525d791054064e81578e0286623`):**
- Native ARM64 source workflow [40418049229](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049229) passed: 71 Python tests, CTest 8/8 in Release, CTest 8/8 under ASan/UBSan, ARM64 filesystem/IWD symbol audits, and the original `G_RunFrame` entity block compile. Artifact [12697265311](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049229/artifacts/12697265311) is a native-module/evidence archive, **not an APK**.
- JNI packaging workflow [40418049373](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049373) passed 71 tests and Gradle build. Artifact [12697345288](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049373/artifacts/12697345288) is explicitly diagnostic, **not a game**.
- Android x86_64 emulator proof [40418049246](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049246) passed. Its report confirms original IWD/filesystem fixture functions executed and touch reached the original `usercmd_s` adapter, but also records `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. Evidence artifact [12696755465](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40418049246/artifacts/12696755465) is a runtime log/evidence archive, **not a game**.

These green runs do not compile or link the full `cl_input.cpp` translation unit: that experiment was removed from the default build after exposing the D3D/client-header boundary. No original client-input archive is claimed.

**Scope boundary:** these changes address actual 32/64-bit header portability blockers but do not link the original client input into the APK or run `CL_CreateCmd` in a live Android game frame. `Com_Frame`, `FS_Startup`, FastFile/map loading, renderer output, weapons/actors in Android gameplay and physical ARM64 execution remain unproven. No playable APK is claimed; PR #4 remains open and unmerged.


### Phase Y — boundary of the client-input compile experiment (26 Oct 2026)

The next compile after the LP64 layout fixes exposed a broader dependency boundary. The original `cl_input.cpp` includes `cgame/cg_main.h` / `cg_local.h`, which in turn pull the D3D9 renderer through `gfx_d3d/r_gfx.h`. The NDK has no `d3d9.h`. Other compile errors also show that the full client/UI header graph still contains Windows-only types and pointer-width assumptions (`clientDebug_t`, `refdef_s`, `__forceinline`, `FxEffectDef`, `FxImpactTable`).

I removed the experimental `iw3_sp_client_input` target and its archive audit from the default Android workflow rather than leaving the branch with a knowingly failing build or reporting a non-linked object as integration. The failed run remains visible as evidence: [ARM64 attempt 40417087767](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40417087767). The source-level command queue correction and regression test remain in place; the header portability fixes remain limited to standard alignment and explicit LP64 layouts. The D3D/client header graph is now documented as the next integration blocker.

**Next actual integration requirement:** establish a renderer-neutral client header boundary and port the original client/cgame input dependencies without inventing substitute state. Only then can the original `CL_CreateCmd` be linked into the Android runtime and called from its frame loop. The current JNI diagnostic remains separate and does not call it.

**Scope boundary:** this experiment did not produce a playable APK. No Android game-frame execution, real map rendering, FastFile/map load, combat, or physical ARM64 gameplay is proven. PR #4 remains open and unmerged.


### Phase Z — bind original filesystem startup defaults to Android filesDir (26 Oct 2026; CI pending)

The next real blocker after the IWD lookup/read fixtures is the original startup entry point. FS_RegisterDvars() obtains its base path from Sys_Cwd() and its CD path from Sys_DefaultCDPath(). A process working directory is not a valid Android game-data contract, so this pass adds a narrow POSIX service that returns the app-private filesDir configured by nativeSetDataRoot, and returns an empty CD path. The root getter fails closed when the root is unset or the destination buffer is too small; native tests check exact path round-trip and NUL termination.

The same pass adds a source-provenance generator for the original FS_RegisterDvars, FS_Startup, FS_SetRestrictions, FS_IsBasePathValid, and FS_InitFilesystem bodies from third_party/KisakCOD/src/universal/com_files.cpp. The native ARM64 workflow compiles them into a separate static dependency-audit archive and checks both their definitions and the unresolved original Dvar/filesystem/language services. The JNI diagnostic now exercises the real Android path-default adapter and requires IW3_JNI_FS_STARTUP_PATH_PASS in the emulator evidence.

This is deliberately NOT yet an invocation of FS_Startup. The original Dvar registry, Com_StartupVariable, language initialization, and the full com_files.cpp service graph are not linked. The archive is not linked into the JNI APK. No licensed FastFile or real map is loaded, no renderer or gameplay is running, and physical ARM64 execution remains unproven.

- New source extraction: tools/iw3_android/prepare_real_engine_fs_startup.py with body hashes and explicit false runtime/gameplay fields.
- Android path adapter: android/iw3-native/iw3_android_fs_startup_io.cpp.
- Root getter and regression: z2026_platform_copy_data_root, platform_native_test.cpp, and tests/test_iw3_android_fs_startup.py.
- CI audit marker: IW3_ORIGINAL_FS_STARTUP_AARCH64_DEPENDENCY_AUDIT_GREEN (pending for this head at documentation time).

Scope boundary: this is a real startup prerequisite and a compile/dependency gate, not a playable APK. Keep PR #4 open and unmerged until original startup is actually called in a linked runtime, the genuine licensed assets/map load, renderer output appears, and touch drives original player/weapon/actor gameplay on ARM64.


## Phase AA — original dvar pointer-width and callback ABI repair (2026-10-26)

The next blocker exposed while tracing `FS_RegisterDvars` into the real filesystem startup path was in the vendored original `src/universal/dvar.cpp`, not in the JNI bridge. Several Win32-era code paths stored native pointers in 32-bit `DvarValue::integer` and `DvarLimits::integer.max` members. That truncates string values and enum-table addresses on LP64; enum lookups also performed 32-bit pointer arithmetic. The domain callback path reconstructed a 16-byte `DvarValue` as five scalar arguments, which is not the native 64-bit C++ calling convention.

This pass changes the authentic dvar implementation to:

- Store string values through `DvarValue::string`, including registration, parsing, copying, latching/reset, setter conversion buffers, and cleanup to `nullptr`.
- Store enum tables through `DvarLimits::enumeration.strings` and index them as pointer arrays in enum-to-string, prefix lookup, value display, domain display, and string-to-enum conversion.
- Call the declared `dvar_s::domainFunc(dvar_s *, DvarValue)` type directly from `Dvar_SetVariant` and `Dvar_SetDomainFunc`, preserving the native aggregate ABI rather than using the old x86 scalar-call cast.
- Replace the stack-buffer assertion in `Dvar_SetStringFromSource` with a pointer comparison against `dvar->current.string`, verifying the setter did not retain the temporary stack buffer.

The new `prepare_real_engine_dvar_pointer_abi.py` stages corrected function bodies from the vendored KisakCOD `dvar.cpp` for host runtime regression and ARM64 compile auditing. The native regression exercises real extracted `Dvar_RegisterString`, `Dvar_RegisterEnum`, enum table lookup, `Dvar_StringToValue`, and `Dvar_UpdateEnumDomain` functions with 64-bit stack addresses; test-only stubs satisfy external services for that isolated function test. The separate ARM64 archive compiles the wider corrected string/enum setter and callback functions, and deliberately leaves registry services unresolved so this archive is not mistaken for a linked runtime.

**Verification:** the first host run exposed a real failure in the original enum-prefix path: the digit parser returned `-1337` before the existing prefix-match loop could run. I corrected that branch so nonnumeric names reach the prefix lookup, and the subsequent native-source workflow passed in [run 40430328329](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40430328329). The Python suite reported **75 tests passed**. The host runtime regression passed in Release and the ASan/UBSan configuration; both CTest runs report **9/9 passed**. The same run compiled the corrected dvar ABI archive for Android AArch64 and printed `IW3_ORIGINAL_DVAR_LP64_POINTER_ABI_AARCH64_COMPILE_GREEN`. Its symbol audit intentionally still shows `Dvar_RegisterVariant` and `Dvar_ClampValueToDomain` as unresolved external services.

**Scope limit:** this is a real LP64 portability repair in the original dvar source, but the complete dvar registry is not linked into Android yet. `FS_Startup`/`FS_InitFilesystem` still have unresolved real registry, localized-directory, file-read and language services; no FastFile/map load, renderer frame, actor/weapon gameplay, or playable ARM64 APK is claimed by this phase. The compiled evidence bundle is [artifact 12701607657 — NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40430328329/artifacts/12701607657).


### Phase AB — explicit native integer-domain bounds in original dvar clamp (27 Oct 2026; source CI green)

The ARM64 dvar ABI audit previously left the authentic `Dvar_ClampValueToDomain` body unresolved in its archive even though the original `Dvar_MakeExplicitType` calls it. This pass stages the real `Dvar_ClampValueToDomain` and `Dvar_ClampVectorToDomain` bodies in both the AArch64 audit archive and the host runtime regression.

In the vendored `src/universal/dvar.cpp`, integer-domain clamping now names `domain.integer.min` and `domain.integer.max` explicitly. This preserves the original `DvarLimits` union semantics: `DvarLimits_Enumeration::stringCount` shares the offset of `DvarLimits_Integer::min`, while the enum string-table pointer is a separate native-width field (offset 8 on LP64). The C++ smoke test has static layout assertions for those offsets and executes the authentic extracted clamp for values below, above, and inside the integer range.

- Engine change: [`a23adf7`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/a23adf7c69bfae852236879c1f761bd6e12e4a13).
- Source audit now requires the clamp and vector clamp to be defined in the ARM64 archive; `Dvar_RegisterVariant` remains a visible unresolved registry dependency.
- Verified run: [native ARM64 source workflow 40435233478](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40435233478). Python suite: 75 tests passed; Release CTest: 9/9; ASan/UBSan CTest: 9/9; ARM64 compile/symbol audit passed.
- Evidence artifact: [12703686512 — source and ABI evidence, NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40435233478/artifacts/12703686512).

The first attempt exposed an overbroad test guard that rejected a valid union alias elsewhere in `Dvar_ValueInDomain`; the guard was narrowed and explicit LP64 layout assertions were added before the successful rerun.

**Scope limit:** this does not link the full dvar registry into Android or invoke `FS_Startup`. FastFile/map loading, the original renderer, actual player/weapon/actor gameplay and physical ARM64 execution remain unproven. The JNI artifact remains diagnostic only; no playable APK is claimed.

### Phase AC — bounded deterministic Android IWD discovery (27 Oct 2026; CI pending)

The next filesystem portability issue was in the Android OS adapter used by the authentic
`FS_AddIwdFilesForGameDirectory` path. The engine mounts at most 1024 IWD archives after
sorting the complete list, but the adapter retained every matching filename in a
`std::vector` before returning the list. A large app-private game-data directory could
therefore consume unbounded memory even though the original engine only uses the first
1024 sorted entries.

The adapter now maintains a max-heap of the lexicographically smallest 1024 regular
`.iwd` filenames while counting all eligible entries. It emits those 1024 (or fewer)
names in ascending order and reports the total count separately. This preserves the
original engine's sorted-prefix/cap behavior while bounding retained filename state to
1024 entries; symlinks and non-regular files remain excluded by the existing rooted
`fstatat(..., AT_SYMLINK_NOFOLLOW)` check.

A native regression creates 1030 IWD-named files and verifies that the adapter reports
all 1030 but emits exactly `archive-0000.iwd` through `archive-1023.iwd` in order.
This exercises the same platform function called by the original directory-scanning
source slice. It does not claim that the full startup runtime or licensed game assets
are integrated.

- Engine-side Android adapter change: `android/iw3-native/iw3_android_platform.cpp`.
- Regression: `android/iw3-native/platform_native_test.cpp`.
- Native ARM64 source workflow [40443331931](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40443331931) passed on code HEAD `c53bef4`. The host CTest suite passed **9/9 in Release and 9/9 under ASan/UBSan**; the `iw3_portable_platform` test includes the 1030-entry sorted-prefix and undersized-output regressions. Artifact [12707615573](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40443331931/artifacts/12707615573) contains native modules and evidence, **not an APK**.
- The source preflight [40443332055](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40443332055) also passed. JNI packaging and Android emulator runs for this HEAD were still in progress at documentation time and are not counted as passed.
- Scope remains limited to IWD enumeration. Original `FS_Startup` is not invoked by
  the diagnostic APK; licensed FastFile/map loading, the original renderer, live
  client-frame input, weapon/actor gameplay, and physical ARM64 execution remain
  unproven. The APK artifact remains diagnostic only and PR #4 must stay unmerged.


### Phase AD — original search-path insertion and game-directory setup (27 Oct 2026; ARM64 source CI green)

The next filesystem-startup layer was FS_AddSearchPath, FS_AddGameDirectory, and FS_AddLocalizedGameDirectory. These are authentic functions called from FS_Startup; leaving FS_AddLocalizedGameDirectory unresolved meant the startup archive could compile while omitting a key part of search-path registration.

This pass stages all three original function bodies from the vendored src/universal/com_files.cpp into the ARM64 startup dependency audit. The existing source-level regression now checks their extracted bodies and the expected call chain into FS_AddIwdFilesForGameDirectory.

A portability cleanup in the authentic FS_AddGameDirectory body replaced the decompiler-era Z_Malloc(512, ...) plus uint32_t* temporary with Z_Malloc(sizeof(directory_t), ...). The allocation now follows the native engine type instead of a magic byte count tied to the old Win32 build.

The first host build caught an integration mistake: adding a second Sys_DirectoryHasContents implementation duplicated the already-existing rooted implementation in android/iw3-native/iw3_android_iwd_directory_io.cpp. That duplicate was removed. The startup archive now deliberately reports Sys_DirectoryHasContents as an external service, while the existing platform module supplies the fail-closed implementation backed by z2026_platform_directory_has_contents. The workflow audits that boundary instead of hiding it.

- Engine allocation fix: [68f8d1b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/68f8d1bc6d141f10cddcbfd3cc2f90e3019b103d).
- Original-function staging and tests: [9f125cd](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/9f125cd0393f8e440727bbc47c99d445542ac5ea), [71d97bf](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/71d97bf4e80071218cb83e3fd1967876d8dac2fa), final regression update [dec31aa](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/dec31aaca1a172c90be80651a477edcecb4c3bbd).
- Final native ARM64 source workflow: [40450859855](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40450859855) — PASS. Host Release CTest: 9/9; ASan/UBSan CTest: 9/9; ARM64 compile and fail-closed symbol/dependency audit passed.
- Source preflight: [40450859816](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40450859816) — PASS.
- Evidence artifact: [12710785846 — compiled modules and audit evidence, NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40450859855/artifacts/12710785846).

The ARM64 archive now defines FS_AddSearchPath, FS_AddGameDirectory, and FS_AddLocalizedGameDirectory. It still leaves the real dvar registry, IWD enumeration/mount, path-building, allocator, language, and file-read dependencies visible; the archive is not linked into the JNI diagnostic runtime. FS_Startup has not been executed by this pass, no licensed FastFile/map has been loaded, no original renderer scene or combat has been demonstrated, and physical ARM64 gameplay remains unproven. The APK generated by the separate JNI workflow remains diagnostic only. Keep PR #4 open and unmerged.

### Phase AE — reject unsupported localized search paths instead of aliasing the base directory (27 Oct 2026)

The Android stringed-system adapter intentionally exposes only the authentic English language name until the real localization subsystem is ported: `SEH_GetLanguageName(0)` returns `english`, while unsupported indices return an empty string. The original `FS_AddLocalizedGameDirectory` loops over all 15 language indices. Before this fix, `FS_AddGameDirectory` formatted an empty language as `dir/`; because that resolves to the parent game directory, a non-empty `main` directory could be registered repeatedly as a localized directory for unsupported languages. This was a concrete search-path correctness bug in the staged original startup path.

The original `FS_AddGameDirectory` now returns early when a localized language name is null or empty, before formatting or probing the path. Supported language behavior is unchanged, and the non-localized game directory is still added by the original final call. The startup extraction gate requires the guard, and `tests/test_iw3_android_fs_startup.py` checks that the guard precedes path formatting and agrees with the Android language adapter.

- Engine correction: [f274d41](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f274d41554e54f6bbcf5f3ace6f0f6375e34e5d1).
- Extraction contract: [960d286](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/960d286ccff97ad36a4e32f582f14afc97d97f94).
- Regression test: [2aa2e6b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/2aa2e6bcde3671b84965dcb0ef8b43bd7dcb4ca4).

This is a source/runtime-correctness fix for search-path setup, not proof that `FS_Startup` executes in Android. The full dvar registry, complete filesystem service graph, licensed FastFile/map load, renderer, client input loop, weapon/actor gameplay, and physical ARM64 execution remain open gates. No playable APK is claimed; keep PR #4 unmerged.
