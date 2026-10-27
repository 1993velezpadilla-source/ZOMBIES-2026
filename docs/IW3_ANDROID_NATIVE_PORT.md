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

### Phase AF — execute original localized search-path setup under a host regression harness (27 Oct 2026)

The previous source-only guard is now exercised by a native CTest harness that compiles and calls the extracted original `FS_AddLocalizedGameDirectory`, `FS_AddGameDirectory`, and `FS_AddSearchPath` bodies. Only narrow platform services are test doubles; path selection, directory-record allocation, search-path insertion, and the unsupported-language early return are the original engine code.

The regression calls `FS_AddLocalizedGameDirectory("/private/iw3", "main")` while the Android language adapter exposes English at index 0 and empty names for unsupported indices. It verifies that the original code probes only `/private/iw3/main/english`, inserts exactly one localized entry (`main/english`) plus the normal non-localized `main` entry, and invokes IWD scanning only for those two valid directories—not once per unsupported language. This test failed to exist before the fix; it now executes the actual extracted function bodies instead of only searching source text.

- Native source workflow: [40454969282](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40454969282) — PASS on the code/test HEAD before this documentation-only commit. Python suite: 76/76; CTest Release: 10/10 including `iw3_original_fs_localized_paths_fail_closed`; ASan/UBSan CTest: 10/10; ARM64 compile and symbol/dependency audits passed.
- Artifact [12711544286](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40454969282/artifacts/12711544286) contains native modules and audit evidence, **not an APK**.
- Engine fix [f274d41](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f274d41554e54f6bbcf5f3ace6f0f6375e34e5d1); host harness [521296b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/521296bc6c6df2814a8572072e289e945cf7e4a6); CMake test registration [b8832fa](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b8832fa9c8b94bfcb6ed0d73047442177b00ee60).

The native harness does not call `FS_Startup` or mount real game archives. The real dvar registry and full filesystem service graph are still not linked into Android; licensed FastFile/map loading, original renderer output, client input loop, weapon/actor gameplay, and physical ARM64 execution remain unproven. Keep PR #4 open and unmerged.


### Phase AG — preserve the original 1024-entry IWD scan cap semantics (27 Oct 2026; CI pending)

A source-to-adapter comparison found a real behavior mismatch in Android IWD discovery. The original `FS_AddIwdFilesForGameDirectory` caps the `Sys_ListFiles` result at 1024 entries **before** sorting the retained entries. The Android platform adapter instead used a max-heap to choose the lexicographically smallest 1024 names from the whole directory. That could mount a different set of archives than the original engine's cap behavior on the same native directory enumeration.

The adapter now retains only the first 1024 valid `.iwd` names in native `readdir` order while continuing to count every eligible archive. It returns that bounded prefix without sorting it; the unchanged original engine function then applies its existing sort to exactly the retained entries. Memory remains bounded by 1024 names, and the original overflow warning/cap path still sees that more than 1024 archives exist.

- Platform correction: [d788c9c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/d788c9c4b18ced55c3493ac73748d40255b7277f).
- Regression harness: [01160c6](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/01160c6e9f1856482e577a6c8e3a0239628c4509). The native test creates 1030 IWD fixtures, captures the filesystem's actual `readdir` prefix, checks the adapter returns precisely that first 1024-entry prefix, verifies the total count remains 1030, and retains the undersized-output fail-closed case.

**Validation status:** the preceding HEAD `0a06d27` had green source-preflight, native ARM64, JNI diagnostic and Android x86_64 emulator runs ([40455246401](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40455246401), [40455246410](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40455246410), [40455246471](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40455246471)). Those results predate this fix and do not validate the new head; CI for the new commits must finish before this phase is marked green.

This corrects archive selection semantics but does not complete the filesystem runtime. `FS_Startup`/`FS_InitFilesystem` are still not invoked by the Android JNI app; no licensed FastFile or real map is loaded, no original renderer scene or weapon/actor gameplay is proven, and no physical ARM64 gameplay has been observed. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged.


### Phase AH — original Dvar_RegisterVariant dependency step and zero-capacity rooted read fix (27 Oct 2026; CI pending)

The next startup blocker was the dvar registration boundary: the ARM64 audit compiled string/enum helpers and wrappers, but left the authentic `Dvar_RegisterVariant` entry point itself unresolved. The generator now extracts that exact upstream body from `third_party/KisakCOD/src/universal/dvar.cpp` into the same ARM64 audit translation unit. The audit requires the function to be defined and keeps its actual dependencies visible: `Dvar_FindMalleableVar`, `Dvar_RegisterNew`, and `Dvar_Reregister`. The first is private/static in the upstream translation unit, so this is a dependency-graph step, not a linked registry. No duplicate dvar state or no-op registry is introduced.

The Android rooted file API also had a contract bug: `z2026_platform_read_file` documented zero-capacity reads for empty files, but rejected every null output pointer before it could test the file. It now permits a null output only when capacity is zero. A native regression verifies that an empty file returns 0, a nonempty file with zero capacity fails closed, and a null output with nonzero capacity is rejected.

- Changed platform adapter: `android/iw3-native/iw3_android_platform.cpp`.
- Regression: `android/iw3-native/platform_native_test.cpp`.
- Original dvar source extraction and symbol gate: `tools/iw3_android/prepare_real_engine_dvar_pointer_abi.py`, `tests/test_iw3_android_dvar_pointer_abi.py`, and `.github/workflows/iw3-original-native-android.yml`.

**Validation on HEAD `36d952e`:** preflight [run 40468290100](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40468290100) passed with 76 Python tests. Native ARM64 [run 40468290104](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40468290104) passed; Release CTest is 10/10 and ASan/UBSan CTest is 10/10. Its AArch64 symbol audit now defines the original `Dvar_RegisterVariant` body and explicitly verifies that `Dvar_FindMalleableVar`, `Dvar_RegisterNew`, and `Dvar_Reregister` remain unresolved. The native evidence bundle is [artifact 12716819656 — NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40468290104/artifacts/12716819656). JNI integration [run 40468290096](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40468290096) also passed ARM64 ELF/JNI/package/signature checks and produced [artifact 12717357724 — diagnostic APK, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40468290096/artifacts/12717357724). These results do not invoke `FS_Startup`/`FS_InitFilesystem`, mount licensed IWDs through a complete runtime, load a FastFile/map, render a scene, or run weapon/actor gameplay. Physical ARM64 gameplay remains unproven. Keep PR #4 open and unmerged.


