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

**Validation update (26 Oct 2026):** native ARM64 run [40401446714](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446714) passed the host test/sanitizer stages and the AArch64 archive audit. The archive defines both `FS_ListFilteredFiles()` and `FS_ListFilteredFilesInLocation()`; the original Hunk, sanitizer, path and OS-listing services remain unresolved by design. The run uploaded audit evidence [12688218194](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446714/artifacts/12688218194), explicitly not an APK. JNI integration [40401446845](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446845) and x86_64 diagnostic emulator run [40401446788](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40401446788) were still running at documentation time. This still does not execute the real list function against a mounted game filesystem or integrate full `FS_Startup()`, FastFile/map loading, renderer, touch-driven gameplay or physical ARM64 execution. No playable APK is claimed; PR #4 remains open and unmerged.
