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


## Phase AX — native-width original FS_BuildOSPath for Android startup (2026-10-27)

Reviewed the current PR head and CI before changing the filesystem startup slice. The combined AArch64 FS_Startup archive audit had shown FS_BuildOSPath/FS_BuildOSPathForThread as unresolved alongside the Dvar, IWD enumeration, allocator, language and file-read services.

Implemented at code commit [6320e86](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/6320e86c44221ea128b947cbaab09646482f467b), with extraction/test corrections at [e7fa689](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/e7fa689246383a87c3d0abc7c0736dcc4d0fafbf):

- Corrected the authentic FS_BuildOSPathForThread body in third_party/KisakCOD/src/universal/com_files.cpp: path component lengths now use bounded native size_t lengths instead of decompiled uint32_t temporaries. The 256-byte engine limit is checked without overflowing the sum.
- Overlong paths preserve the original thread-specific contract (background/threaded calls clear the output; main-thread calls report ERR_FATAL). The output is also cleared if a test/platform fatal handler unexpectedly returns.
- prepare_real_engine_fs_startup.py now extracts the original FS_ReplaceSeparators, FS_BuildOSPath, and FS_BuildOSPathForThread functions from the vendored engine source into the startup dependency-audit archive.
- The host regression now executes those original path-builder functions, checks separator normalization, checks the 256-byte overflow behavior for backend and main-thread calls, and exercises the original localized directory insertion with the resulting OS path.
- The ARM64 workflow requires all three path functions to be defined and rejects them from the combined startup object's unresolved-symbol list.

Validation on HEAD e7fa689246383a87c3d0abc7c0736dcc4d0fafbf:

- [Source preflight 40583644871](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583644871) — PASS; 111 Python source/regression tests.
- [Native Android ARM64 source/ABI 40583644880](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583644880) — PASS; Release CTest 14/14 and ASan/UBSan CTest 14/14. The complete original com_files.cpp and dvar.cpp compile gates passed; the archive-level audit reports IW3_ORIGINAL_FS_BUILD_OS_PATH_AARCH64_RESOLVED and IW3_ORIGINAL_FS_STARTUP_AARCH64_RELOCATABLE_LINK_AUDIT_GREEN. Artifact [12769594094](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583644880/artifacts/12769594094) contains native modules/audit reports only, NOT an APK.
- [JNI ARM64 package 40583644708](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583644708) — PASS; Gradle built, verified and signed the arm64-v8a diagnostic package. APK SHA-256: c89abe2d09b00a21046beabe90cf59df4888ae6ac2f40cdde07c51a9646ea442. Artifact [12770404005](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583644708/artifacts/12770404005) is explicitly DIAGNOSTIC — NOT A PLAYABLE GAME.
- Android emulator runtime [40583634644](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583634644) — PASS on the x86_64 emulator. The proof executes the original ZIP32 parser, FS_LoadZipFile fixture indexing, FS_AddSearchPath insertion, FS_AddIwdFilesForGameDirectory scan, FS_AddGameDirectory registration, original file lookup/read/close and IWD clone branches; actual ADB touches produced attack=1, sprint=2 and slide chord=514 in the original usercmd_s adapter, and pause/resume passed. Artifact [12771060660](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583634644/artifacts/12771060660) is logs/evidence only. The report explicitly says original_upstream_fsh_table_integrated=false, arm64_device_execution_proven=false and gameplay_proven=false.
- Earlier run [40583457156](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40583457156) failed in the new generator contract because it expected initializer syntax rather than the source's declaration-plus-assignment form. The marker was corrected in e7fa689; the succeeding preflight and ARM64 workflow passed. That failed attempt remains visible and is not counted as a pass.

This resolves one real path-builder edge in the staged startup graph; it does not invoke FS_Startup/FS_InitFilesystem or mount game data. Remaining original startup dependencies include Dvar_RegisterInt/String/Bool, FS_AddIwdFilesForGameDirectory, Z_Malloc, SEH_GetLanguageName, FS_ReadFile, and SEH_InitLanguage. The next integration target is the original IWD directory scan/mount path and its rooted Android Sys_ListFiles service, followed by real FastFile/map loading, renderer integration, touch-to-usercmd_s consumption, and observed gameplay on physical ARM64. No playable APK, real map load, original renderer scene, or ARM64 combat is claimed; keep PR #4 open and unmerged.


## Phase AY — link the original Dvar registry into the FS-startup dependency audit (2026-10-27)

Reviewed PR #4 and the latest native/JNI CI before changing the startup dependency graph. The ARM64 build already compiled the complete original `dvar.cpp` into `libiw3_sp_dvar_android.a`, but the FS-startup audit linked only `libiw3_sp_fs_startup.a`. That audit therefore kept `Dvar_RegisterInt/String/Bool` unresolved even though their real upstream provider had already been built. This was an incomplete integration check, not a runtime failure.

Implemented:
- Commit [b314c7f](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b314c7f95e2ff161dd30ae0743e9a97aa09b0888) adds a relocatable AArch64 link of the original FS-startup archive and the complete original Dvar archive, including the POSIX `NET_Sleep`, Android `Com_Printf` sink, and extracted original `Vec4Compare` provider.
- Commit [6031062](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/60310628d22b87e47fb0a7a0fce788a0cd580267) adds a regression requiring the combined audit marker and preserving the explicit unresolved-service gate.
- The combined object must define and no longer leave unresolved `Dvar_RegisterInt`, `Dvar_RegisterString`, or `Dvar_RegisterBool`. It deliberately continues to report `FS_AddIwdFilesForGameDirectory`, `Z_Malloc`, `SEH_GetLanguageName`, `FS_ReadFile`, and `SEH_InitLanguage` as unresolved. No stub provider is added.
- Commit [40cfb8c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/40cfb8c04512b3b3d664302095396532104b7b7c) fixes the emulator workflow's PR branch filter: GitHub's `pull_request.branches` selects the PR base, not the head. PR #4 targets `feature/zombies-offline-sp-weapons-20261024`, so the old head-branch filter prevented this emulator proof from running on PR updates.

Validation:
- [Native ARM64 source/ABI run 40592544077](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592544077) — PASS on code/test commit `60310628`; Release CTest 14/14 and ASan/UBSan CTest 14/14. The log contains `IW3_ORIGINAL_FS_STARTUP_DVAR_REGISTRATION_AARCH64_COMBINED_LINK_GREEN`. Artifact [12773808292](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592544077/artifacts/12773808292) contains the combined object and dependency reports, not a game or APK.
- [Preflight run 40592729668](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592729668) — PASS after the workflow-trigger fix.
- At the time of this entry, the rerun on current head `40cfb8c` was still in progress: [native ARM64 40592729547](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592729547), [JNI diagnostic 40592729529](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592729529), and [emulator runtime proof 40592729545](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40592729545). These are not counted as passed here.

This is a real dependency-link improvement, but it is still a relocatable audit object. `FS_Startup`/`FS_InitFilesystem` have not been invoked in the Android app; no licensed IWD/FastFile/map was loaded; the original renderer is not showing a scene; and touch-driven weapons/actors on physical ARM64 remain unproven. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged.


## Phase AY — stage original IWD enumeration in the filesystem-startup dependency archive (2026-10-27; validation pending)

The latest combined AArch64 startup/Dvar link still reported `FS_AddIwdFilesForGameDirectory` as an unresolved symbol. That function is called by the original `FS_AddGameDirectory` body, and its authentic implementation was already staged separately for the diagnostic IWD path. The startup archive had not yet included that body, so the audit stopped one edge before directory scanning.

Implemented on `feature/iw3-native-android-arm64-20261025`:

- [`3e79df0`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/3e79df08eb6a018533ea124324f17be49f845677): `prepare_real_engine_fs_startup.py` now stages the original `FS_AddIwdFilesForGameDirectory` body from vendored `com_files.cpp` into the existing startup audit source. It retains the upstream null/empty directory-list guard, `sizeof(s0[0])` qsort element size, original `FS_LoadZipFile` call and original search-path insertion.
- [`029a05b`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/029a05b8174394b5d1fa0c2cba0206458ab84861): regression coverage now checks that the extracted body and its 64-bit-safe list/sort contracts are present, and that the runtime is still explicitly unproven.
- [`288b4e8`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/288b4e8b70ce13c1ad05cb5d6cac753867e15b12): the AArch64 workflow requires `FS_AddIwdFilesForGameDirectory` to be defined in the startup archive and absent from the combined startup/Dvar undefined-symbol list. It also keeps the real follow-on edges visible: `FS_LoadZipFile`, `Sys_ListFiles`, `FS_FreeFileList`, `IwdFileLanguage`, `iwdsort`, `I_strncmp`, `SEH_GetLanguageIndexForName`, `Com_PrintWarning`, plus the existing allocator/language/file-read services.

The fresh preflight, native ARM64 source/ABI, JNI diagnostic and emulator workflows were triggered by the branch updates; their final results have not yet been inspected. Do not count this pass as CI-green until the run for the latest code completes.

**Scope boundary:** this closes a real function-definition edge in a dependency-audit archive; it does not execute `FS_Startup` or `FS_InitFilesystem` in the Android app. The remaining original IWD enumeration/mount services are intentionally unresolved rather than stubbed. No licensed FastFile/map load, original renderer scene, touch-driven weapon/actor gameplay, or physical ARM64 gameplay is proven. The JNI APK remains diagnostic only. Keep PR #4 open and unmerged.


### Phase AY validation correction — keep the path-only host test isolated (2026-10-27)

The first build after adding the original IWD enumerator failed in the host-only localized-path test with a duplicate definition of `FS_AddIwdFilesForGameDirectory`: the test intentionally supplies a narrow stub, while the new startup audit source now contains the real body. This failure was inspected and is not counted as passing evidence.

Corrective changes:
- [`d952aef`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/d952aefc14362ac925fc57669e7ecf8738fe06c4): put only the extracted IWD enumerator behind `#if !defined(IW3_FS_STARTUP_HOST_TEST)` in the generated source. The original body remains present and compiled in the actual startup archive.
- [`e62fb77`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/e62fb77fd248323ac209260003724b1b16b78c78): corrected the generator's newline escaping.
- [`748400e`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/748400e5069c876fdffbb03f3e26802aaa0a96a3): define the exclusion macro only for the focused host test target, leaving the ARM64 startup archive unchanged.
- [`b6b1107`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b6b1107aa8d5e58aa3cc353c2267872494c3026f): add a regression for this separation.

Validation on code commit `b6b1107aa8d5e58aa3cc353c2267872494c3026f`:
- [Preflight run 40601336530](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601336530) — PASS; 113 Python tests.
- [Native Android ARM64 source/ABI run 40601328329](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328329) — PASS; Release CTest 14/14, ASan/UBSan CTest 14/14, original KisakCOD frame/IWD/filter compile gates, and AArch64 relocatable startup+Dvar audit.
- [PR native run 40601336640](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601336640) — PASS on the same code commit.
- [Artifact 12778902451](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328329/artifacts/12778902451) contains native modules, symbols and provenance reports only; **not an APK and not a game**.

The AArch64 audit now confirms that the original `FS_AddIwdFilesForGameDirectory` is defined in the startup archive and no longer unresolved in the combined startup+Dvar object. The following genuine services remain unresolved and intentionally visible: `FS_LoadZipFile`, `Sys_ListFiles`, `FS_FreeFileList`, `IwdFileLanguage`, `iwdsort`, `I_strncmp`, `SEH_GetLanguageIndexForName`, `Com_PrintWarning`, `Z_Malloc`, `SEH_GetLanguageName`, `FS_ReadFile`, and `SEH_InitLanguage`.

The JNI ARM64 packaging run [40601328212](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328212) subsequently passed compilation, ELF/JNI checks, package signature validation and artifact upload; [artifact 12778947705](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328212/artifacts/12778947705) is explicitly a diagnostic APK, **NOT a playable game**. The x86_64 emulator runtime [40601328227](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328227) was still running at the latest inspection and is not counted as passed. Even a successful diagnostic APK/emulator run would not prove real-map rendering or gameplay. `FS_Startup`/ `FS_InitFilesystem` are still not invoked by the Android app, no licensed FastFile/map is loaded, no original renderer scene or touch-driven weapon/actor combat is proven, and physical ARM64 gameplay remains unverified. PR #4 remains open and unmerged.


## Phase AZ — link the original path builder into the IWD diagnostic and recover a launcher-only emulator ANR (2026-10-27)

Reviewed the latest branch and CI before editing. The last emulator proof at [40601328227](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328227) compiled and launched the JNI diagnostic; all logged original ZIP/IWD/file-read probes and touch-surface initialization passed. The job then failed before touch injection because UIAutomator saw an Android system dialog, “Quickstep isn't responding”, over the still-running app. The captured hierarchy and screenshot are in artifact [12778213139](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328227/artifacts/12778213139). This was a launcher/UI test-harness failure, not evidence that the app view was absent or that engine gameplay worked.

Implemented in this pass:
- The emulator probe now retries view discovery a bounded five times. It only recovers the exact Quickstep launcher ANR system dialog by tapping the dialog's actual android:id/aerr_wait bounds from UIAutomator. It does not click through an app ANR and does not substitute arbitrary screen coordinates.
- The IWD lookup source slice already carried the original FS_ReplaceSeparators and FS_BuildOSPathForThread bodies. Added the missing original FS_BuildOSPath wrapper to that same generated source, so the rooted IWD scanner uses the engine's 256-byte fail-closed path semantics without linking the entire uninitialized FS_Startup object.
- Removed the competing platform FS_BuildOSPath implementation. The existing lookup IO module remains the single Com_Error provider; the diagnostic fails closed on fatal path overflow rather than returning a truncated path.
- Added source regressions for the launcher recovery and single-provider path-builder link.