Phase AH follow-up: the extracted `Dvar_RegisterVariant` compilation unit now declares the exact upstream signatures for `Dvar_RegisterNew`, `Dvar_Reregister`, and the private `Dvar_FindMalleableVar` boundary. These declarations exist only so the compiler can type-check the authentic body in isolation; the ARM64 symbol audit still requires all three to remain unresolved, so this does not pretend the registry is linked.


### Phase AI — signed-char-safe original dvar-name validation (27 Oct 2026; CI pending)

A source audit found that authentic `Dvar_IsValidName()` passed a plain `char` directly to `isalnum()`. On Android ABIs where `char` is signed, bytes at or above 0x80 become negative; passing those values (other than EOF) to the C character-classification API is undefined behavior. The original function now casts the byte to `unsigned char` before classification. Its existing policy remains unchanged: null names are rejected, and every non-null byte must be alphanumeric under the active C locale or underscore.

The exact original `Dvar_IsValidName()` body is now included in both the ARM64 dvar source-audit TU and the host smoke TU. The executable regression checks null, a valid ASCII name, forbidden punctuation, and a high-bit byte; the Python source gate forbids the unsafe `isalnum(nameChar)` call. This targets a real signed-char/UBSan portability defect in the vendored KisakCOD source, not a substitute implementation.

Validation completed on code commit `c1eb7f3a6c0286021fa098d66150819e85e41815`:
- Source preflight passed (run [40469808054](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469808054)).
- Native ARM64 source/module workflow passed 76 Python tests, 10/10 CTest Release, 10/10 CTest ASan/UBSan, and the AArch64 dvar symbol audit (run [40469807933](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807933); evidence bundle [12717908062 — NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807933/artifacts/12717908062)).
- JNI ARM64 compile/package/signature checks passed (run [40469807951](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807951); artifact [12718560155 — diagnostic APK, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807951/artifacts/12718560155)).
- Android x86_64 emulator diagnostic passed: original IWD/FS fixture paths executed and touch events reached the `usercmd_s` adapter (run [40469807955](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807955); artifact [12718042714 — runtime evidence, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807955/artifacts/12718042714)). The same evidence explicitly records `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`.
- Windows MP dedicated/client compile run [40469807977](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40469807977) was still in progress when this documentation update was made and is not counted as passed. Scope boundary: the original dvar registry remains an isolated audit archive with unresolved `Dvar_FindMalleableVar`, `Dvar_RegisterNew`, and `Dvar_Reregister`; the full registry is not linked to Android, `FS_Startup` is not invoked in a complete runtime, and no licensed FastFile/map load, renderer output, or touch-driven weapon/actor gameplay is proven. The diagnostic JNI APK remains not a game; PR #4 must stay open and unmerged.

### Phase AJ — guard original IWD global-load policy against short filenames (27 Oct 2026)

The current Android file-read lifecycle calls the original `FS_FilesAreLoadedGlobally()` while opening IWD members. A source audit found that the function computed a suffix pointer with `&filename[filenameLen - strlen(extension)]` before checking that the filename was at least as long as the extension. Short names (including empty or one-to-three-character paths) could form a pointer before the supplied string, causing undefined behavior and a potential out-of-bounds read on the Android path.

The authentic KisakCOD implementation now uses native `size_t` lengths and checks `filenameLen >= extensionLen` before suffix pointer arithmetic. The extension policy and matching behavior for `.hlsl`, `.txt`, `.cfg`, `.levelshots`, `.menu`, `.arena`, and `.str` are unchanged.

The exact-source extraction gate now requires the length guard and rejects the previous unsafe subtraction. The host CTest invokes the compiled original function through a narrow smoke wrapper and checks every supported suffix plus short negative cases (`""`, `"a"`, `"ab"`, `"abc"`, and `"foo.bin"`). The Python regression also checks the extracted source contract. The same host test is included in the ASan/UBSan test run.

- Engine/source + executable regression commit: [fc10e7b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/fc10e7bbdddf32c63620fda88e961d04e7977360).
- Source preflight: [40492534684](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492534684) — PASS.
- Native ARM64 source/module workflow: [40492534778](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492534778) — PASS. The workflow's original-source tests, Release host tests, ASan/UBSan checks, ARM64 ELF build, frame compile, filtered-file ABI audit, and IWD-indexer audit all completed successfully. Artifact [12728804473](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492534778/artifacts/12728804473) contains compiled modules/evidence, **not an APK**.
- JNI ARM64 compile/package/signature workflow: [40492534713](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492534713) — PASS. Artifact [12728884971](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492534713/artifacts/12728884971) is a signed diagnostic APK, **not a game**.
- Android x86_64 emulator diagnostic: [40492528398](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492528398) — PASS for the existing parser/FS/touch/lifecycle probes. Artifact [12729360183](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40492528398/artifacts/12729360183) is runtime logs, not gameplay evidence. It is an x86_64 emulator with synthetic IWD fixtures, not a physical ARM64 device or a real map.
- Windows SP weapon/killhouse and dedicated compile workflows were still in progress when this note was written; they are not counted as passed.

**Scope boundary:** this fixes one real UB bug in the original filesystem policy and executes its regression, but the complete filesystem runtime is still not linked into Android. The original dvar registry dependencies (`Dvar_FindMalleableVar`, `Dvar_RegisterNew`, `Dvar_Reregister`) remain unresolved at the integration boundary; `FS_Startup`/ `FS_InitFilesystem` are not run by the complete game runtime. No licensed FastFile/map load, original renderer output, touch-driven player movement/weapon/actor gameplay, or physical ARM64 gameplay is proven. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged.


### Phase AK — signed-char-safe original IWD filename hashing (27 Oct 2026; CI pending)

The newest source review found one remaining C character-classification hazard on the active IWD indexing path: original `FS_HashFileName()` called `tolower(fname[i])` with a plain `char`. On Android's signed-char ABI, bytes such as `0xFE` promote to a negative integer outside the C `tolower()` contract. The result can corrupt the hash bucket for a member name and invokes undefined behavior.

