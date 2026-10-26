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