Validation status: fresh preflight, Android ARM64 native/ABI, JNI package and emulator workflows are triggered by these changes. Their final results have not yet been inspected, so this phase is not marked CI-green yet. The last known completed evidence remains:
- [Preflight 40601336530](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601336530) — PASS on b6b1107.
- [Native ARM64 40601328329](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328329) — PASS on b6b1107, including Release/ASan/UBSan CTest 14/14 and the startup+Dvar relocatable audit.
- [JNI package 40601328212](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328212) — PASS for the signed ARM64 diagnostic package, not gameplay.
- [Emulator 40601328227](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40601328227) — FAIL at UIAutomator discovery due to the Quickstep ANR dialog; original JNI/IWD probes before that point passed. This run is not counted as a full emulator-probe pass.

Scope boundary remains explicit: this links the authentic path builder into the existing diagnostic IWD shared library; it does not call FS_Startup() or FS_InitFilesystem(). No licensed FastFile/map has been loaded, no original renderer scene is shown, no touch-driven weapon/actor gameplay is proven, and no complete runtime has been exercised on physical ARM64. Keep PR #4 open and unmerged; the JNI APK remains diagnostic only.


### Phase AZ validation correction — align the regression with bounded UI recovery (2026-10-27)

The first CI attempt after the Phase AZ edits failed in source preflight, before any NDK build. The new emulator script intentionally replaced its one-shot “Native diagnostic view is not visible in the actual Android hierarchy” failure with a bounded-retry failure message, but the existing accessibility regression still required the old literal. The path-builder integration regression passed; this was a stale test assertion, not a C++ compile result.

- Failed attempt: [native ARM64 run 40608349575](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40608349575), step “Verify original upstream IW3 source and synthesize header-only ABI overlay”; 115 Python tests ran, one failed because of the obsolete message assertion.
- Corrected the regression to require the new bounded-recovery failure message.
- Fresh CI for the corrected test commit is pending. No ARM64 CMake/link result is inferred from the failed preflight run.


### Phase AZ linker correction — keep the diagnostic link narrow (2026-10-27)

The first native CMake build after Phase AZ failed at the host link stage. The attempt had added the whole extracted FS-startup source object to the diagnostic shared library. CI correctly exposed duplicate definitions of Com_Error, FS_ReplaceSeparators and FS_BuildOSPathForThread, plus unresolved Dvar and other FS_Startup services. That attempt is not counted as a successful link or runtime integration.

Corrective implementation:
- Removed the full-startup object from the diagnostic shared library; the separate ARM64 FS-startup archive audit remains unchanged.
- Extended the existing original IWD lookup extractor to include only the missing verbatim FS_BuildOSPath wrapper. Its existing original FS_BuildOSPathForThread and FS_ReplaceSeparators bodies remain the single providers for those helpers.
- Removed the second Com_Error implementation from the directory adapter; the existing lookup IO adapter is the sole provider.
- Added a regression that runs the extractor, verifies the original wrapper body and provenance flags, and rejects the over-broad startup-object link.

Failure evidence: [native ARM64 run 40608438801](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40608438801) failed in the host CMake link with the duplicate and unresolved symbols above. Fresh validation for the corrected narrow link is pending; no success is inferred from the failed run.


### Phase BA — combined original IWD mount and ZIP link audit (2026-10-27)

The next blocker was not another isolated compile error: the FS-startup audit had the authentic FS_LoadZipFile, allocator/checksum helpers, IWD language helper, and ZIP parser in separate source slices, so the dependency report could not show which of those providers resolved when linked together.

Implementation on the PR branch:

- Added the non-game audit target iw3_sp_iwd_services, combining the existing authentic IWD allocator/checksum/string service slice with the original IWD filename/language slice.
- Added iw3_sp_unzip to compile the original KisakCOD unzip.cpp source as its own ARM64 audit archive.
- Added a combined AArch64 relocatable link of the original FS-startup archive, full Dvar archive, IWD services/names, FS_LoadZipFile, and ZIP parser.
- The combined link explicitly verifies definitions for IwdFileLanguage, Z_Malloc, FS_LoadZipFile, unzOpen, unzGetGlobalInfo, unzReadCurrentFile, and unzClose. It does not hide or stub the remaining services.
- Kept iwdsort and I_strncmp in the explicit unresolved list. An earlier experiment copied those helpers into the service slice and the host linker caught duplicate definitions because they already belong to the IWD directory slice. The service generator was restored to its original boundary; the final audit reports those dependencies as pending rather than duplicating their definitions.

Validation:

- [Native ARM64 audit run 40615993341](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40615993341) — PASS. Host Release CTest 14/14; ASan/UBSan CTest 14/14; original Android ARM64 source targets compiled; the log contains IW3_ORIGINAL_FS_STARTUP_IWD_SERVICES_AARCH64_COMBINED_LINK_GREEN.
- [Source preflight run 40615993363](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40615993363) — PASS.
- [JNI integration run 40615993227](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40615993227) — the diagnostic Activity/JNI ARM64 build completed successfully. This is still a diagnostic package, not the game.
- [Android emulator run 40615993206](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40615993206) — the original JNI diagnostic had compiled and was executing its emulator probe when this note was written; no final emulator result is claimed here.

The combined link still intentionally reports these unresolved engine services: iwdsort, I_strncmp, SEH_GetLanguageName, FS_ReadFile, SEH_InitLanguage, Sys_ListFiles, FS_FreeFileList, SEH_GetLanguageIndexForName, and Com_PrintWarning. The next integration pass must choose a single provider for the original IWD directory helpers, then connect the authentic file-list allocator/platform enumeration and language/read services before calling FS_Startup() / FS_InitFilesystem() in a runtime.

Scope boundary remains unchanged: IW3_FS_STARTUP_RUNTIME_INVOKED=false, IW3_REAL_GAME_DATA_MOUNTED=false, and IW3_PLAYABLE_APK=false. No real map, renderer scene, physical ARM64 gameplay, weapon/actor execution, or playable APK is proven. PR #4 stays open and unmerged.


### Phase BB — instrument the diagnostic touch-to-usercmd proof (2026-10-27)

The prior emulator run [40615993206](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40615993206) did launch the JNI Activity and passed the original ZIP parser, IWD search-path, game-directory, and FS-read probes. It then failed at the final touch assertions: the probe searched for IW3_JNI_USERCMD snapshot lines, but the JNI touch entry point had never emitted those lines. That was a test-observability defect, not proof of gameplay.

Correction:

- The diagnostic JNI touch entry now calls the existing native touch adapter, then takes a snapshot from the original IW3 SP usercmd_s layout and logs the observed attack bit and button mask.
- The log is emitted only when both the touch event and snapshot succeed; failures are logged distinctly.
- Added a regression test tying the JNI log format to the emulator script's attack, sprint, and slide checks. The source continues to identify the Activity as diagnostic, not a game engine.

This only makes the diagnostic input probe observable; it does not connect these snapshots to the full original client/server frame loop.

Current validation after this correction:
- [Source preflight 40616676075](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40616676075) — PASS.
- [Native ARM64 audit 40616676124](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40616676124) — PASS; Release CTest 14/14, ASan/UBSan CTest 14/14, original ARM64 modules compiled, and the combined FS/IWD/ZIP link marker is green.
- [JNI integration 40616675993](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40616675993) — PASS for the diagnostic ARM64 Activity/JNI package only.
- [Android emulator probe 40616676055](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40616676055) — PASS on x86_64 emulator. Logs prove the diagnostic adapter observed attack=1/buttons=1, sprint buttons=2, and slide buttons=514 after actual ADB taps. This is not ARM64-device gameplay.

No playable APK, real map load, 3D scene render, or physical ARM64 gameplay is claimed.


### Phase BE — original Hunk temporary allocator made LP64-safe (2026-10-27)

The next dependency after the original FS_ReadFile audit was Hunk_AllocateTempMemory / Hunk_FreeTempMemory. The authentic com_memory.cpp used uint32_t pointer masks for 4 KiB page boundaries and always added a 32-bit dummy field to hunkHeader_t; on ARM64 the pointer field is eight bytes, so that header would exceed the allocator's fixed 16-byte offset.

This pass moves the Hunk counters/base pointers into one engine-owned com_memory_state.cpp used by the common engine source list, fixes the original temporary allocator's page-base arithmetic through uintptr_t, and keeps the allocation header exactly 16 bytes on both ILP32 and LP64. The original allocator bodies are staged into an ARM64 dependency-audit archive and combined with the FS/Dvar/IWD/readfile archives; no memory or language service is stubbed.

Fresh preflight, host Release/ASan/UBSan and Android ARM64 CI are pending for this update. The expected link gate is that Hunk_AllocateTempMemory and Hunk_FreeTempMemory become defined; SEH_InitLanguage and the remaining virtual-memory/tracker services stay visible. The archive is not the runtime and is not linked into the diagnostic APK.

The emulator probe now rechecks foreground/accessibility state before each gesture and uses short hold gestures so a recurring Quickstep launcher ANR cannot silently consume the remaining inputs. The latest prior emulator attempt passed ZIP/IWD/read diagnostics but failed the usercmd gesture assertions after the launcher overlay; this correction is not validated until the new emulator run finishes.

Hard boundary: FS_Startup/FS_InitFilesystem have not been invoked in the complete Android runtime; no licensed map/FastFile, renderer scene, physical ARM64 gameplay, or playable APK is claimed. PR #4 remains open and unmerged.


## Phase BF — original StringEd language initializer in the ARM64 startup audit (2026-10-28)

Reviewed the current PR head `d722b83122ec0ca4a9c76f342060e0f02b6fc2ec` and the latest native/ JNI/emulator Actions runs before editing. The latest combined ARM64 FS/Dvar/IWD/ZIP/readfile/Hunk audit resolved the original temporary Hunk allocator, but still reported `SEH_InitLanguage` as an unresolved dependency. The JNI and x86_64 emulator runs were successful diagnostics only; neither proves the game runtime.

Implemented on `feature/iw3-native-android-arm64-20261025`:

- Added `prepare_real_engine_language.py`, which extracts the exact original `SEH_InitLanguage`, `SEH_UpdateCurrentLanguage`, `SEH_GetLanguageName`, and `SEH_GetLanguageIndexForName` bodies and the original 15-entry language table from KisakCOD's `src/stringed/stringed_hooks.cpp`. It records source/table/function hashes and refuses to overwrite vendored source.
- Added `iw3_android_language_compat.h` with a native pointer-width guard for `languageInfo_t`: 8 bytes on ILP32, 16 bytes on LP64. The old upstream comment described only the Win32 layout; the extracted table now compiles with the correct ARM64 layout.
- Added the original language source as the optional `iw3_sp_language` audit archive and a host CTest that checks all 15 names, case-insensitive name-to-index lookup, unknown-name fallback, and out-of-range name fallback.
- In the combined ARM64 audit build only, the English-only diagnostic definitions of `SEH_GetLanguageName` and `SEH_GetLanguageIndexForName` are now excluded. The JNI diagnostic retains its narrow fallback; the combined link instead uses the authentic source functions. No fake language initializer or replacement registry was added.
- Extended the combined AArch64 relocatable link to require `SEH_InitLanguage`, `SEH_UpdateCurrentLanguage`, and the original language table to be defined alongside the already-resolved Dvar registration and IWD services.

Validation for code HEAD `b0739a33d1e012ab9dc60fbd1acffcc4137276a2` is now complete:

- [Native ARM64 audit 40623831860](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831860) — **PASS**. The workflow ran 129 Python tests; host Release CTest passed 15/15 and ASan/UBSan CTest passed 15/15. The Android NDK AArch64 compile and combined relocatable link passed. The combined link defines `SEH_InitLanguage()`, `SEH_UpdateCurrentLanguage()`, `SEH_GetLanguageName()`, `SEH_GetLanguageIndexForName()`, and `g_languages`. Marker: `IW3_ORIGINAL_FS_STARTUP_LANGUAGE_INIT_AARCH64_LINK_GREEN`.
- [Source preflight 40623831921](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831921) — **PASS**.
- [JNI diagnostic build 40623831861](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831861) — **PASS for ARM64 compilation/package/signature only**. Artifact [12788492120](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831861/artifacts/12788492120) is explicitly a diagnostic JNI APK, not the game.
- [x86_64 Android emulator diagnostic 40623831855](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831855) — **PASS for the diagnostic probe only**. Artifact [12789155404](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40623831855/artifacts/12789155404) records execution of original ZIP/IWD parsing, IWD indexing/searchpath/read paths, rooted Android files-directory access, touch down/up readback into `usercmd_s`, sprint/slide button translation, and pause/resume lifecycle events. The evidence explicitly says `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`.

The first Phase BF native attempt failed because the extracted initializer called `SEH_UpdateCurrentLanguage()` before its declaration and two old regressions still expected the previous unresolved-symbol loop. The compatibility header and those tests were corrected; the successful runs above are on the resulting code HEAD.
Hard acceptance gates remain open: the combined audit is not the runtime. The app still does not invoke the complete original `FS_Startup()`/`FS_InitFilesystem()` call path, mount licensed game FastFiles or load a map, render a real 3D scene, or run touch-driven weapons/actors through the complete original frame loop on a physical ARM64 device. The JNI artifact remains diagnostic. Keep PR #4 open and unmerged; `IW3_PLAYABLE_APK=false` remains explicit.



## Phase BG — connect the original StringEd initialization chain to the FS-startup audit (2026-10-27; validation pending)