The authentic `third_party/KisakCOD/src/universal/com_files.cpp` now uses `tolower(static_cast<unsigned char>(fname[i]))`. ASCII hashing, extension cutoff, separator normalization, and the original hash formula remain unchanged. The extraction gate now requires the safe call and rejects the old expression. The native IWD-name test adds a high-bit filename regression with a deterministic C-locale hash value of 930; a new Python regression verifies the exact original body and generated source.

- Code + test commit: [3e9774f](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/3e9774f9b1d847370748c0f7834aa46fd1a613ca).
- A standalone GCC C++20 reproducer compiled with `-fsigned-char -fsanitize=address,undefined` and passed the ASCII known-answer cases plus the `0xFE` regression. This is a local focused reproducer, **not** a run of the repository's full test suite.
- The original-source fix is in [`3e9774f`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/3e9774f9b1d847370748c0f7834aa46fd1a613ca); the new regression's assertion corrections are in [`bea88f5`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/bea88f55fb1904eaa780173c0657edb701414d5d) and the final tested HEAD is [`267f499`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/267f4994d253647b61b1c9dbf8f7a311f1be5415).
- Source preflight [run 40505160797](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160797) passed **80 Python tests**.
- Native ARM64 source/module [run 40505160790](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160790) passed: CTest Release **10/10**, CTest ASan/UBSan **10/10**, the original IWD-name regression, the original SP frame ARM64 compile and the filesystem/indexer symbol audits. [Artifact 12734113703 — compiled modules/evidence, NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160790/artifacts/12734113703).
- JNI ARM64 integration [run 40505160992](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160992) passed native compilation, exported JNI symbol, APK package and signature checks. [Artifact 12734293003 — signed diagnostic APK, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160992/artifacts/12734293003).
- Android x86_64 emulator [run 40505155505](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505155505) passed the actual Activity/JNI probe. Logs show original ZIP32/IWD parsing, searchpath and directory registration, IWD lookup/read/clone and rooted disk-file open/read/close; actual Android touch events produced attack, sprint and sprint+crouch bits in the `usercmd_s` adapter. [Artifact 12734363284 — emulator logs/screenshots, NOT GAMEPLAY](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505155505/artifacts/12734363284). This is x86_64 emulation with synthetic fixtures, not ARM64-device gameplay.
- The first two runs for the newly added Python regression caught mistakes in the test's own expected-marker assertions; those were corrected before the green `267f499` runs. For transparency, the failed intermediate run is [40505067674](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505067674).
- Windows SP/killhouse runs [40505161252](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505161252) and [40505160713](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40505160713) were cancelled before completion during subsequent branch updates; neither is counted as passed.

**Scope boundary:** this fixes an authentic filename-hash portability defect and adds executable regression coverage. It does not load a licensed IWD or FastFile, invoke the complete `FS_Startup`/`FS_InitFilesystem` runtime, render a map, or prove touch-driven gameplay on physical ARM64. The JNI package remains diagnostic only; PR #4 stays open and unmerged.


### Phase AL — signed-char-safe original enum-index parsing (27 Oct 2026)

The current branch review found one more C-ctype portability hazard in the authentic `Dvar_IndexStringToEnumString()` body: it passed `indexString[indexStringIndex]` directly to `isdigit()`. A high-bit byte can become negative on signed-char builds, which violates the C ctype contract. The original source now calls `isdigit(static_cast<unsigned char>(indexString[indexStringIndex]))`, preserving the existing enum-index parsing behavior while safely rejecting non-ASCII digit bytes.

Regression coverage added:
- The original-source extractor now requires the safe cast and rejects the unsafe call.
- The host test executes the extracted original function with a high-bit index byte and verifies it returns the empty-string failure result.
- The dvar ABI regression target is compiled with `-fsigned-char` for GCC/Clang so the test exercises the same signed-char condition explicitly; the option is limited to that test target.
- No dvar registry, filesystem runtime, or gameplay is claimed by this change.

Code/test commits:
- Engine source: [464e4bb](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/464e4bbdfd1d7d6235d2675b32120fccc148f8eb).
- Extraction/source gate: [f28a713](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f28a7131475e5973cac4f121b27658d6f4d5e0c4).
- Python regression: [d8e40f8](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/d8e40f8a3f9d937b8a558a184c201076d6207eae).
- Native high-bit regression: [9b7522c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/9b7522c82c1ed47427c77eda5111051108bc33ad).
- Explicit signed-char test build: [1dbf6c4](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/1dbf6c44dc0803e084e845664352ee3705098f22).

Validation completed for code/test HEAD `1dbf6c4` (documentation follow-up does not change these sources):
- Native source workflow [40506916667](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40506916667) — **PASS**. The log shows 80 Python tests; CTest Release 10/10; CTest ASan/UBSan 10/10; the new `iw3_original_dvar_pointer_width` high-bit regression passed in both CTest runs; original dvar audit compiled to AArch64 ELF. Artifact [12736080649 — source modules/evidence, NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40506916667/artifacts/12736080649).
- JNI ARM64 compile/package/signature workflow [40506916708](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40506916708) — **PASS**, including 80 Python source tests, native AArch64 ELF/package/signature checks. Artifact [12734744636 — signed JNI diagnostic APK, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40506916708/artifacts/12734744636).
- Source preflight [40506916756](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40506916756) — **PASS**.

The earlier attempts for these workflows were cancelled while successive file commits were landing; the final reruns above completed successfully and are the evidence to use.

**Integration boundary remains unchanged:** `Dvar_FindMalleableVar`, `Dvar_RegisterNew`, and `Dvar_Reregister` still need to be linked with the authentic shared registry state before `FS_Startup`/ `FS_InitFilesystem` can run as a complete Android runtime. No licensed FastFile/map load, original renderer scene, physical ARM64 gameplay, or playable APK is proven. Keep PR #4 open and unmerged.


### Phase AM — map sparse Android pointer IDs to native touch slots (27 Oct 2026; validation pending)

A source review of the latest Activity found a real multi-touch input defect: MotionEvent.getPointerId() returns a stable Android pointer identifier in the range 0..31, but MainActivity discarded any ID >= 10 and the native adapter used the ID directly as an index into a ten-element array. Android pointer identifiers are not compact slot indexes, so valid simultaneous touches could silently lose look/attack/movement events after the platform reused a higher pointer ID.

The Android adapter now stores each external pointer ID separately from its ten available simultaneous-touch slots. DOWN/MOVE finds the existing slot by pointer ID or claims a free slot; UP releases that mapping; snapshots resolve the same ID back to its slot. IDs outside Android's 0..31 range remain rejected, and a new DOWN is rejected only when all ten slots are occupied. The Activity no longer filters valid IDs 10..31.

Regression coverage:
- Native C++ test sends pointer ID 31 and pointer ID 4 simultaneously and verifies both map to independent command bits.
- Releasing ID 31 clears attack without clearing ID 4's still-held sprint bit.
- ID 32 is rejected; a snapshot of an unmapped ID returns an inactive state and zero coordinates.
- Python source regression prevents reintroducing the Activity's old id >= 10 filter.

Scope boundary: this fixes the native touch adapter's pointer-ID/slot mismatch and improves the path toward touch-driven original commands. It still does not link the complete client input translation unit into the Android runtime, run Com_Frame, load a real map, render the original scene, or prove physical ARM64 gameplay. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged until those gates pass.

Validation for the code/test tree (documentation-only HEAD follow-up does not alter these sources):
- Native source/ARM64 workflow [40530589940](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530589940) — **PASS**. It ran 83 Python tests, CTest Release 10/10, CTest ASan/UBSan 10/10, compiled the original filtered-file functions for AArch64, and audited the original frame/filesystem/dvar archives. Artifact [12746471575 — native modules and audits, NOT AN APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530589940/artifacts/12746471575).
- JNI ARM64 package workflow [40530589888](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530589888) — **PASS**. It ran 83 Python tests, Gradle completed successfully, the package contains an AArch64 `libiw3_sp_math.so`, and APK Signature Scheme v2 verified. Artifact [12746641469 — signed JNI diagnostic APK, NOT A GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530589888/artifacts/12746641469).
- Android emulator runtime workflow [40530569311](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530569311) — **PASS** on code/test commit `b6df195`. It ran 83 Python tests, booted an x86_64 emulator, executed the diagnostic JNI Activity, and observed touch DOWN/UP plus attack, sprint and sprint+crouch bits in the original-layout `usercmd_s` adapter. Artifact [12746231970 — emulator logs/evidence, NOT GAMEPLAY](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530569311/artifacts/12746231970).
- Source preflight [40530589990](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530589990) — **PASS**, but this is the separate RotU/static preflight, not proof of Android gameplay.
- Windows SP build/runtime workflows [40530590091](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530590091) and [40530590325](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40530590325) were still in progress at the time of this update and are not counted as passing.

The host regression specifically exercises sparse IDs 31 and 4 concurrently, verifies their attack/sprint bits remain independent, and verifies releasing ID 31 does not clear the still-held ID 4. The Android emulator uses its normal synthetic fixture touches; it is not evidence of a physical ARM64 device or a game map.


### Phase AN — captured Android pointers remain releasable outside the view (27 Oct 2026)

Review of the current native touch boundary found a gameplay-relevant failure mode: Android can continue dispatching a captured MotionEvent after the finger crosses the view/screen boundary. The adapter rejected any finite normalized coordinate outside [0,1] before checking whether the event was MOVE or UP. Consequently, an out-of-view UP was discarded and the corresponding touch role (including ATTACK) could remain active in later usercmd snapshots.

The original native platform boundary now rejects invalid pointer IDs, non-finite coordinates, and invalid DOWN flags, but clamps finite coordinates to [0,1] before updating the existing pointer slot. This preserves bounded coordinates for the original touch-role classifier and, importantly, allows an UP outside the view to release its slot.

Regression coverage:
- A finite coordinate of 1.01 is accepted and observed as 1.0 in the snapshot.
- An out-of-view UP at 1.25 is accepted and deactivates the pointer.
- An attack pointer moved and released at x=1.25 no longer leaves BUTTON_ATTACK set in the next usercmd snapshot.
- NaN coordinates remain rejected.
- Python source guard requires the clamping implementation and the native release regression.

Code/test commits:
- Native boundary: [331c8ba](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/331c8bab2b904994e8f8f0e84b35b6d8f7787fc0).
- Native regression: [0a21b23](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/0a21b238602a54f2eba1f9645dc48c231aadf08d).
- Python source guard: [4c9d3ce](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4c9d3ceb5ffa5d78ce6fb19c44796f90057f000d).

Validation is pending for this new code. The branch's current Android workflows must pass before this change is considered verified. A separate current-head commit [493e759](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/493e75953e8c3bd27eb657477deed715fb3d0003) also adds an object-only compile gate for the complete original `com_files.cpp` translation unit; its CI was still pending when this phase began.

Scope boundary unchanged: this prevents stuck controls in the Android adapter, but does not link the full original client input TU into the Android game runtime. The current JNI APK remains diagnostic only; no real FastFile/map load, original renderer scene, or physical ARM64 gameplay is claimed. Keep PR #4 open and unmerged.


### Phase AO — restore the original sound-shutdown declaration for the Android FS compile gate (27 Oct 2026)

The latest HEAD CI was inspected before editing: ARM64 source-port workflow run [40541980104](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40541980104) failed while compiling the **complete original** `third_party/KisakCOD/src/universal/com_files.cpp` object. The compiler error was precise: `SND_StopSounds` was undeclared at `FS_Shutdown()`. Android had included `sound/snd_stopsounds.h` for the enum only, whereas the normal Win32 include path exposed the function prototype transitively through the platform/sound headers.

Fix: `android/iw3-native/iw3_android_filesystem_compat.h` now includes the narrow upstream `sound/snd_stopsounds.h` enum header and declares the exact original ABI `void __cdecl SND_StopSounds(snd_stopsounds_arg_t which);`. This is a declaration only: no Android no-op or fake sound implementation was added, and the original `FS_Shutdown()` call to `SND_StopSounds(SND_STOP_STREAMED)` remains unchanged. The function will still need the real sound service when the complete runtime is linked.