Reviewed PR #4 at code head `b0739a33` and inspected the completed native/JNI/emulator Actions jobs before making this change. The previous combined ARM64 audit had the original `SEH_InitLanguage` registry functions, IWD mount, ZIP reader, file-read helpers and Hunk allocator, but it did not include the StringEd package loader that `FS_InitFilesystem()` calls through `SEH_Init_StringEd()` and `SEH_UpdateLanguageInfo()`.

Implemented on `feature/iw3-native-android-arm64-20261025`:

- Commit [220a5f0](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/220a5f0df6185b6c04570cc30d438799cf43d4a5) extends the existing source-hash-checked extractor to preserve the original `FS_LanguageHasAssets`, `SEH_StringEd_SetLanguageStrings`, `SEH_UpdateLanguageInfo`, `SEH_Init_StringEd` and `SEH_Shutdown_StringEd` bodies from `stringed_hooks.cpp`. It includes the original filesystem/StringEd declarations rather than introducing substitute language logic.
- Commit [c53ab17](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c53ab176e1e1a5393814dfa69467bc24548c71cf) adds `iw3_sp_stringed_ingame`, compiled from the complete vendored `src/stringed/stringed_ingame.cpp`. The original `SE_Init`, `SE_ShutDown`, `SE_LoadLanguage`, `SE_Load` and file-data helpers remain upstream code.
- Commit [b8814ea](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b8814ea1af06cf560c88be226e9551cdec21b017) adds that archive to the AArch64 relocatable FS/Dvar/IWD/ZIP/readfile/Hunk/language link and requires the original StringEd startup symbols to be defined.
- Commit [1c2759f](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/1c2759fb7becf7a1799e29b1b4dadc09bae8a980) adds regression checks for the original hook chain, its CMake provider and the new link marker.

The audit deliberately requires `FS_ListFiles` to remain visible as unresolved at this stage. The original StringEd loader calls it to enumerate localized-string files; this pass must not misreport that missing filesystem provider as a completed localization runtime.

**Validation status:** the fresh source preflight, Android NDK ARM64 audit, JNI diagnostic build and emulator diagnostic have been triggered for the updated branch. Their final results have not yet been inspected; this phase is not marked CI-green until those jobs complete.

**Scope boundary:** this is dependency integration, not gameplay. The app still does not invoke the complete original `FS_InitFilesystem()` chain; the new StringEd archive is not linked into the JNI APK. No licensed FastFile/map load, renderer scene, physical ARM64 execution of the game loop, or touch-driven weapon/actor gameplay is proven. The JNI artifact remains diagnostic only. Keep PR #4 open and unmerged.



## Phase BH — resolve original FS_ListFiles into the StringEd dependency chain (2026-10-27; CI pending)

After staging the original StringEd hooks, the next unresolved symbol was `FS_ListFiles`: `SE_R_ListFiles()` calls it recursively to enumerate localized-string files. This pass extends the authentic startup source slice rather than adding a replacement directory scanner.

Implementation:

- Commit [7e8df1e](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/7e8df1e26ec0215bda3cb96315576f991653634e) adds original `FS_ListFiles`, `FS_CheckLocation`, `FS_AddFileToList`, `FS_ReturnPath`, `FS_SanitizeFilename`, `FS_UseSearchPath` and `FS_IwdIsPure` bodies from `com_files.cpp` to the startup dependency archive.
- Commit [15c6dfc](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/15c6dfc55d3e59629734624216c9af850e4bd599) adds the original `SEH_GetCurrentLanguage()` body needed by `FS_UseSearchPath()`.
- Commit [c8ec509](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c8ec5099d7923cc327f3a6bcebaaa3e44c59c9c7) adds the existing original `iw3_sp_filtered_files` archive to the combined AArch64 link. The audit now requires `FS_ListFiles`, `FS_ListFilteredFiles`, `FS_ListFilteredFilesInLocation` and the original search helpers to be defined, and no longer treats `FS_ListFiles` as an expected unresolved symbol.
- Commits [4b5fdd2](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4b5fdd26589d292fb26acd8d1e339e03afdc2844) and [c2da310](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c2da310e7950cdc23914485d920d4457882b213f) add regression coverage for this link boundary.
- The first extraction attempt failed because helper prototypes and definitions shared a signature. Commits [b9a7b49](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b9a7b4942046ecf38d1a87b673b02357bfebc7b7) and [4374e71](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4374e718c6d100c0ca2bebce1d2c1d466d672425) corrected the extractor to match definition-only signatures ending at the newline after the declaration; the signature does not include the opening brace, so the complete function body is retained.

Validation currently available for code HEAD `4374e718c6d100c0ca2bebce1d2c1d466d672425`:

- [Source preflight 40626826243](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626826243) — PASS.
- [Native ARM64 audit 40626826402](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626826402) — running; final compile/link result not yet available.
- [JNI diagnostic build 40626826236](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626826236) — running.
- [x86_64 emulator diagnostic 40626826295](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626826295) — running.

The next dependency boundary is now explicit: `Hunk_UserCreate`, `Hunk_UserAlloc`, `Hunk_UserDestroy`, `Hunk_CopyString`, `Com_FilterPath` and `I_strnicmp` must remain visible until their original providers are integrated. The source audit must fail if these are accidentally hidden or falsely marked resolved.

**No runtime completion is claimed.** The full `FS_InitFilesystem()` call path is still not invoked in the Android Activity; no real licensed FastFile/map is loaded; no renderer scene or touch-driven weapons/actors are demonstrated on an ARM64 device. The JNI APK is still diagnostic only. Keep PR #4 open and unmerged.



## Phase BI — repair LP64 StringEd parser and complete the filtered-list compile boundary (2026-10-27; validation pending)

The first native build after adding the original StringEd provider failed in two concrete places, and those failures were inspected rather than marked green:

1. The generated language-hook translation unit included `stringed_ingame.h`, pulling inline parser code into the wrong audit source and exposing 32-bit pointer casts at lines 376, 379 and 385.
2. The original FS startup slice used `FS_IsBackupSubStr` and `FS_ListFilteredFiles` before declarations/providers were visible to that translation unit.

Corrections:

- [Commit 485a64e](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/485a64eaa81ab75a4d22c0d739228c47a4f85ad1) removed the full StringEd header from the language-hook slice and declared only the original `SE_Init`, `SE_ShutDown` and `SE_LoadLanguage` entry points needed by the hook bodies.
- [Commit 8d55035](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/8d55035d7cd6a8ee89d42db1cc73686751c53a9b) and [commit 5e3fff0](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/5e3fff052ffd225ebe97f2972f69a7f629f2aa2e) corrected the original inline `CStringEdPackage::ReadLine()` to keep `strchr` results as pointers and calculate the line length with pointer subtraction. No 32-bit pointer cast remains in that path.
- [Commit 9622c8b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/9622c8b9efb7854dcc3b41cb85b41d7453ae306e) stages the original `FS_IsBackupSubStr` body, and [commit 062ff9e](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/062ff9e73f2f465b98039773affed185ecd498a8) adds the declaration for the authentic `FS_ListFilteredFiles` provider.
- [Commit 6e5af4d](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/6e5af4db12f36b15d011350a0c9712601f8cea53) adds source regressions for the FS listing boundary; [commit 27e30b6](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/27e30b60eea7934bad529f82a4af143cdfa38c4d) adds a regression against reintroducing the StringEd pointer truncation.

The failed native attempt was [run 40626969922](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626969922); its log showed the above compiler errors. The source-preflight run [40626969931](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40626969931) passed for the earlier code state, but the latest corrections still require fresh native/NDK validation. The current code head is `27e30b60eea7934bad529f82a4af143cdfa38c4d`; do not treat the older failed build as validation of these corrections.

The next runtime dependency boundary remains the original Hunk-user allocator family: `Hunk_UserCreate`, `Hunk_UserAlloc`, `Hunk_UserDestroy`, `Hunk_CopyString`, plus `Com_FilterPath` and `I_strnicmp`. The audit must continue exposing those until their authentic providers are ported and exercised.

No full runtime start, licensed FastFile/map load, 3D scene render, physical ARM64 execution, or gameplay is proven. The diagnostic JNI APK is not the game; PR #4 stays open and unmerged.



## Phase BJ — replace the D3D-coupled StringEd TU with source-verified loader bodies (2026-10-27; validation pending)

The next native build showed that compiling the whole upstream `stringed_ingame.cpp` translation unit imports `database/database.h` and fails on `gfx_d3d/r_gfx.h: d3d9.h` in the Android/Linux build. That TU contains both the needed original StringEd loader and unrelated D3D/FastFile lookup entry points, so compiling it whole is not a valid Android integration boundary.

Correction:

- Added [prepare_real_engine_stringed.py](https://github.com/1993velezpadilla-source/ZOMBIES-2026/blob/feature/iw3-native-android-arm64-20261025/tools/iw3_android/prepare_real_engine_stringed.py) in commit [f45f27b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f45f27b9ace80f440af2fa9476f51230916da079). It hash-checks the vendored source and extracts the original `SE_Init`, `SE_ShutDown`, `SE_LoadLanguage`, `SE_Load`, `SE_GetFoundFile`, `SE_LoadFileData`, `SE_FreeFileDataAfterLoad`, `SE_BuildFileList`, `SE_R_ListFiles` and `SE_NewLanguage` bodies plus their source-owned globals. It excludes `database/database.h` and the unrelated `SE_GetString_FastFile` DB path; no loader logic is replaced.
- Commit [c0844dd](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c0844ddd69ca0d588c6674757b478c1930dcc991) changed the CMake provider to consume this extracted source. Commit [2617952](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/2617952a840be301351881b2260cec3fa82483a3) stages it and passes `IW3_EXTRACTED_STRINGED_INGAME` to both host and ARM64 configurations.
- Commit [c6d616d](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c6d616dc2104c8bfb68c11d26d57cb43cfcb5410) adds generator/link-boundary regressions. The follow-up [commit 77616cf](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/77616cf2df517ac7a77082b60e2d9e6211e295f3) updates the language test to assert the generated-source variable rather than the removed full-TU path.

Validation notes:
- Native run [40627217087](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40627217087) failed on the D3D header dependency, as expected for the full-TU experiment.
- Native run [40627243110](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40627243110) failed earlier in preflight because a regression still expected the old full-source CMake path. That assertion was updated in `77616cf`.
- The latest native/NDK run [40627267559](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40627267559) and the associated JNI/emulator jobs have not yet produced final results; do not mark this phase CI-green until they finish.

The code is still a dependency audit, not a playable build. The original filesystem startup is not invoked by the Activity, no real FastFile/map is loaded, and no scene render or touch-driven weapon/actor loop is proven on ARM64. PR #4 remains open and unmerged.



## Phase BK — correct StringEd source-staging command separation (2026-10-27; fresh CI pending)

The first run of the D3D-free StringEd extraction did not reach compilation: the workflow accidentally ended the language staging command with a shell continuation, so argparse treated the next `python3 prepare_real_engine_stringed.py` invocation as extra arguments. This was a workflow syntax defect, not a source-parser result.

- Failed run: [40627267559](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40627267559), step `Verify original upstream IW3 source and synthesize header-only ABI overlay`.
- Fix: [commit b16b35c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/b16b35c75dcb5bc9554d50f4808d914b14b0eee5) removes the trailing continuation between the separate language and StringEd generator commands.
- The current code head is `b16b35c75dcb5bc9554d50f4808d914b14b0eee5`. Fresh native/NDK/JNI/emulator results have not yet been inspected; the prior failure is not evidence for or against the corrected staging step.

The acceptance boundary is unchanged: the StringEd bodies must come from the original source, the combined audit must preserve unresolved Hunk-user/filter services, and the diagnostic APK must not be called a playable game.



## Phase BL — remove duplicate providers from the combined original startup link (2026-10-27; fresh CI pending)

The first ARM64 combined-link attempt after the StringEd/filtered-list additions failed with two duplicate symbols. The linker identified the exact providers:

- `SEH_GetCurrentLanguage()` was defined by the original StringEd hook slice and the English-only diagnostic implementation in `iw3_android_iwd_lookup_io.cpp`.
- `FS_IwdIsPure(iwd_t*)` was defined by both the new startup slice and the already-existing original `FS_Read` archive.

Fixes:

- [Commit 05bbc27](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/05bbc2751ffd46f050df32e6ec0a09a357cf3140) removes the redundant `FS_IwdIsPure` extraction from the startup archive. The combined audit uses the existing original provider from the FS-read archive.
- [Commit 32cf2e2](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/32cf2e221e627eaf7a9369fb36534a9a353f1251) wraps the English-only `SEH_GetCurrentLanguage()` provider with `#if !defined(IW3_IWD_DIRECTORY_LINK_AUDIT)`. It remains available to the isolated diagnostic library, while the combined startup audit must bind the original language implementation.
- [Commit c66bf3b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c66bf3b93e7df1d74c176d294bbcede11f13e81b) removes the obsolete duplicate-provider regression expectation; [commit 4d2284a](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4d2284a723b679462aba8d05142e8a68122ae038) adds a test protecting the diagnostic-only language guard.

Evidence: [native run 40627406847](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40627406847) failed at the combined link with those two duplicate-symbol diagnostics. The current code head is `4d2284a723b679462aba8d05142e8a68122ae038`; fresh native/NDK, JNI and emulator jobs are queued/running and are not yet counted as passed.

The source preflight and host sanitizer suite had passed earlier in this pass, including the D3D-free StringEd loader archive and 15/15 CTest cases, but the ARM64 combined link is not green until the new run confirms the duplicate providers are gone. The next expected unresolved engine providers are still Hunk-user allocation and path-filter functions; do not replace them with empty implementations.

No Android Activity invocation of full `FS_InitFilesystem()`, licensed FastFile/map load, 3D scene, or gameplay loop is proven. The JNI artifact remains diagnostic, and PR #4 remains open and unmerged.



## Phase BM — port original HunkUser address state and virtual-memory services (2026-10-27; native CI pending)

The StringEd/filtered-file chain now reaches the original HunkUser allocator. The original code used 32-bit integer fields for absolute addresses and computed the reset page using `user[114].name`, which depends on the ILP32 structure layout. That cannot safely serve the ARM64 allocator.

Implemented:

- [Commit 70d7117](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/70d7117722e044c37a7453234bd217a0ca194efe) changes the original `HunkUser::end` and `HunkUser::pos` to `uintptr_t`, preserves the ILP32 offsets/sizes with static assertions, and aligns the LP64 buffer to 32 bytes.
- [Commit 7a2ff2b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/7a2ff2b73b246804b21b5ddeed84ccba3965e76e) stages the original `Hunk_UserCreate`, `Hunk_UserAlloc`, `Hunk_UserAllocAlignStrict`, `Hunk_UserSetPos`, `Hunk_UserReset`, `Hunk_UserDestroy` and `Hunk_CopyString` bodies with checked pointer-width substitutions. The original allocation policy and page-crossing behavior are retained; no fake allocator is substituted.
- [Commit 863443b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/863443b6d7d9e256d0ee19cae96453639d20602f) adds POSIX virtual-memory services using `mmap(PROT_NONE)`, `mprotect`, `madvise(MADV_DONTNEED)` and `munmap`, with reservation-range tracking and fatal handling of invalid ranges.
- [Commit e2f3f50](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/e2f3f500aacccb9fe4631f4918cd154fe291b010) adds the host regression target; [commit ab0c95c](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/ab0c95c44461a1c48f6d7437649acf3eab543034) tests 32-byte alignment, allocation across page boundaries, reset/decommit and string copying.
- [Commit cd8290b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/cd8290b62650fe67f3ebd72a85d292fd8485b8ed) stages the source and passes it into host/ARM64 CMake; [commit a37f6bc](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/a37f6bc15666ec11974367746abd4f5ef7541ab2) includes the provider in the combined ARM64 link audit and requires the HunkUser/Z_Virtual symbols to resolve.
- Follow-up commits [8c5ae9b](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/8c5ae9b5d1b7745f918d3f11634b8e4b50d02095), [fadfb7f](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/fadfb7f0d50a5dd349625570e82fc5ed2b37174c), [9177ad1](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/9177ad1bb8f9f95da488ee6a039ef9c1d01baf4e), [c88caed](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/c88caed2e169a7957edef0e54ec08d59aa0499e9), [6b67e11](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/6b67e11f359ad66c61454e54a66a622801e81634), [5653387](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/56533879714ec61e72b40b31a9a08265d32dc8fe) and [bb90322](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/bb90322cc9b59533cef2f7777d6cc257aa09d4e8) tighten failure handling, regressions and uploaded source/link evidence.

The first preflight for the new target failed on a stale test expecting HunkUser to remain unresolved; that expectation was updated in `5653387`. The current native ARM64 workflow [40628363959](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40628363959) is pending and has not yet validated the latest combined link. The separate source preflight [40628363924](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40628363924) passed, but it is not the native build result.

The combined audit still deliberately leaves `MyAssertHandler`, `Com_FilterPath` and `I_strnicmp` visible as unresolved engine services. No full `FS_InitFilesystem()` execution, real licensed FastFile/map load, renderer scene, physical ARM64 game-loop run or touch-driven combat is proven. The APK remains diagnostic only; PR #4 stays open and unmerged.


## Phase BN — repair stale ARM64 provider gate and emulator probe shell syntax (2026-10-28)

Inspected the latest CI before changing code. The previous native ARM64 run [40628489327](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40628489327) failed after the combined object had already compiled: the gate still required `MyAssertHandler` and `I_strnicmp` to remain undefined even though the real HunkUser/StringEd/q_shared provider set now defines them. The same run's defined-symbol listing showed both providers as `T`; `Com_FilterPath` remains undefined and is kept as an explicit next dependency. This was a stale assertion, not a reason to add a stub.

The emulator run [40628489402](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40628489402) compiled and started the JNI diagnostic, and logcat showed the existing ZIP/IWD probe markers passing, but the shell reported an unterminated Python heredoc at line 53. Two process-substitution blocks ended with `PY)` on one line; Bash requires the heredoc delimiter alone, followed by the closing `)` on its own line.

Changes committed on `feature/iw3-native-android-arm64-20261025`:
- Native workflow now requires `MyAssertHandler` and `I_strnicmp` in the combined defined-symbol report and rejects them if still undefined; it separately requires `Com_FilterPath` to remain visible as unresolved. No missing service is stubbed.
- Fixed both Python heredoc terminators in `tools/iw3_android/run_emulator_probe.sh`.
- Updated the HunkUser and filesystem-startup regression assertions to match the real provider contract.
- Added a regression that runs `bash -n` against the emulator probe and rejects the malformed `PY)` terminator.

The fresh CI runs triggered by these changes are the authority for whether the fixes pass; prior failed runs are retained as evidence and are not reclassified. This phase does not start `FS_Startup` in the Activity, mount licensed game data, load a FastFile/map, render a 3D scene, or prove gameplay on physical ARM64. The JNI APK remains diagnostic only; keep PR #4 open and unmerged.


### Phase BN validation update — corrected gate and emulator probe now pass (2026-10-28)

Fresh CI completed for code head `e752f09b15c50fcc93441a858237a2739f140cbd`:

- [Native ARM64 source/link audit 40629029559](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029559) — PASS. Python suite: 136 tests; CTest Release: 16/16; ASan/UBSan CTest: 16/16; the complete original `g_runframe.cpp` archive, filtered-file archive, original FS/IWD/StringEd/Hunk providers, and combined AArch64 relocatable link passed. Artifact [12790975916](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029559/artifacts/12790975916) contains native modules and audit reports, not an APK.
- [Source preflight 40629029599](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029599) — PASS.
- [JNI ARM64 diagnostic package 40629029660](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029660) — PASS for AArch64 ELF/JNI/package/signature checks only. Artifact [12790129433](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029660/artifacts/12790129433) remains diagnostic, not a playable game.
- [Android x86_64 emulator probe 40629029553](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029553) — PASS after the heredoc fix. Log artifact [12791190363](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40629029553/artifacts/12791190363) records the original ZIP/IWD parser and file/searchpath read paths executing, touch DOWN/UP read back through the authentic `usercmd_s` adapter, attack/sprint/slide button masks, and Activity pause/resume.

The emulator evidence still explicitly reports `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. The ARM64 link gate now correctly treats `MyAssertHandler` and `I_strnicmp` as resolved original providers while retaining `Com_FilterPath` as an unresolved real service. The full FS startup runtime remains uninvoked; no licensed FastFile/map load, original renderer scene, or playable Android APK is proven. Keep PR #4 open and unmerged.


## Phase BO — resolve original filesystem wildcard service for the ARM64 startup audit (2026-10-28)

The latest successful native audit still intentionally left `Com_FilterPath` unresolved while compiling the authentic `FS_ListFilteredFilesInLocation()` body. The vendored KisakCOD source slice declares `Com_Filter` and `Com_FilterPath` in `q_shared.h`, but neither provider exists in the available `universal/q_shared.cpp` / `qcommon/common.cpp` source. The original filesystem therefore could not pass its combined dependency audit without a provider.

This pass adds `android/iw3-native/iw3_android_filter.cpp`, a portable provider for the declared engine service using the id Tech 3 wildcard semantics (literal runs, `*`, `?`, bracket ranges and the original double-open-bracket branch; path filtering normalizes backslash/colon to slash and preserves the engine's `MAX_QPATH-1` truncation). This is explicitly a missing helper port, not an extracted KisakCOD body and not a substitute filesystem/renderer/game loop. It fails closed on null input, malformed character classes and overlong literal runs; case folding passes unsigned characters to `toupper` to avoid undefined behavior.

Regression coverage is both behavioral and structural: a native CTest exercises wildcard, range, case-sensitivity, separator normalization, malformed patterns and bounds; Python preflight verifies that the provider is compiled and included in the combined AArch64 audit. The native workflow now links `libiw3_sp_filter.a` into the relocatable original FS/Dvar/IWD/ZIP/FS_ReadFile/Hunk/StringEd/filtered-file object and requires both `Com_Filter(` and `Com_FilterPath(` to be defined and absent from the undefined-symbol list. The stale HunkUser regression was updated to reflect this new provider contract.

**Validation status at documentation time:** the new commits have triggered source preflight, host/ASan/UBSan, Android ARM64 link audit, JNI diagnostic and x86_64 emulator jobs. They are not counted as green until the new runs finish. Even if all pass, the combined object is only dependency evidence: the Android Activity still does not invoke full `FS_Startup()/FS_InitFilesystem()`, mount licensed game IWD/FastFiles, load a map, render a scene, or execute player/weapon/actor gameplay on physical ARM64. The JNI APK remains diagnostic only. PR #4 remains open and unmerged.


## Phase BP — original warning service and Android log sink (2026-10-28)

The latest code head before this pass was `180f55bb3a5a9b3a8445129272560caad2413c36`. Its successful native audit still deliberately listed `Com_PrintWarning` as unresolved from the authentic `FS_AddIwdFilesForGameDirectory()` body. The provider exists in KisakCOD's `src/qcommon/common.cpp`, but that translation unit also pulls in client, renderer, script, sound and Windows-specific services, so compiling the whole file into the filesystem audit is not a valid shortcut.

This pass stages the original `Com_PrintWarning(int, const char*, ...)` body from `common.cpp` and makes only narrow platform adaptations:
- the original `"^3"` warning prefix and output type `2` are preserved;
- the MSVC `_vsnprintf` spelling is changed to bounded `std::vsnprintf`, with `va_end` added;
- the two-byte prefix setup is expressed directly so this isolated warning function does not import an unrelated `I_strncpyz` dependency.

The platform sink defines `Com_PrintMessage` for this audit boundary: Android routes channel/severity to logcat, and host tests route it to stderr. This is logging glue only; it does not provide game state, filesystem behavior, rendering, or gameplay. The full `common.cpp` translation unit is not linked.

The native workflow now compiles `libiw3_sp_com_print_warning.a`, includes it in the ARM64 relocatable FS-startup and combined startup/Dvar/IWD audits, and requires `Com_PrintWarning` to be defined rather than falsely treating it as a remaining unresolved service. A host CTest checks that the formatted warning reaches the platform sink. Python regressions verify source provenance, the exact portability edits, and that all runtime/gameplay evidence flags remain false.

The first ARM64 combined-link attempt exposed a duplicate diagnostic `Com_PrintWarning` in `iw3_android_iwd_directory_io.cpp`. That fallback is now guarded by `IW3_IWD_DIRECTORY_LINK_AUDIT`, so it remains available only to the narrow diagnostic path and cannot collide with the staged original warning body in the combined engine audit. A regression pins this separation.

The first JNI integration rerun then showed that the app's Gradle CMake configure does not provide `IW3_EXTRACTED_COM_PRINT_WARNING`. The audit target and its host CTest are now conditional on that extraction variable: the dedicated native-audit workflow supplies it and must compile/link it, while the separate JNI diagnostic build is not forced to generate an audit-only source file. This preserves the distinction between the audit target and the diagnostic APK.

**Validation is pending until the fresh CI runs for the new commit finish.** This closes one logging dependency only. The startup audit still is not a full runtime link; the Android Activity does not invoke `FS_Startup()/FS_InitFilesystem()`, mount licensed game FastFiles, load a map, render a 3D scene, or run player/weapon/actor gameplay on a physical ARM64 device. Keep PR #4 open and unmerged; the JNI package remains diagnostic only.



## Phase BQ — original q_shared startup string providers (2026-10-28; ARM64 and emulator diagnostics green; gameplay pending)

The prior startup+Dvar audit still showed `I_strncat` and `Com_sprintf` as missing providers. `I_strncpyz` and `I_stricmp` already come from the original IWD-services extraction in the expanded graph, so adding second copies of them would be incorrect. This pass stages only the two still-missing bodies from `third_party/KisakCOD/src/universal/q_shared.cpp`, rather than adding handwritten engine substitutes.

- Added `tools/iw3_android/prepare_real_engine_q_shared_strings.py`. It extracts original `I_strncat` and `Com_sprintf`, recording source/body hashes without modifying vendored `q_shared.cpp`. The existing original IWD-services archive remains the sole provider for `I_strncpyz` and `I_stricmp`.
- Only `Com_sprintf` receives a narrow portability adaptation: MSVC `_vsnprintf` becomes bounded `std::vsnprintf`; a zero-sized destination returns `-1` before indexing; and C99's required-length result is translated back to the original `-1`-on-truncation contract. The original `I_strncat` body is staged verbatim.
- Added a native CTest for the original append call contract and the formatter's normal, truncated and zero-size cases, plus Python source-provenance and workflow-wiring regressions. The host test supplies only the already-audited `I_strncpyz` dependency; the ARM64 combined object uses the original IWD-services provider.
- The native workflow builds `libiw3_sp_q_shared_strings.a`, includes it in the combined AArch64 relocatable audit, and requires `I_strncat`, `I_strncpyz`, `I_stricmp` and `Com_sprintf` to be defined and absent from that object's undefined-symbol list. The JNI Gradle configuration does not receive this audit-only extraction and the archive is not linked into the diagnostic APK.

The first ARM64 link attempt exposed duplicate definitions: the new archive duplicated `I_strncpyz`/`I_stricmp` already present in the original IWD-services archive, and the directory adapter's diagnostic `Com_sprintf` collided with the original body. The staged provider is now limited to the two missing functions, and the diagnostic formatter is guarded out when `IW3_IWD_DIRECTORY_LINK_AUDIT` is defined. A regression pins this separation.

Validation for code HEAD `dbc3c3b260303df98849f219c0b2f8db4ac97819`:
- Source preflight: passed (run `40644461428`).
- Host Release CTest: 19/19 passed.
- Host ASan/UBSan CTest: 19/19 passed.
- Native Android ARM64 compile and combined-link audit: passed (run `40644453400`), including `IW3_ORIGINAL_Q_SHARED_STRING_SERVICES_AARCH64_LINK_GREEN` and `IW3_ORIGINAL_SOURCE_ANDROID_ARM64_ELF_GREEN`.
- JNI diagnostic package build: passed (run `40644453404`); artifact `12796668334` is explicitly labeled NOT A GAME.
- Emulator diagnostic: passed (run `40644453405`); artifact `12796234478` contains the native execution log. The evidence validates original ZIP32/IWD fixture paths and touch-to-`usercmd_s` readback on an x86_64 emulator, but explicitly records `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false` and `gameplay_proven=false`.

This is a bounded dependency-closure step only. The combined object still retains unrelated engine command/parser, shutdown, CD-key and Dvar services; the Activity still does not invoke `FS_Startup()/FS_InitFilesystem()`, mount real game IWD/FastFiles, load a map, render the original scene, or run touch-driven gameplay on physical ARM64. `IW3_PLAYABLE_APK=false` remains explicit. PR #4 stays open and unmerged.


## Phase BR — original Com_Printf service for Android filesystem startup (2026-10-28)

The latest ARM64 startup/Dvar/IWD audit still had the authentic `FS_Startup()` call to `Com_Printf(channel, fmt, ...)` unresolved. KisakCOD provides that body in `src/qcommon/common.cpp`; compiling all of `common.cpp` would pull in unrelated client, renderer, script and platform dependencies.

This pass stages only the original `QDECL Com_Printf` body. The sole source adaptation replaces MSVC `_vsnprintf` with bounded `std::vsnprintf` and calls `va_end`; it preserves the original channel, message type 0 and `Com_PrintMessage` sink. The sink remains the existing Android logcat / host-stderr platform boundary. The full `common.cpp` translation unit is not linked.

- Added `tools/iw3_android/prepare_real_engine_com_print_printf.py` with source/body hashes and explicit `playable_apk=false`, `filesystem_startup_invoked=false` evidence.
- Added a native CTest that invokes the extracted original formatter and checks the formatted message reaches the existing sink.
- The ARM64 audit links the new provider alongside the original FS startup and warning archives and fails if `Com_Printf` remains undefined.
- Added source-provenance and workflow-wiring regressions.

**Status at commit time:** CI is required to validate this provider. Even after it passes, this closes one startup logging dependency only; the combined graph still has original command/parser, Dvar startup and fatal-error services unresolved. The Android Activity still does not invoke `FS_Startup()/FS_InitFilesystem()`, mount real game IWD/FastFiles, load a map, render the original scene, or run touch-driven gameplay on physical ARM64. The JNI package remains diagnostic only. Keep PR #4 open and unmerged.


**Follow-up link correction:** the first ARM64 attempt exposed a duplicate `Com_Printf` definition from `iw3_android_dvar_log.cpp` when the authentic extracted provider was combined with the dvar archive. The fallback is now compiled only when the original provider is absent. The Dvar audit links the original `Com_Printf` plus the existing `Com_PrintMessage` sink and checks the combined object, rather than claiming the fallback is the original provider. The failed run is retained as evidence and is not counted as a pass.

## Phase BS — native-width filesystem string dvars in original command paths (2026-10-28)

While tracing the next command-subsystem dependency needed for a real Android bootstrap, the original `src/qcommon/cmd.cpp` still contained two path constructions in `Cmd_Dumpraw_f()` that cast `fs_basepath->current.integer` to `char *`. This reads a string-valued Dvar through its 32-bit integer union member and can truncate the path pointer on LP64.

The original KisakCOD source now uses `fs_basepath->current.string` for both the `raw\\` and `zone\\english\\` directory roots. The paths, command behavior and formatting are otherwise unchanged. This is a source portability correction, not a substitute command system, and `cmd.cpp` is **not yet part of the Android runtime link**.

Regression coverage in `tests/test_iw3_android_command_string_dvar_abi.py` scopes the check to the original dump command, requires both string-member accesses, rejects the old integer-pointer casts, and ensures numeric dvars elsewhere remain allowed.

- Engine-source correction: [`4b47d9e`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/4b47d9e382e292b8e4b120b5c5c734f9e72a63b8).
- Regression test: [`01c6366`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/01c6366103dda43012a41cc8c15250c96b5e9056).
- Native Android source/link workflow [40648357515](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357515) passed on code head `01c6366103dda43012a41cc8c15250c96b5e9056`: Python suite **149 tests passed**, Release CTest **20/20**, ASan/UBSan CTest **20/20**, and the original-source ARM64 ELF/link audit passed. Artifact [12798521789](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357515/artifacts/12798521789) contains source modules and audit reports, **not an APK**.
- JNI ARM64 diagnostic packaging [40648357468](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357468) passed compile/package/signature checks; artifact [12798775741](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357468/artifacts/12798775741) is explicitly named `NOT-A-GAME`.

Validation follow-up: in the x86_64 Android emulator run [40648357598](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357598), the build, boot/probe, evidence validation and artifact-upload steps all completed successfully; the overall workflow was later marked cancelled during concurrency cleanup, so this is component-level log evidence rather than an overall green run. The Windows SP executable build step in [40648357628](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357628) completed successfully, but that workflow was cancelled during concurrency cleanup; it is not counted as a completed full Windows validation. The temporary offline SP killhouse workflow [40648357580](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648357580) was cancelled before its launch/weapon/actor inspection step (that step was skipped), so it provides no new gameplay evidence.

**Scope boundary:** the correction addresses two genuine native-width pointer reads in original command code. It does not close the startup command/parser service graph or integrate `FS_Startup()/FS_InitFilesystem()` into the Android Activity. The native audit itself explicitly reports `IW3_FS_STARTUP_RUNTIME_INVOKED=false`, `IW3_REAL_GAME_DATA_MOUNTED=false`, and `IW3_PLAYABLE_APK=false`. Licensed FastFiles/map loading, original renderer output, and touch-driven player/weapon/actor gameplay on physical ARM64 remain unproven. Keep PR #4 open and unmerged.


## Phase BT — Android emulator touch-coordinate regression (2026-10-28)

The latest x86_64 emulator attempt [40648979506](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648979506) launched the diagnostic Activity and logged successful original ZIP/IWD smoke markers, but failed before touch injection because the hosted Quickstep launcher was showing its named ANR dialog. The uploaded UIAutomator XML in artifact [12799595100](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40648979506/artifacts/12799595100) records the Wait button at `[377,644][1770,776]` while the captured landscape screenshot is 2280×1080. The old probe incorrectly scaled node bounds by the maximum extent of nodes visible inside the modal, producing a tap at y=911—outside the button. This was a probe-coordinate defect, not gameplay evidence.

Fix on the feature branch:
- Added `tools/iw3_android/parse_touch_target.py`, which reads the real screenshot dimensions, uses UIAutomator's active-display bounds directly, prioritizes the explicitly named Quickstep Wait button over any hidden app node, and declines to tap out-of-frame bounds.
- Added `tests/test_iw3_android_emulator_touch_target.py` covering the captured Wait coordinates, the app touch view, modal priority, out-of-frame nodes and invalid display dimensions.
- Refactored both target-selection sites in `run_emulator_probe.sh` to use the shared helper.
- Updated the older touch-accessibility and ZIP workflow regressions to check the shared helper contract rather than the removed embedded parser.

Relevant commits: [5640ef2](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/5640ef2aeb5b7b1a0b13135b407b17290d77df83), [36af5f7](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/36af5f72ed6ab94c2d372f3db4ca7ab6fa95bb6d), [7638968](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/76389685f0879d303470aba26c3009c063a1cab7), [cad0f05](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/cad0f051efafc337a6e77493089b2b6c92d6a2ec), [f688709](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f68870919d4e70fe813118b9b4f2d6ce5f53c20c).

Validation on code HEAD `f68870919d4e70fe813118b9b4f2d6ce5f53c20c`:
- Native original-source ARM64 audit [40652578550](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578550) — PASS, including the full original SP `G_RunFrame` ARM64 archive and filesystem/IWD dependency audits.
- Source preflight [40652578468](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578468) — PASS.
- JNI ARM64 diagnostic build [40652578527](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578527) — PASS for compilation, ELF/JNI/package/signature checks only.
- Emulator touch run [40652578478](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578478) was still running at the time this section was written; do not count it as passed until the final workflow conclusion is green.

Scope remains strict: the original frame archive is not linked into the JNI diagnostic APK. The Android Activity still does not execute full `FS_Startup()/FS_InitFilesystem()`, mount licensed game IWD/FastFiles, load a real map, render the original scene, or execute touch-driven gameplay on physical ARM64. `IW3_PLAYABLE_APK=false`; PR #4 stays open and unmerged.


### Phase BT validation follow-up

The fresh Android emulator run [40652578478](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578478) completed **PASS** on code HEAD `f68870919d4e70fe813118b9b4f2d6ce5f53c20c`. Its log now records the correct recovery coordinate `x=1073 y=710` for the Wait button, then selects the app view at `x=1140 y=540`. ADB DOWN/UP gestures produced native `usercmd_s` snapshots for attack (`buttons=1`), sprint (`buttons=2`) and slide+sprint chord (`buttons=514`); the runtime-evidence verifier completed and emitted `IW3_ORIGINAL_CPP_EXECUTED_INSIDE_ANDROID_EMULATOR_GREEN`. Artifact [12800318089](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578478/artifacts/12800318089) is the new diagnostic log/evidence package, **not a game**.

JNI ARM64 packaging [40652578527](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578527) and the native ARM64 audit [40652578550](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40652578550) both completed PASS. The emulator run remains x86_64 and validates the adapter only; it does not make those input events part of the original engine frame. No original renderer, map/FastFile startup, physical ARM64 gameplay or playable APK is demonstrated.

## Phase BV — preserve the native Hunk pointer through collision-map wrapper (2026-10-28)

Reviewed PR #4 head `a0ef7d7` and the completed CI jobs before editing. The native ARM64 source/link audit [40667252800](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40667252800) and JNI diagnostic packaging [40667252721](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40667252721) passed their stated gates. Two separate failures exposed different issues:

- The Android emulator build [40667252665](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40667252665) stopped before boot because Maven Central returned HTTP 429 while Gradle resolved ASM/JDOM and other transitive dependencies. The native emulator execution step was skipped; this run provides no new gameplay evidence.
- The Windows SP build [40667252700](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40667252700) failed with MSVC C2440 in `src/qcommon/cm_load_obj.cpp`: `CM_Hunk_AllocateTempMemoryHigh` still declared a `uint32_t` return while the corrected original `Hunk_AllocateTempMemoryHigh` now returns a pointer. The temporary killhouse build failed at the same mismatch.

Fix applied to the vendored original source:
- Changed `CM_Hunk_AllocateTempMemoryHigh` to return `uint8_t*`, matching the original allocator declaration in `universal/com_memory.h` and its implementation. The wrapper returns the allocation pointer; the caller stores it as a pointer to the leaf-brush copy. No allocator behavior or collision-map algorithm was replaced.
- Extended `tests/test_iw3_android_hunk_temp.py` to pin the wrapper signature, direct return and pointer-typed consumer, preventing this downstream ABI mismatch from returning.

Validation status for this new fix is **pending** until the fresh native and Windows SP workflows finish. The prior ARM64 audit remains a pass for its earlier source head only; it does not validate this wrapper edit. The JNI artifact is diagnostic only. Full Android FS startup, real IWD/FastFile/map loading, original renderer output, touch-driven gameplay and physical ARM64 execution remain unproven. Keep PR #4 open and unmerged.

### Phase BV validation follow-up — 2026-10-28

The fresh workflows for the Phase BV source/test tree at 149f9d7c1106b662076c25e06f781ab1c2d3aeab have completed. This documentation-only follow-up does not change the validated C++ or regression-test files.

- [Native Android ARM64 source/link audit, run 40675222604](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222604) — **PASS**. Python source regressions: 161 passed. Release CTest: 20/20. ASan/UBSan CTest: 20/20. NDK AArch64 compilation and the existing filesystem/Dvar/Hunk/G_RunFrame relocatable audits passed. The log still explicitly reports IW3_PLAYABLE_APK=false and leaves original frame services unresolved.
- [JNI ARM64 package, run 40675222783](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222783) — **PASS for diagnostic build/package/signature only**. APK SHA-256: cf87b2cd92dadfe7cc2a8bf764e55935688d2bd173fa44f42df5aebc3010f9f7. This APK contains the existing JNI diagnostic path; it is not the full engine or a playable game.
- [Android x86_64 emulator probe, run 40675222585](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222585) — **PASS for diagnostic execution**. Original ZIP32 stored/deflate parsing, fixture IWD indexing, search-path insertion, directory scan, IWD read/handle lifecycle and touch DOWN/UP → usercmd_s were observed; pause/resume was also recorded. The evidence explicitly says arm64_device_execution_proven=false and gameplay_proven=false. Artifact [12810167159](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222585/artifacts/12810167159) is logs/evidence, **NOT THE GAME**.
- [Windows SP source build, run 40675222953](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222953) — **PASS**. The prior MSVC C2440 mismatch in CM_Hunk_AllocateTempMemoryHigh is gone after aligning the wrapper's return type with the pointer-returning original allocator.
- [Windows offline SP killhouse diagnostic, run 40675222620](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222620) — workflow **PASS**, but the gameplay assertions are deliberately partial: the source-built process stayed alive at 40 seconds, player/entity and a registered bullet weapon were present, and actor AI think ran; actual_weapon_fire_callback=false, bullet_fire_dispatched=false, damage/pain/death callbacks and weapon-fired verification were also false. This is not proof of firing/damage/death and is not Android evidence. Metadata-only artifact: [12810821404](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222620/artifacts/12810821404).
- [Static source preflight, run 40675222713](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40675222713) — PASS; it is a source preflight, not a gameplay test.

The previous emulator attempt [40667252665](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40667252665) failed before boot because Maven Central returned HTTP 429; that transient dependency-resolution failure did not recur in the fresh emulator run. It was not treated as an engine failure or a game pass.

**Acceptance boundary unchanged:** the Android Activity still does not execute the complete original FS_Startup()/FS_InitFilesystem() graph, mount licensed IWD/FastFiles, load an actual map, display the original renderer, or execute original player/weapon/actor gameplay on physical ARM64. No playable ARM64 APK exists. Keep PR #4 open and unmerged.


### Phase CA — original q_parse/session services staged into the filesystem-startup ARM64 audit (28 Oct 2026)

The next concrete dependency exposed by the staged `FS_Startup` / StringEd chain was the original token parser. Added `tools/iw3_android/prepare_real_engine_q_parse.py`, which extracts the original `Com_InitParse`, `Com_InitParseInfo`, `Com_BeginParseSession`, `Com_GetParseThreadInfo`, `Com_EndParseSession`, `Com_SetCSV`, `Com_GetCurrentParseLine`, `Com_UngetToken`, parse-mark helpers, `Com_Parse`, `Com_ParseExt`, `SkipWhitespace`, `Com_ParseCSV`, and `Com_ParseOnLine` from `third_party/KisakCOD/src/universal/q_parse.cpp`. The original four-context `g_parse` state and punctuation table are extracted from the same upstream file and SHA-256 recorded. The vendored source is not rewritten.

The slice no longer includes upstream `qcommon/threads.h`, which imports Windows-only headers. It declares only the existing thread-selector ABI; the actual thread services remain unresolved rather than being implemented in the engine archive. Added `iw3_sp_q_parse` as a compile/audit archive and a host CTest that executes the extracted original parser against quoted tokens, line comments/CRLF line counting, one-token unget, and CSV fields. The host harness supplies thread selectors and fail-closed fatal-error sinks only; those helpers are not part of the generated engine source or Android runtime.

The native ARM64 workflow now includes the parser archive in the relocatable filesystem-startup/StringEd link and checks the combined object for parser function definitions. It does not add the parser archive to the JNI diagnostic target.

**Verified evidence on code commit `f6a8389aa8af4f582af27b781e3d4b26c2b3d0f5`:**

- Native source/ARM64 audit [run 40684658822](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40684658822): **21/21 CTest Release and 21/21 CTest with ASan/UBSan passed**, including `iw3_original_q_parse_host_runtime`; the NDK build produced the parser archive; the combined startup link emitted `IW3_ORIGINAL_Q_PARSE_AARCH64_LINK_GREEN` and `IW3_ORIGINAL_FS_STARTUP_AARCH64_RELOCATABLE_LINK_AUDIT_GREEN`.
- Source preflight [run 40684658933](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40684658933): passed.
- Audit artifact [12813988767](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40684658822/artifacts/12813988767): original-source modules and reports only; **not an APK**.

During this pass, the first native attempt caught a Windows-only thread-header include, then the host link caught the fatal `Com_ScriptErrorDrop` path referenced by the original unget routine. The include was replaced with ABI declarations; the host harness now aborts if the exceptional double-unget error path is reached. A subsequent ARM64 audit initially inspected the startup archive's symbol list instead of the combined object's list; that audit was corrected to capture and inspect the combined definitions, and the latest run passed. These intermediate failures are preserved in Actions history.

**Scope boundary:** the parser functions now compile for ARM64 and execute in the host regression, and their definitions participate in the relocatable startup audit. This still does **not** invoke `FS_Startup()` or `FS_InitFilesystem()` in Android. Original `Com_Error` / fatal parser reporting and thread-selection services, command argument state (`Cmd_Argc` / `Cmd_Argv`), the full Dvar and filesystem service graph, actual IWD mounting, licensed FastFiles/map loading, renderer, live touch-to-frame integration, and gameplay remain incomplete. The CI report continues to state `IW3_PLAYABLE_APK=false`; no playable APK exists. Keep PR #4 open and unmerged.


### Phase CB — guard the original FS_Startup against an empty home path (28 Oct 2026)

A focused runtime test exposed a portability hazard in the authentic `FS_Startup()` body: when `fs_homepath` is explicitly empty but `fs_basepath` is set, the original path-registration branch added `gameName` a second time with an empty OS root. On Android, the rooted POSIX adapter must reject that relative/empty search path; registering it also creates an invalid searchpath node that can shadow or alias unrelated paths.

The original `third_party/KisakCOD/src/universal/com_files.cpp` now keeps the normal `<basepath>/<gameName>_shared` registration, but only registers the corresponding homepath `gameName` directory when `fs_homepath->current.string[0] != '\\0'`. This is a narrow guard in the real engine function, not a substitute filesystem implementation.

The source-staging generator `tools/iw3_android/prepare_real_engine_fs_startup.py` now requires that guard and records `empty_homepath_search_registration_skipped=true`. The host harness `fs_localized_path_native_test.cpp` now executes the extracted original `FS_RegisterDvars()` and `FS_Startup()` bodies with only Dvar/platform services supplied by the harness, forces an empty `fs_homepath`, and asserts:
- the original basepath remains `/private/iw3`;
- all 14 registered searchpath nodes have a non-empty base path;
- the expected seven basepath directory probes and fourteen IWD scan calls occur;
- original command/CD-key registration side effects are reached exactly once.

The Python regression verifies that the source guard, extraction requirement, and executable host scenario remain aligned.

**Verified on code commit `b49d75f35d75ebd9c6dfafcf8f650419d0acb27a`:**
- Source preflight [run 40688699733](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699733): PASS.
- Native ARM64/source audit [run 40688699751](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699751): PASS; CTest Release **21/21**, CTest with ASan/UBSan **21/21**; original filesystem startup, IWD, Hunk, StringEd and frame compile/link gates passed. Artifact [12816331756](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699751/artifacts/12816331756) contains native modules/reports, **not an APK**.
- JNI ARM64 diagnostic build [run 40688699908](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699908): PASS for compile/package/signature. Artifact [12816182436](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699908/artifacts/12816182436) is **diagnostic only, not the game**.
- Android emulator runtime probe [run 40688699875](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699875): PASS on an Android x86_64 emulator. Log evidence records original ZIP/IWD fixture execution, original file read paths, touch DOWN/UP and sprint/slide input reaching the `usercmd_s` adapter, and lifecycle pause/resume. Artifact [12816725114](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40688699875/artifacts/12816725114) is a log/evidence archive, **not a game**.
- The emulator evidence explicitly keeps `original_upstream_fsh_table_integrated=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`.

**Scope boundary:** this proves the original `FS_Startup()` path-registration body executes in a host regression with narrow service harnesses, and that the corrected source compiles in the existing ARM64 audit. It does not invoke the complete `FS_InitFilesystem()` chain in the Android Activity, link the full filesystem/Dvar/runtime service graph, mount licensed FastFiles, load a real map, render a 3D scene, or run weapons/actors on a physical ARM64 device. The Android JNI artifact remains diagnostic; `IW3_PLAYABLE_APK=false`. PR #4 stays open and unmerged.

## Phase CC — original command-argument accessors in the startup audit (2026-10-28)

The next concrete dependency edge was the original `Cmd_Argc()` / `Cmd_Argv(int)` pair used by the filesystem and Dvar startup graph. Added `tools/iw3_android/prepare_real_engine_cmd_args.py`, which extracts the two function bodies from `third_party/KisakCOD/src/qcommon/cmd.cpp` and records source/body/generated SHA-256 hashes. It does not extract or define `cmd_args`: that state remains owned by the complete upstream `cmd.cpp` translation unit, so the relocatable audit continues to expose the missing command-subsystem integration instead of concealing it with duplicate state.

A host test now executes those exact accessor bodies against the real `CmdArgs` declaration from `cmd.h`, covering ordinary arguments, nested argument frames, and the original empty-string result for an out-of-range index. CMake builds the accessor archive and host test when the source-audit workflow stages it. The ARM64 workflow links that archive into the filesystem-startup, Dvar, and IWD dependency audits and requires both accessors to be defined while requiring `cmd_args` to remain visibly unresolved.

Code/evidence commits:
- `330aa4f` — original-source accessor extractor.
- `440320a` — native accessor regression.
- `d3a961b` — Python wiring regression.
- `b49e005` — CMake archive and host test.
- `1fe9c9c` — ARM64 extraction/link checks and evidence upload.
- `b30620a`, `35979e8`, `8fb21d7` — corrected stale workflow-shape assertions after CI caught them.

Validation confirmed on the latest native audit run:
- Preflight: passed.
- Python preflight suite: 171 tests passed.
- CTest Release: 22/22 passed.
- CTest ASan/UBSan: 22/22 passed.
- Original command accessor archive compiled for Android ARM64.
- Relocatable startup/Dvar audit emitted `IW3_ORIGINAL_CMD_ARG_ACCESSORS_AARCH64_LINK_GREEN`; `Cmd_Argc()` and `Cmd_Argv(int)` are defined, while `cmd_args` remains unresolved as intended.

Native CI evidence: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40692472320  
Preflight evidence: https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40692472329  
ARM64 audit artifact (compiled objects/reports only, not a game APK): https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40692472320/artifacts/12816838973

The Android JNI integration build also completed successfully in run 40692472477, but it remains a diagnostic/build check, not proof that the original runtime is linked or playable. The emulator execution and Windows SP smoke were still running when this section was first recorded.

**Remaining boundary:** `cmd_args` storage/initialization still belongs to the full original command subsystem. This accessor archive is deliberately excluded from JNI and is not a substitute runtime. `FS_Startup()` has not been demonstrated running in the app; no real FastFile/map load, original renderer, complete touch-to-game loop, weapon fire/damage, or physical ARM64 device gameplay has been proven. `IW3_PLAYABLE_APK=false` remains the status.


## Phase CD — original Com_SkipRestOfLine parser service (28 Oct 2026)

The latest ARM64 startup audit already staged the authentic `q_parse.cpp` parser/session bodies, but the combined filesystem-startup dependency list still named `Com_SkipRestOfLine(const char **)` as missing. The original implementation is in the same vendored `src/universal/q_parse.cpp`; it advances to the next LF, updates the active parse session's line counter, and safely leaves a null input unchanged.

This pass extends `tools/iw3_android/prepare_real_engine_q_parse.py` to extract that exact upstream body alongside the existing parser functions. It does not add a new parser implementation or alter the vendored function. The native parser regression now covers:
- skipping a CRLF-terminated line and advancing the original parse-line counter exactly once;
- continuing to parse the next line using the same original parser/session state;
- reaching NUL when the input has no trailing newline;
- preserving a null input pointer.

The ARM64 workflow now requires `Com_SkipRestOfLine` to be defined and absent from the unresolved-symbol report in both the parser and combined startup audits, and emits `IW3_ORIGINAL_Q_PARSE_SKIP_LINE_AARCH64_LINK_GREEN` only after those checks pass. The parser archive remains an audit artifact; it is not linked into the JNI diagnostic APK.

Code changes:
- `tools/iw3_android/prepare_real_engine_q_parse.py` — original-body extraction and provenance fields.
- `android/iw3-native/parser_native_test.cpp` — host runtime behavior regression.
- `tests/test_iw3_android_q_parse.py` — source provenance, test wiring and CI-gate assertions.
- `.github/workflows/iw3-original-native-android.yml` — combined-link requirements.

**Verified on code commit `c6544a303dc94bd9e6cf9282dbfd29f5b8d75ceb`:** source preflight [run 40698933518](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40698933518) passed. The native ARM64/source audit [run 40698933224](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40698933224) passed after its cancelled first attempt was rerun: Release CTest **22/22**, ASan/UBSan CTest **22/22**, the original parser host runtime regression passed, and the Android NDK AArch64 link audit emitted `IW3_ORIGINAL_Q_PARSE_SKIP_LINE_AARCH64_LINK_GREEN`. The log records the original `Com_SkipRestOfLine(const char **)` body hash and its definition in the combined startup audit. Native evidence artifact [12820473331](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40698933224/artifacts/12820473331) contains compiled objects and reports, **not an APK**. The JNI diagnostic build was still in cleanup at the time of this update; the emulator run [40698933244] was cancelled before producing a job/evidence artifact and is not counted as passed.

**Scope boundary:** this closes one authentic parser dependency if the new link gate passes. It does not link the full command-state object, full Dvar registry, all filesystem/platform services or the original frame into a working Android runtime. It does not invoke the complete `FS_InitFilesystem()` path in the app, mount licensed FastFiles, load a map, render the original 3D scene, or demonstrate touch-driven weapons/actors on a physical ARM64 device. `IW3_PLAYABLE_APK=false`; keep PR #4 open and unmerged.


### Phase R — original command-argument state storage joins the ARM64 audit (28 Oct 2026)

The latest dependency inspection showed that the original **Cmd_Argc()** and **Cmd_Argv()** bodies were defined in the relocatable startup/Dvar audit, but their genuine global state, **cmd_args**, remained unresolved. The state is declared in the vendored **src/qcommon/cmd.cpp** as **CmdArgs cmd_args;**; it is not a synthetic runtime object.

Changes on the feature branch:

- **tools/iw3_android/prepare_real_engine_cmd_args.py** now extracts that exact declaration from the original source, requires exactly one match, hashes the declaration, and stages it beside the unchanged original **Cmd_Argc** / **Cmd_Argv** bodies. The generator imports **re** for the strict source check.
- **android/iw3-native/cmd_args_native_test.cpp** no longer defines its own **CmdArgs cmd_args{}**. The host regression now consumes the extracted original global and checks its static zero-initialized state before exercising nested argument access.
- **tests/test_iw3_android_cmd_args.py** checks single-source ownership, the host-test setup, and the explicit state-link gates.
- **.github/workflows/iw3-original-native-android.yml** now requires **cmd_args** to be present in the defined-symbol table and absent from the unresolved-symbol table in the startup-only, full-Dvar, and startup+Dvar relocatable combinations. This does not mean the tokenizer or command dispatcher has been integrated.

Relevant commits: **277fdf59** (extract original storage), **82edc954** (host runtime regression), **5f383cd1** (source/test gate), **70b6cd97** (CMake scope), **6e10dff6** (regex import), and **c75f475e** (restore the compact workflow from the last known-good revision and re-apply the state-resolution gates).

The first two workflow-file edits produced no-job failure runs while the native workflow file had unintentionally expanded from 777 lines to 1,638 lines. I restored the workflow from its known-good blob (**130f934d**, 777 lines) and applied the three intended checks line-by-line; the current file is 792 lines and GitHub has again scheduled the named native ARM64 workflow. Those no-job failures are not counted as successful tests.

**CI validation update (code HEAD c75f475e12ff3729ccb3b797a42f331d58663178; docs-only follow-up b2fb4ff):**

- Source/RotU preflight [run 40702723430](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702723430): **passed**.
- Native ARM64/source audit [push run 40702714391](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702714391): **passed**. The log records **174 Python tests**, CTest Release **22/22**, ASan/UBSan CTest **22/22**, AArch64 ELF/link checks, and the original full-frame compile audit. It emitted **IW3_ORIGINAL_CMD_ARGS_STATE_AARCH64_LINK_GREEN** and the Dvar/startup combined-state marker twice; the symbol is defined and no longer unresolved in the three combined objects. Native evidence artifact [12821845647](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702714391/artifacts/12821845647) contains modules/reports, **not an APK**.
- JNI diagnostic package [run 40702723527](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702723527): **passed** ARM64 compilation, package integrity and signature verification. Diagnostic artifact [12821823158](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702723527/artifacts/12821823158); APK SHA-256 **f7447ecc8342a42ca20244bf6d6adf87428424c959a7056433884810af71de34**. It remains explicitly a JNI diagnostic, not a game.
- Android x86_64 emulator probe [push run 40702714539](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702714539): still running at the native-runtime probe step when checked; no new emulator result is counted yet.
- The matching PR-triggered native audit [run 40702723429](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40702723429) was still in progress at that check. The docs-only follow-up at **b2fb4ff** triggered fresh runs; its preflight [40703034759](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40703034759) passed, while its native/JNI runs were still running.

The new source regressions, host runtime test and sanitizer checks passed. The original cmd_args storage is now resolved in the audit objects; the command tokenizer/dispatcher and actual startup invocation remain unintegrated.

**Scope boundary:** this resolves one authentic global-state dependency in the *audit objects* only. It does not include the original command tokenizer/dispatcher, does not call FS_Startup() / FS_InitFilesystem() in the Android app, and does not load licensed FastFiles or a real map. There is still no original 3D renderer, no complete touch-to-game-loop connection, no observed physical ARM64 gameplay, and no playable APK. Keep PR #4 open and unmerged.


### Phase — resolve the original player-update edge in the ARM64 frame audit (28 Oct 2026)

The latest native workflow confirmed that the complete original `G_RunFrame` object compiles for AArch64, but its first gameplay-phase service, `G_UpdatePlayer(gentity_s*)`, remained unresolved. This pass extracts the exact body from `third_party/KisakCOD/src/game/g_active.cpp` using `prepare_real_engine_g_update_player.py`. The generator verifies the source hash, preserves the function body verbatim, and checks the declarations for `SV_ReadPacket`, `CL_WritePacket`, and `Sentient_UpdatePlayerTrail` against their original KisakCOD headers.

The native ARM64 workflow now compiles that original body against the real `g_runframe.h` state definitions, then performs a relocatable link of the complete `libiw3_sp_frame.a` with the new object. It requires `G_UpdatePlayer` to be defined exactly through the provider and absent from the combined undefined-symbol table. The original packet and sentient services, plus `G_UpdatePlayerTriggers`, entity processing, and script VM services, are explicitly required to remain unresolved. This avoids replacing any gameplay callback with a stub.

The source and regression test are in `tools/iw3_android/prepare_real_engine_g_update_player.py` and `tests/test_iw3_android_g_update_player.py`; the generated source, report, object, combined object and symbol tables are retained by the native workflow artifact.

**Scope boundary:** this closes one authentic compile/link dependency edge only. It does not execute `G_UpdatePlayer`, link the player packet path, run `G_RunFrame` in Android, mount real game data, load a map, render a 3D scene, or prove weapon/actor gameplay. The JNI APK remains diagnostic and `IW3_PLAYABLE_APK=false`. Keep PR #4 open and unmerged.


### Phase — original player-trigger update edge in the ARM64 frame audit (28 Oct 2026)

The latest frame audit had the authentic `G_RunFrame` and `G_UpdatePlayer` bodies compiled for AArch64, but `G_UpdatePlayerTriggers(gentity_s*)` was still an unresolved first-phase edge. This pass adds `prepare_real_engine_g_update_player_triggers.py`, which extracts the complete original body from `third_party/KisakCOD/src/game/g_active.cpp` verbatim, hashes it, and verifies the real declarations for its math, sentient/path-node and trigger services against the vendored engine headers.

The native workflow now compiles both original player-update functions with the Android NDK and relocatably links their objects with `libiw3_sp_frame.a`. The link gate requires both functions and `G_RunFrame` to be defined, and requires the player/trigger update symbols to be absent from the combined undefined-symbol table. The actual node, claim and trigger providers remain unresolved and are explicitly checked as such; no stubs were introduced.

This phase is a source/ABI/linkage milestone only. It does not execute the functions in Android, initialize the complete server runtime, load a real IWD/FastFile/map, render a scene, or prove touch-driven combat. The emulator is not a physical ARM64 device. The JNI package remains diagnostic and is not a playable game; keep PR #4 open and unmerged until all gameplay gates are evidenced.

### Phase Y — LP64 headers blocking the original player/trigger frame compile (28 Oct 2026; CI running)

The first current-head ARM64 compile of the authentic `G_UpdatePlayerTriggers` body exposed header-level portability failures before the symbol audit could run:

- `scr_variable.h` hard-coded Win32 sizes for pointer-bearing script VM records. The original 32-bit assertions remain unchanged on 32-bit builds; LP64 now has explicit measured assertions for `VariableStackBuffer`, `VariableUnion`, `VariableValue`, `VariableValueInternal_u`, `VariableValueInternal`, `scrVarDebugPub_t`, `scrVarGlob_t`, `scr_classStruct_t`, `VariableDebugInfo`, and `ThreadDebugInfo`.
- `net_chan.h` used MSVC-only `__declspec(align(4))`; it now uses standard C++ `alignas(4)`.
- `com_math.h` used MSVC-only `__forceinline`; its three coercion helpers now use a compiler-specific `KISAK_FORCEINLINE` definition with equivalent inline intent.
- The engine's float-returning `random()` collided with POSIX `long random(void)` on Android. The original engine RNG was renamed to `Com_Random` in `com_math.h/.cpp` and all 36 source callsites in the vendored engine were updated. A source regression scans the engine tree for any remaining callsites that would accidentally bind to libc.

These are portability fixes to the original engine source; no substitute engine or no-op service was added. The LP64 script layout assertions only permit the affected translation units to compile. They do **not** prove that the script VM's pointer-bearing records, script execution, or the complete runtime are safe on ARM64; those still require end-to-end auditing and execution.

Regression added: `tests/test_iw3_android_lp64_script_layouts.py`. The first run caught a stale test expectation after the RNG symbol was made unconditional; that assertion was corrected.

Validation currently queued/in progress for code commit `6b4c799fb0ccf094b0e1f2f88f9d580ba6471aea`:
- Native ARM64 source/audit: [40736429762](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40736429762) — queued at last inspection.
- Source preflight: [40736429817](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40736429817) — queued at last inspection.
- JNI diagnostic build: [40736429746](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40736429746) — in progress at last inspection.

Do not count the intermediate failed preflight as the final result, and do not count queued runs as passing. No new evidence from this phase proves `FS_Startup()` execution, real FastFile/map loading, renderer output, live frame consumption of touch commands, weapon/actor gameplay, or physical ARM64 execution. The JNI package remains diagnostic only; PR #4 stays open and unmerged.



## Phase Z — LP64 layouts for original SP game registry records (28 Oct 2026)

The current ARM64 trigger-update compile exposed three remaining Win32-only size assertions in the authentic `game/game_public.h` after the SP game-state headers were decoupled from the D3D client/server headers:

- `client_fields_s`: Win32 `0x14`; native LP64 `0x20` (five pointer/int/enum/function-pointer fields).
- `VehicleLocalPhysics`: Win32 `0x34`; native LP64 `0x38` because its embedded `trace_t` has the native-width layout.
- `game_hudelem_field_t`: Win32 `0x1C`; native LP64 `0x28` (name plus setter/getter pointers).

The header now keeps the original 32-bit assertions under the 32-bit branch and records the measured LP64 sizes under `__LP64__`, `_LP64`, or `_WIN64`. No field order, gameplay logic, or upstream function body was changed. The regression `tests/test_iw3_android_game_public_portable_headers.py` requires each record to retain both ABI branches.

### Verified on code commit `fa4f55c70840081e05bd9eff1cc3bb3fc72ec746`

- Native ARM64 PR run [40740627238](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40740627238): **PASS**.
- Native ARM64 push run [40740618654](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40740618654): **PASS**.
- Source/preflight suite: **192 Python tests passed**.
- CTest Release: **22/22 passed**.
- CTest ASan/UBSan: **22/22 passed**.
- Android NDK compilation and ELF checks passed for the original frame and the original `G_UpdatePlayer` / `G_UpdatePlayerTriggers` bodies.
- Combined relocatable ARM64 audit emitted `IW3_ORIGINAL_G_UPDATE_PLAYER_AND_TRIGGERS_AARCH64_FRAME_EDGES_RESOLVED_GREEN`.
- Native evidence artifact [12839735900](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40740627238/artifacts/12839735900) contains compiled objects/reports only, **not an APK**.

### Scope boundary

This resolves the three header compile failures; it does not execute the frame in Android. The combined object deliberately retains real sentient/path-node/trigger and packet services as unresolved. No full Android runtime initialization, real IWD/FastFile/map load, original 3D renderer, live touch-to-frame connection, physical ARM64 execution, or weapon/actor gameplay is proven. `IW3_PLAYABLE_APK=false`; PR #4 remains open and unmerged.


## Phase AA — original entity-frame dispatch edge staged for ARM64 (28 Oct 2026)

The last green frame audit defined the original `G_RunFrame`, `G_UpdatePlayer`, and `G_UpdatePlayerTriggers`, but still listed `G_RunFrameForEntity(gentity_s*)` as an unported service. That function is central to per-entity processing: it dispatches the original missile, item, mover, think, actor-target and damage-debug paths.

This pass adds `tools/iw3_android/prepare_real_engine_g_runframe_entity.py`. It extracts both `G_RunFrameForEntityInternal` and `G_RunFrameForEntity` verbatim from the vendored `src/game/g_main.cpp`, records source/body/generated SHA-256 hashes, and verifies the external declarations and the original missile/item/mover provider definitions against their real source/header files. The isolated translation unit uses the real frame state header and the complete original `scr_vehicle_s` layout from `bg_local.h`; the `MAX_VEHICLES` constant is checked against the original `g_main.h`. No entity, weapon, script or render service implementation was stubbed.

The native ARM64 workflow now stages the extraction, compiles it with the Android NDK, checks the object is ELF64/AArch64, and performs a second relocatable link with the authentic frame/player/trigger/sentient audit objects. The new gate requires both entity-frame functions to be defined and absent from the combined undefined-symbol table. It explicitly expects real external missile/item/mover/client/script/render services to remain unresolved; this is a dependency-edge audit, not a complete runtime link.

Code commits:
- `9ca462d437811a71c3107dbfe3442718d011e159` — original-source extractor.
- `78054a26fc9a0ada4465ae6c85eb864f198b28a6` — source-preservation and provenance regressions.
- `38056da0d9cdd8d3033c045d626ba5534659366e` — isolated temporary output in the test.
- `5608385bd10ce8f41bd3462b43a92c7a69fc6ac4` — Android NDK compile/link gate and artifact retention.

### Validation completed on code tree `0997bf9e17a43893e41d060be5e071581f665cc9`

- Source preflight [40756784273](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784273): **PASS**.
- Native ARM64 source/link audit [40756784326](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784326): **PASS**. The workflow ran **206 Python tests**, CTest Release **22/22**, and ASan/UBSan CTest **22/22**. The Android NDK compiled the original entity-frame functions as ELF64/AArch64, and the combined relocatable object defined both `G_RunFrameForEntity` and `G_RunFrameForEntityInternal` without either remaining undefined. Evidence marker: `IW3_ORIGINAL_G_RUNFRAME_FOR_ENTITY_AARCH64_FRAME_EDGE_RESOLVED_GREEN`.
- Native artifact [12845787812](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784326/artifacts/12845787812): compiled objects and reports only, **not an APK**.
- JNI diagnostic package [40756784264](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784264): **PASS**; artifact [12847165670](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784264/artifacts/12847165670) is diagnostic only.
- Android emulator probe [40756784297](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784297): **PASS** for original ZIP/IWD fixture operations, JNI execution, touch-to-`usercmd_s`, and lifecycle. It ran on x86_64; its evidence still says `arm64_device_execution_proven=false` and `gameplay_proven=false`. Log artifact: [12846296439](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784297/artifacts/12846296439).
- Native Windows SP compile [40756784310](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784310): **PASS** after the public server-header correction described in Phase AB below.
- Killhouse SP smoke [40756784216](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784216): workflow **PASS**, original `killhouse` level loop and actor AI think observed. However, `actual_weapon_fire_callback=false`, `bullet_fire_dispatched=false`, `actor_damage_callback=false`, `actor_death_callback=false`, and `actual_graphics_verified=false`. Evidence [12847316067](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784216/artifacts/12847316067) does **not** prove weapon fire, damage, death, or playable Android gameplay.

**Scope boundary:** the entity-frame provider is now compile/link-audited, but not executed in the Android game runtime. The script/client/actor/path services remain unresolved; `FS_Startup()` has not run in the app; real IWD/FastFiles/map loading, original 3D rendering, live touch-driven frame execution, and physical ARM64 combat remain unproven. `IW3_PLAYABLE_APK=false`; keep PR #4 open and unmerged.


## Phase AB — expose canonical SP server APIs to client/cgame consumers (28 Oct 2026)

The offline SP build failed before this correction with C3861 for `SV_GetEntityState`, `SV_WaitServerSnapshot`, `SV_RecordClientCommand`, `SV_ExecuteClientCommand`, `SV_RecordClientThink`, `SV_ClientThink`, `SV_TrackPlayerDied`, and `SV_AddToPlayerScore`. Their canonical declarations already existed in `server/server.h`, but shared SP translation units did not include that private header.

The original SP public interface `server/sv_public.h` now forward-declares only the pointer types `gentity_s` and `usercmd_s`, and exposes the exact existing prototypes. `client/cl_input.cpp` and `cgame/cg_snapshot.cpp` now include that public interface; `game/g_combat.cpp` already did. The new regression requires every public prototype to match the canonical declaration in `server.h` exactly and requires the client/cgame includes. No service implementation or simulation stub was added.

Code commits:
- `4585c83df2f944a4f8b4d0e59c90a223577fd171` — public SP server declarations.
- `6d8df54075626c28da5c6d5a7bcc4bcfe2db11f0` — client input includes the public interface.
- `02ef0e9f9ff90650f83a75b34eebc5921bcfabfa` — cgame snapshot includes the public interface.
- `0997bf9e17a43893e41d060be5e071581f665cc9` — regression guard for the public API contract.

The latest native ARM64 run also executed the new header regression as part of its 206-test suite and passed both CTest configurations. The original Windows SP executable build then passed in [40756784310](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40756784310). The Killhouse smoke reached the real level loop and actor AI, but its evidence explicitly shows no weapon-fire callback, bullet dispatch, damage, pain, or death. That is the next gameplay test blocker—not a reason to infer combat success from an equipped weapon.

The next Android runtime blockers remain the original script services (`Scr_RunCurrentThreads`, `Scr_IncTime`), `ClientEndFrame`, actor corpse/event services, and `Path_RunBadPlaces`, followed by real filesystem startup, map loading, original renderer integration, and physical ARM64 gameplay evidence.


### Phase CF — user-owned COD4 data staging prerequisite (28 Oct 2026)

The Android diagnostic now offers a Storage Access Framework directory picker for a game root selected by the user. `GameDataImporter` enumerates only the selected root's `main/` and `zone/` trees and copies `.iwd` and `.ff` files into the app-private `filesDir`, preserving the game directory structure, normalizing directory components to lowercase for Android's case-sensitive filesystem, and preserving original asset filenames. It rejects unsafe path segments, verifies canonical destinations remain below the private root, writes through a temporary file, syncs it, and only then replaces a destination file. It does not bundle game assets, decrypt or redistribute them.

This removes one prerequisite for testing the original filesystem against user-owned files, but **does not mount the original search-path table, parse FastFiles, load a map, initialize a renderer, or execute gameplay**. The JNI bridge and APK remain diagnostic. The import is intentionally restricted to `main/` and `zone/`; a source root must contain at least one `.iwd` and one `.ff` file.

The code is covered by `tests/test_iw3_android_game_data_import.py`; Android Gradle CI must still compile the new Java helper and the emulator probe must be rerun after this UI change. Do not mark the APK playable based on an import-pass marker. The remaining critical work is integrating the authentic filesystem/dvar/bootstrap graph, loading licensed FastFiles and a real map, porting the original renderer, and wiring the Android input hook into the running client command loop on physical ARM64 hardware.


### Phase CH — validate staged IWD archives with original FS_LoadZipFile (28 Oct 2026)

Baseline inspected: `799952b6a8a5ebe1133f273235294721ef77b492`; PR #4 remained open/unmerged. The SAF importer staged user-owned `.iwd/.ff` files, but no post-import native check attempted to index the imported IWDs. Added a bounded scan of root-level `main/*.iwd` and `zone/*.iwd` that calls the original `FS_LoadZipFile`, validates the real index/hash/checksum fields and entry names, then closes/frees the original archive state and restores `fs_iwdFileCount/fs_checksumFeed`.

The activity now calls `nativeValidateImportedIwds(filesDir)` after import and reports validated archive/entry counts or the failing path. CI also executes the same path against a temporary synthetic IWD under an isolated app-private root; this proves the original indexer and cleanup path run, but it is explicitly a fixture, not proprietary game data.

**Still not gameplay:** this is IWD indexing, not full searchpath startup or FastFile/map loading. `FS_Startup/FS_InitFilesystem` are not invoked by the app, the original renderer and live command/frame loop are not integrated, and no physical ARM64 gameplay is proven. The APK remains diagnostic only. PR #4 must remain open and unmerged.


## Phase CI — original IWD entry-counter overflow guard

- Hardened the authentic `FS_LoadZipFile` body to reject negative `fs_iwdFileCount` and any archive whose entry count would overflow `INT_MAX`, before allocation.
- The extraction generator enforces the guard; the synthetic Android JNI IWD fixture tests rejection at `INT_MAX` and then confirms normal two-entry indexing still works.
- Validation: 217 Python tests, CTest Release 22/22, CTest ASan/UBSan 22/22; ARM64 audit and JNI build passed; emulator log includes `IW3_JNI_IMPORTED_IWD_INDEX_FIXTURE_PASS`.
- Evidence: [ARM64 audit](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665908), [JNI build](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665869), [emulator execution](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40783665919).
- Scope remains diagnostic: emulator x86_64; startup invocation, real game data/FastFiles/map, original rendering and real gameplay are not proven. `IW3_PLAYABLE_APK=false`.


### Phase CJ — malformed IWD fail-closed runtime regression (28 Oct 2026)

The native IWD-index fixture now also creates a ZIP32 entry whose length-coded filename contains an embedded NUL. It calls the authentic `FS_LoadZipFile` and requires rejection before index allocation/publication, with `fs_iwdFileCount` and `fs_checksumFeed` unchanged. The Android-only marker `IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS` is required by `run_emulator_probe.sh`; the emulator gate therefore verifies the negative path rather than only successful parsing or APK packaging. Regression: `tests/test_iw3_android_iwd_fail_closed.py`. Details: [Phase CJ](IW3_ANDROID_PHASE_CJ.md).

This is failure-path evidence for the original IWD indexer, **not** full filesystem startup. `FS_Startup/FS_InitFilesystem`, real FastFile/map loading, original rendering, live gameplay and physical ARM64 execution remain unproven. Keep PR #4 open/unmerged; the APK is diagnostic only.


#### Phase CJ validation result (code HEAD `866f378c93d756ea393963d3384d07f0a54f2d59`)

- Preflight [40787292165](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292165): PASS.
- Native ARM64 audit [40787292168](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292168): PASS; 220 Python tests, CTest Release 22/22, ASan/UBSan CTest 22/22; original IWD indexer compiles for AArch64.
- JNI package [40787292213](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292213): PASS; signed ARM64 diagnostic APK artifact [12859254508](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292213/artifacts/12859254508), **not a playable game**.
- Emulator [40787292208](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292208): PASS; log includes `IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS`, original IWD indexing/read and touch-to-`usercmd_s`; artifact [12859728152](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292208/artifacts/12859728152). Emulator is x86_64; `gameplay_proven=false` and `arm64_device_execution_proven=false`.
- Windows SP build [40787292140](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292140): PASS. Killhouse smoke [40787292232](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292232): smoke workflow PASS, but real fire dispatch, damage/death callbacks and graphics remain false.

Next runtime gate remains the authentic startup/command dependency graph: the combined audit still explicitly reports `IW3_FS_STARTUP_RUNTIME_INVOKED=false` and `IW3_PLAYABLE_APK=false`. Keep PR #4 open/unmerged.


### Phase CK — original filesystem logging query and Android writer-lock service (28 Oct 2026)

The latest ARM64 dependency report still showed the original FS_ReadFile chain with unresolved `Com_LogFileOpen()`, `Sys_LockWrite(FastCriticalSection*)`, and `Sys_UnlockWrite(FastCriticalSection*)`. This pass adds two real providers rather than masking those symbols:

- `prepare_real_engine_com_logfile_open.py` extracts the original `int logfile` state and verbatim `Com_LogFileOpen()` body from `src/qcommon/common.cpp`; the JNI app does not call it and the extraction report explicitly keeps `playable_apk=false`.
- `iw3_android_fs_lock_io.cpp` ports the original writer-gate algorithm from `src/universal/win_common.cpp` to Android/POSIX using sequentially-consistent compiler atomics over the upstream 8-byte `FastCriticalSection` layout and `sched_yield()` instead of the Windows-only `NET_Sleep(0)` dependency.
- `fs_readfile_services_native_test.cpp` executes the extracted original logfile query against the real extracted state and stresses the writer lock with a reader gate plus eight contending threads. It verifies that the writer waits while `readCount != 0`, excludes concurrent writers, and returns `writeCount` to zero.
- The ARM64 combined FS/IWD audit now fails if either service is missing or unresolved. The new services are included only in the dependency-audit archive, not linked into the JNI diagnostic APK.

**Validation (code commit `ae340e6b1cb997f4aa9acbe70403efe0dfd9816d`):**
- Preflight [40793488500](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488500): PASS.
- Native ARM64 audit [40793488539](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488539): PASS; 224 Python tests; CTest Release 23/23; CTest ASan/UBSan 23/23.
- The combined ARM64 FS/IWD link log defines `Com_LogFileOpen()`, `Sys_LockWrite(FastCriticalSection*)`, and `Sys_UnlockWrite(FastCriticalSection*)`, with no corresponding unresolved entries, and emits `IW3_ORIGINAL_FS_READFILE_LOGFILE_AND_WRITE_LOCK_AARCH64_LINK_GREEN`.
- Audit artifact [12862368849](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40793488539/artifacts/12862368849) contains the compiled native module and audit evidence; it is **not an APK**.

This closes only two service edges in the filesystem read graph. `FS_Startup/FS_InitFilesystem` still is not invoked by the Android app; authentic FastFile/map loading, the original renderer, touch-to-live-frame integration, and physical ARM64 gameplay remain unproven. Keep PR #4 open and unmerged.


### Phase CL — original client command builder touch-hook gate (29 Oct 2026)

The original `src/client/cl_input.cpp` already calls `z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles)` from `CL_CreateCmd`, after `CL_MouseMove` and before `CL_FinishMove`. The blocker is build integration: that client translation unit is not part of the Android shared-library target, so the existing touch hook is not running in a client frame.

This pass adds `tools/iw3_android/prepare_real_engine_cl_createcmd.py` and `tests/test_iw3_android_cl_createcmd.py`. The generator extracts the original function body verbatim, hashes it, checks that the touch hook occurs exactly once and remains between original mouse processing and command finalization, and emits a report that explicitly says the client runtime is not linked or invoked. The ARM64 workflow now cross-compiles the extracted function with original client headers and inspects its ELF64/AArch64 object and external touch/finish dependencies. The object is an audit artifact, not part of the JNI APK.

- Phase details: [IW3_ANDROID_PHASE_CL.md](IW3_ANDROID_PHASE_CL.md).
- Source preflight [40799653535](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653535): PASS.
- ARM64 native audit [40799653566](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653566): PASS; 227 Python tests, CTest Release 23/23, CTest ASan/UBSan 23/23.
- JNI Android diagnostic build [40799653491](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653491): PASS.
- ARM64 object/report artifact [12864594953](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653566/artifacts/12864594953) is not an APK; JNI artifact [12865720936](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40799653491/artifacts/12865720936) is diagnostic only.

**Boundary:** compiling the original command builder is not the same as executing it. Client state/input dependencies remain unresolved; no live frame, map, renderer, weapon/actor gameplay, physical ARM64 execution, or playable APK is proven. Keep PR #4 open and unmerged.