Added `tests/test_iw3_android_fs_sound_abi.py`: it checks the Android declaration against the original `snd_public.h` prototype, confirms the enum and original call are present, and rejects a stub definition in the compatibility header.

- Fix commit: [0de8cc0](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/0de8cc008b1e518d734c7bc40d265dc66a6af4ce)
- Regression commit: [874f898](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/874f898004aacbca9c9cff1c32c68d9249ccb88e)

Validation after the fix is now green in [native ARM64 workflow run 40543600189](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40543600189): **93 Python tests passed**, **CTest 10/10 passed**, ASan/UBSan host checks passed, and the complete original `com_files.cpp` translation unit compiled as an Android ARM64 object. The same run also passed the original frame, IWD indexer, filtered-file/location and typed `G_RunFrame` ARM64 compile/audit steps. Artifact [12752181230](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40543600189/artifacts/12752181230) contains native modules and audit evidence, not an APK. The earlier failing run [40541980104](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40541980104) is retained as the regression trigger and is not counted as passing. The separate JNI packaging workflow is still running at the time of this note.

Scope boundary unchanged: this fixes a compile-time ABI declaration gap only. It does not link the real audio service, complete `FS_Startup()`/IWD mounting into a game runtime, load FastFiles/maps, render the original scene, or prove ARM64 gameplay. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.


### Phase AP — compile the complete original dvar translation unit without Win32 headers (27 Oct 2026)

The last successful Android source gate compiled the complete original `com_files.cpp` translation unit, but the authentic dvar registry still existed only as a collection of extracted ABI-audit bodies. The next compile-time portability barrier was the original `universal/dvar.cpp` translation unit: it directly included `Windows.h` and `win_local.h`, which brings DirectInput/Win32-only declarations into the Android build. Its unused `devgui.h` include also exposes 32-bit-only UI layout assertions that are not part of the dvar registry.

Implemented on `feature/iw3-native-android-arm64-20261025`:

- `qcommon/fast_critical_section.h` now owns the original two-counter `FastCriticalSection` declaration and `Sys_LockWrite/Sys_UnlockWrite` prototypes. Compile-time assertions pin its 8-byte size and `writeCount` offset. `win_local.h` includes that shared declaration, preserving the Win32 layout rather than duplicating a platform-specific copy.
- Original `dvar.cpp` selects a narrow Android compatibility header instead of importing `Windows.h`/DirectInput through `win_local.h`. The unused `devgui.h` include is excluded on Android; the original dvar registration and lookup bodies remain unchanged.
- `iw3_android_dvar_compat.h` provides native atomic wrappers with Win32 `InterlockedIncrement`, `InterlockedDecrement`, and `InterlockedCompareExchange` return-value semantics. It does not implement the engine lock or network-sleep services.
- CMake now compiles the **complete original `dvar.cpp` as an Android ARM64 object-only gate** (`iw3_sp_full_dvar`). It is deliberately not linked into the JNI diagnostic: `Sys_LockWrite`, `Sys_UnlockWrite`, `NET_Sleep`, and the broader engine service graph still need authentic runtime integration.
- Added four source regression tests for the conditional include boundary, shared lock layout, atomic return semantics, and the object-only CMake target.

Commits:
- [`be81007` — shared original critical-section ABI](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/be81007dae1863a082ea164ecb8c5caea020a828)
- [`a86f72e` — use shared ABI from the Win32 header](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/a86f72ecad4ed8054be324ff967ddfff5d7227b7)
- [`c6f6524` — narrow Android include path in original dvar.cpp](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c6f65245dfa0cd7acc4efea1bf6fa98ee5381810)
- [`c7cd6d7` — compile the full original dvar TU for ARM64](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c7cd6d7ecbe57c8717a560d9e50badd01dbebefc)
- [`5855978` — regression guards](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/5855978ca59041cfd47043bc94f12e54ff7c1bc6)

Validation status at this documentation update:
- Source preflight [40550116986](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40550116986) — **PASS** (static source/package gates only).
- Android ARM64 source build [40550116839](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40550116839) — queued/pending; not counted as a pass.
- JNI packaging [40550116957](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40550116957) — queued/pending; not counted as a pass.
- A local GCC C++20 check of the three atomic wrapper return contracts passed, but this is not a substitute for the NDK compile.

Scope boundary: this phase only opens the next full-source compile gate. It does not link the original dvar registry, invoke `FS_Startup()`, mount licensed IWD/FastFiles, load a map, render a scene, or prove gameplay. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged.


### Phase AP validation follow-up — 27 Oct 2026

The first full ARM64 dvar compile attempt, run [40550752915](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40550752915), exposed three concrete header-surface issues: the Win32 `win_net.h` transitively included the Windows-only `net_chan.h` layout; `com_math.h` collided with Android libc's `random()` declaration and required `__forceinline`; and removing that header also removed the original `CLAMP` macro. The Android dvar include boundary was narrowed further: only the exact `NET_Sleep` and `Vec4Compare` declarations are retained, the Win32 network/math headers stay on the Windows branch, and the source-compatible `CLAMP` macro is provided. These are compile-boundary changes; no dvar function body was replaced.

Final code validation at source commit [`c7faa09`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c7faa0935fcef1a911855a4e604a0b0aa478ee56):

- [Android ARM64 native-source workflow 40551042854](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551042854) — **PASS**.
- Its log reports **97 Python tests passed**, **CTest 10/10**, and **ASan/UBSan CTest 10/10**.
- The NDK build explicitly compiled `third_party/KisakCOD/src/universal/dvar.cpp` as `iw3_sp_full_dvar`; log marker: `Built target iw3_sp_full_dvar`.
- [JNI integration workflow 40551042669](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551042669) — **PASS**, producing only a signed diagnostic package.
- [Static source preflight 40551042758](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551042758) — **PASS**.
- The source module artifact [12755855399](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551042854/artifacts/12755855399) contains native modules/audit evidence, not a playable APK.
- The JNI artifact [12754168226](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551042669/artifacts/12754168226) is explicitly **NOT A GAME**.
- The separate offline SP weapons and killhouse workflows were still in progress at this check; their outcomes are not counted.

The new milestone is limited but concrete: the full authentic dvar translation unit now compiles for Android ARM64. It is still not linked into the runtime; `Sys_LockWrite`, `Sys_UnlockWrite`, `NET_Sleep`, the dvar global state/service graph, and the FS startup call path remain unintegrated. No `FS_Startup()`, real IWD/FastFile/map load, original renderer, or real gameplay has been demonstrated. Keep PR #4 open and unmerged.

### Phase AI — native-width copy of original ZIP state in IWD reads (27 Oct 2026; CI pending)

Reviewing the current full `com_files.cpp` compile gate exposed one remaining Win32-size assumption in the authentic `FS_FOpenFileReadForThread()` clone path: it copied exactly 128 bytes from the original `unz_s` state into the per-handle state. `unz_s` contains native pointers (including `FILE *`, the active decompression-state pointer, and a temporary-file pointer), so the Win32 byte count is not a valid structure-size contract on LP64/Android ARM64.

The original engine call now copies `sizeof(*zfi)`, while preserving the existing `file` and `pfile_in_zip_read` members around the state copy exactly as before. The original open/clone/read/close logic is unchanged; no replacement ZIP or IWD implementation was added.

Regression coverage:
- `tests/test_iw3_android_iwd_read.py` extracts the authentic `FS_FOpenFileReadForThread()` body and requires the native-sized copy while rejecting the old 128-byte expression.
- `tools/iw3_android/prepare_real_engine_iwd_read.py` enforces the same requirement during source staging, so the exact-source audit fails closed if the old Win32 size returns.
- The existing Android NDK gate compiles the complete original `com_files.cpp` translation unit, exercising this changed call under the ARM64 ABI.

Validation is pending for this new code. The previous HEAD `dfe26bc` had successful native source, JNI packaging, Windows SP source/runtime, and offline killhouse workflow runs ([native ARM64](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551516936), [JNI diagnostic](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551516990), [Windows SP source](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551516773), [offline SP runtime evidence](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40551516883)). Those runs predate this fix and do not validate it; only new runs for the updated source may be counted.

Scope boundary: this fixes a real native-width IWD state-copy defect and strengthens regression coverage, but it does not link or invoke the complete filesystem startup in the Android app. No licensed FastFile/map load, original renderer scene, touch-driven player/weapon/actor combat, or physical ARM64 gameplay is proven. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.

## Phase AQ — original dvar sleep service on Android (2026-10-27)

The latest source/CI review found that the full original `third_party/KisakCOD/src/universal/dvar.cpp` now compiles as an Android ARM64 object, but its Win32 `NET_Sleep` service was only declared by the Android compatibility header. The original `win32/win_net.cpp` implementation is `NET_Sleep(int msec) { Sleep(msec); }`; dvar readers use `NET_Sleep(0)` to yield while the original critical-section counters change and use a short positive delay in the dvar sorter.

Implemented on `feature/iw3-native-android-arm64-20261025`:
- `7ca4a6f`: added `android/iw3-native/iw3_android_dvar_io.cpp`, mapping zero/non-positive waits to POSIX `sched_yield()` and positive millisecond waits to `nanosleep()`, retrying interrupted sleeps. This is a platform service for the original dvar code, not a registry replacement.
- `db09cb6`: added a native regression for zero-yield and positive-delay behavior.
- `a119921`: archived the untouched full `dvar.cpp` object with the Android sleep provider as `libiw3_sp_dvar_android.a`; added the host CTest.
- `1be48b0`: added an ARM64 relocatable-link audit that verifies the provider resolves `NET_Sleep` while preserving unrelated engine service dependencies as visible.
- `a75732d`: added Python regression coverage for source semantics, CMake wiring and the link audit.
- `ad585b4`: switched to the POSIX `<time.h>` declarations.
- `8ac1bef`: corrected a test assertion that incorrectly matched the explanatory comment `Sleep(msec)`; the check now rejects an actual call expression instead.

Validation:
- [ARM64 native source/ABI gate, run 40562531162](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40562531162) — PASS on `8ac1bef`. Host Release CTest: 11/11; ASan/UBSan CTest: 11/11; full original `dvar.cpp` and the POSIX provider compiled; `ld.lld -r` resolved `NET_Sleep` in the combined archive.
- [Source preflight, run 40562531176](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40562531176) — PASS; the new Python regression passed.
- [ARM64 audit artifact 12761622670](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40562531162/artifacts/12761622670) — native modules and audit reports only, **NOT an APK or game**.
- Earlier run [40562418740](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40562418740) failed only in the new Python assertion because it rejected an explanatory comment; that test was corrected and the succeeding preflight and ARM64 run passed.

Remaining dependency evidence: the relocatable dvar link still reports `Vec4Compare(float const*, float const*)` as an unresolved original engine service. The archive is not linked into the JNI diagnostic or a full runtime. Real dvar startup, `FS_Startup`/ `FS_InitFilesystem`, licensed IWD/FastFile/map loading, original rendering, and gameplay remain unproven. The emulator/JNI workflows are separate diagnostics and do not establish ARM64 device gameplay.

## Phase AR — original Vec4Compare provider for the full dvar archive (2026-10-27)

The Phase AQ ARM64 relocatable-link report exposed `Vec4Compare(float const*, float const*)` as a remaining dependency of the complete original `dvar.cpp`. The function is defined in the vendored KisakCOD `src/universal/com_math.cpp` and compares all four float components with the original exact-equality semantics.

Implemented on the Android branch:
- `7a49b35`: added `prepare_real_engine_dvar_vec4.py`, which extracts the exact function body from original `com_math.cpp`, records the source/body hashes, and refuses to overwrite the vendored source.
- `cd5fb39`: added Python source-contract and CI wiring tests.
- `5a0010e` / `3a304f8`: added a native regression for equal vectors, signed zero, each component mismatch and NaN.
- `2b42ff2`: added the generated original provider to the full-dvar archive and a host CTest when the generated source is supplied.
- `c5c45da`: updated the ARM64 relocatable-link audit to require `NET_Sleep` and `Vec4Compare` to resolve, while checking that `Com_Printf` remains visible as an unported engine dependency.
- `109234f`: corrected the sleep regression's expected marker after the combined audit name changed.
- `c8b9b12`: included the dvar archive, generated provider, report and symbol evidence in the native artifact.

Validation at the time of this update:
- [Source preflight, run 40563082679](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40563082679) — PASS, including the new source extraction regression.
- [ARM64 native source/ABI gate, run 40563082516](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40563082516) — in progress; the host compile/test step was still running. Do not count the ARM64 provider link as passed yet.
- Earlier [run 40562989463](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40562989463) failed before native compilation because a Python test expected the previous audit marker; the marker assertion was corrected and the current preflight is green.

This provider is an incremental dependency fix, not a complete runtime. `Com_Printf` and other original engine services remain unresolved; the dvar archive is not linked into the JNI app. No FS startup, licensed IWD/FastFile/map load, original rendering, or playable Android ARM64 gameplay is claimed.


## Phase AS — Android log sink for the original dvar Com_Printf dependency (2026-10-27)

The last ARM64 relocatable-link audit (run [40563417130](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40563417130)) proved that the original full dvar.cpp object and its POSIX NET_Sleep / exact Vec4Compare provider compile and link together, but still reported Com_Printf(int, char const*, ...) as unresolved. The same log shows many other real engine services still unresolved; the archive is not a runtime.

Implemented on the branch in this pass:
- Added android/iw3-native/iw3_android_dvar_log.cpp: a real Android logcat sink for this one dvar archive dependency. It preserves the channel number in the output, formats variadic arguments with bounded vsnprintf, and does not suppress the message. A host-only stderr path lets the exact formatting code be regression-tested.
- Added dvar_log_native_test.cpp and tests/test_iw3_android_dvar_log.py; the native test captures stderr and asserts the exact formatted channel/message, while Python verifies the Android logcat route and CMake/CI wiring.
- Added the provider to iw3_sp_full_dvar / libiw3_sp_dvar_android.a. The ARM64 audit now requires Com_Printf to be defined and absent from the unresolved list, while explicitly retaining __android_log_write as an external Android platform import.
- This provider is scoped to the dvar dependency archive only. It is not a replacement for the original Com_PrintMessage, console, or logfile subsystem and is not linked into the JNI diagnostic APK.

Validation of the provider at commit c4f8da5:
- [ARM64 native source/ABI gate, run 40573527252](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40573527252) — PASS; host Release CTest 13/13, ASan/UBSan CTest 13/13, original dvar archive resolves Com_Printf while leaving the Android log import and other engine services visible.
- [Source preflight, run 40573531783](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40573531783) — PASS, 106 Python regressions.
- [JNI integration, run 40573531857](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40573531857) — FAIL, not because of Com_Printf: Gradle did not pass the now-required IW3_EXTRACTED_FS_STARTUP path, and the JNI workflow had not generated that source. This separate integration gap is fixed in Phase AT; validation of that fix is pending. Remaining original dvar dependencies and all full-runtime gates remain open: Com_PrintError, Com_PrintWarning, parser/string/memory/command/file services, full FS_Startup / FS_InitFilesystem execution, real IWD/FastFile/map loading, original rendering, touch-driven gameplay and physical ARM64 execution. PR #4 remains open and unmerged; this is not a playable APK.


## Phase AT — wire original filesystem-startup source into both Android Gradle builds (2026-10-27)

The first JNI integration attempt after Phase AS failed at CMake configuration, with the exact error that the original FS_RegisterDvars/FS_Startup/FS_InitFilesystem source was required. Inspection showed a real build-graph mismatch: the native ARM64 audit generated iw3_fs_startup.cpp and passed IW3_EXTRACTED_FS_STARTUP to CMake, but the Android app's Gradle arguments omitted that variable and both JNI workflows omitted the generator call. CMake now correctly fails closed rather than silently skipping the startup translation unit.

Implemented:
- android/iw3-native/android_app/app/build.gradle now passes IW3_EXTRACTED_FS_STARTUP using the same generated-source directory as the other original IW3 C++ inputs.
- Both iw3-original-android-jni.yml and iw3-original-android-emulator-jni.yml run prepare_real_engine_fs_startup.py before Gradle configuration, writing iw3_fs_startup.cpp and an explicit provenance/dependency report.
- Both workflow artifacts retain the new startup report for inspection.
- tests/test_iw3_android_fs_startup_gradle.py checks that the generated source path matches between the generator, Gradle CMake argument and mandatory CMake gate.

This is a build-graph correction that makes the JNI gate compile the original filesystem-startup source instead of failing before compilation. It does not call FS_Startup at runtime or mount licensed game data.

Validation on code commit 0ab6abd (the subsequent documentation-only commit does not change the tested code):
- [Source preflight, run 40574167987](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574167987) — PASS.
- [Native ARM64 source/ABI gate, run 40574158550](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574158550) — PASS; 108 Python tests, Release CTest 13/13, ASan/UBSan CTest 13/13, full original dvar archive link audit resolves Com_Printf and retains the Android logcat import plus other engine services as unresolved.
- [JNI ARM64 package, run 40574158707](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574158707) — PASS; the generated original filesystem-startup source reaches CMake, the native ARM64 diagnostic library packages and signs. Artifact [12766756748](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574158707/artifacts/12766756748) is explicitly a diagnostic APK, NOT the game.
- [Android emulator execution, run 40574158588](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574158588) — PASS on x86_64 emulator; the original C++ diagnostics execute, touch DOWN/UP and sprint/slide chords reach the original usercmd_s adapter, and pause/resume is observed. The evidence explicitly records arm64_device_execution_proven=false and gameplay_proven=false. Artifact [12767541187](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40574158588/artifacts/12767541187) contains the emulator logs, not gameplay.

Next real-runtime blocker: the FS-startup archive still has visible original dependencies including FS_AddIwdFilesForGameDirectory, FS_BuildOSPath, Z_Malloc, SEH_GetLanguageName, FS_ReadFile, SEH_InitLanguage and Sys_DirectoryHasContents; the full dvar archive also has parser, string, memory, command, file and synchronization services unresolved. The next pass must close these original service edges and actually invoke FS startup before attempting a licensed IWD/FastFile/map load. The JNI APK remains diagnostic only: no original renderer scene, real map load, touch-driven player/weapon/actor combat, or physical ARM64 gameplay is proven. PR #4 remains open and unmerged.


## Phase AU — resolve the original FS-startup directory probe on Android (2026-10-27)

The successful Phase AT build exposed the next concrete FS startup edge: KisakCOD defines Sys_DirectoryHasContents only under WIN32, so the verbatim FS_AddGameDirectory startup body still depended on a platform symbol that Android did not provide. The existing z2026_platform_directory_has_contents implementation already performs a no-follow scan under the retained app-private root and returns -1 for invalid/unreadable paths.

Implemented:
- android/iw3-native/iw3_android_directory_has_contents.cpp now provides the original Sys_DirectoryHasContents 0/1 contract once, shared by the FS-startup archive and diagnostic library. It accepts only paths rooted at the configured app data directory, rejects sibling-prefix paths, delegates relative scanning to the existing openat/no-follow service, and maps errors to 0 (fail closed).
- Added fs_startup_directory_native_test.cpp to exercise root path, nested path, empty/unreadable result, and sibling/outside-root rejection against the same adapter.
- Added the CTest target and Python/CI source contract; the ARM64 audit now requires Sys_DirectoryHasContents to be defined and absent from the startup archive's unresolved list.

Validation for Phase AU is pending. This resolves one real startup dependency but does not call FS_Startup, link the complete dvar/filesystem runtime, mount a real IWD/FastFile, or load a map. The next unresolved startup edges remain FS_AddIwdFilesForGameDirectory, FS_BuildOSPath, Z_Malloc, SEH_GetLanguageName, FS_ReadFile, SEH_InitLanguage and Dvar_RegisterInt/String/Bool. No original renderer scene or gameplay is proven.


Phase AU CI correction: the first host build found that the diagnostic already had a Sys_DirectoryHasContents definition in iw3_android_iwd_directory_io.cpp. I removed that duplicate and centralized the rooted implementation in iw3_android_directory_has_contents.cpp, then wired that one source into both the startup archive and diagnostic library. The legacy FS-startup regression now asserts the centralized provider and that the IWD directory adapter no longer defines a second copy. Fresh CI is pending; the failed attempt is retained as evidence of the duplicate-symbol regression, not counted as a pass.


## Phase AV — POSIX ABI fix for rooted FS startup directory service (2026-10-27)

Reviewed PR #4 and the current Android source/CI before changing code. The latest ARM64 source run failed before reaching the NDK because the shared Android directory adapter used the Win32-only spelling `__cdecl` in a translation unit also compiled by the Linux host tests. The compiler reported `expected initializer before 'Sys_DirectoryHasContents'`.

Implemented on `feature/iw3-native-android-arm64-20261025`:
- `b6b69b7`: removed the Win32-only `__cdecl` annotation from `android/iw3-native/iw3_android_directory_has_contents.cpp`. Android and POSIX use the platform default C++ calling convention here; the original Windows-only implementation is unchanged.
- `7df56bd`: updated the dedicated directory-adapter regression to require the POSIX declaration and reject a leaked `__cdecl` spelling.
- `af75fa3`: fixed a second stale assertion in `tests/test_iw3_android_fs_startup.py` that still expected the removed annotation.

Evidence/state at the latest check:
- [Source preflight 40576935748](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40576935748) — PASS on `af75fa3`.
- [Native Android ARM64 source/ABI gate 40576935679](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40576935679) — host Release build/CTest and ASan/UBSan build/CTest passed; Android NDK installation was still in progress, so the ARM64 compile/audit was not yet confirmed.
- [JNI diagnostic integration 40576935823](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40576935823) — in progress; no APK result counted yet.
- Earlier failures [40576763463](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40576763463) and [40575999258](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40575999258) are retained as regression evidence: first the old Python assertion rejected the intended ABI fix; then host compilation exposed the undefined `__cdecl` token. Neither is counted as a pass.

This is a build portability correction only. `FS_Startup` and `FS_InitFilesystem` are still staged/compiled for dependency audit, not invoked by the app. The next runtime graph still has to resolve original IWD enumeration/mount, path, allocation, language, file-read and Dvar services before real game data can be mounted. No FastFile/map load, original renderer scene, touch-driven combat, or physical ARM64 gameplay is proven. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.


## Phase AW — correct archive-level FS startup symbol audit (2026-10-27)

The POSIX calling-convention correction compiled through the full Android NDK stage. That exposed a defect in the CI audit itself: `llvm-nm -u` on a static archive reports undefined references per archive member, even when another member of the same archive defines the symbol. The log showed `Sys_DirectoryHasContents(char const*)` in the defined-symbol list and also as a member-level undefined reference from the original startup object. The old audit incorrectly treated that normal archive representation as a failed provider.

Implemented:
- `6bbb594`: the ARM64 workflow now performs a relocatable link of all `libiw3_sp_fs_startup.a` members with the NDK's `ld.lld -m aarch64linux -r --whole-archive ... --no-whole-archive` and checks the combined object's undefined-symbol list. It still requires the genuinely unported Dvar/IWD/path/memory/language/file services to remain visible.
- `ffbe17a`: added a regression requiring the archive-level link audit and rejecting the old per-member false-positive check.
- `6113b91`: pinned the AArch64 linker emulation explicitly.
- `d20c062`: aligned the test assertion with the NDK linker variable used by the workflow.

CI evidence:
- [Preflight 40577715567](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40577715567) — PASS on `d20c062`.
- ARM64 source/ABI run [40576935679](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40576935679) reached the AArch64 archive audit and failed only at the false-positive check described above; that run is not counted as a pass.
- Run [40577383430](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40577383430) failed earlier in the Python guard because the test expected the literal `ld.lld` command rather than the workflow's `$ld_lld` variable. The assertion was corrected; that run is not counted as a pass.
- The fresh ARM64 and JNI workflows for `d20c062` were queued at the latest check, so the new relocatable-link audit has not yet been confirmed. No result is inferred from pending runs.

This phase fixes the evidence gate, not the runtime. The combined startup object must still report the original Dvar registration, IWD enumeration/mount, path, allocation, language and file-read services as unresolved. `FS_Startup`/ `FS_InitFilesystem` have not been invoked by the Android app; there is still no real FastFile/map load, original renderer scene, touch-driven weapon/actor gameplay, or physical ARM64 gameplay. Keep PR #4 open and unmerged.
