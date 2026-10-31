# IW3 Android ARM64 phase CW — canonical filesystem state ownership

Date: 2026-10-29

## Concrete change

The previous successful source/link audit still had engine-owned filesystem globals unresolved in the combined original FS startup/IWD object. This pass moves the original zero-initialized filesystem globals from `com_files.cpp` into the existing shared-state translation unit `com_files_state.cpp`, which is already part of the original engine's common source list.

Moved state includes the original dvar pointers, server-IWD checksum/name tables, write-log event slots, fake checksum, and `lastValidBase`/`lastValidGame`. Declarations for the latter three state names were made explicit in `com_files.h`. No values are fabricated beyond the original zero-initialized storage; runtime registration and startup remain separate gates.

The Android full-filesystem compile target now compiles `com_files.cpp`, `com_files_state.cpp`, and `com_files_handle_table.cpp`. The ARM64 workflow compiles the canonical state TU as a standalone ELF evidence object, then checks the combined relocatable FS/Dvar/IWD graph. The first attempt showed that the canonical state owner was already present through the existing archive graph: explicitly adding the standalone object duplicated the same globals. The corrected link keeps the object for ELF evidence but relies on the one existing state owner in the combined graph. It fails if any listed original state symbol is absent from the defined-symbol table or remains undefined.

## Validation — source/test commit `63913450c91a41f59c2eace091950451c7253525`

- [Preflight run 40872435196](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40872435196): passed.
- [Original-source Android ARM64 audit run 40872435086](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40872435086): passed.
- Python regression suite: **260 tests passed**.
- CTest Release: **23/23 passed**.
- CTest ASan/UBSan: **23/23 passed**.
- ARM64 object checks: ELF64/AArch64 passed; the combined relocatable FS/Dvar/IWD link emitted `IW3_ORIGINAL_FS_STATE_OWNERSHIP_AARCH64_LINK_GREEN` and `IW3_ORIGINAL_FS_COMMAND_REGISTRATION_AARCH64_LINK_GREEN`.
- [JNI integration run 40872435233](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40872435233): passed and built the explicitly diagnostic APK. It is not the game.
- [Android emulator run 40872435237](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40872435237): still running at the last check; no result is claimed for it.

The earlier ARM64 attempt failed on duplicate symbols because the standalone state evidence object was also included through the existing archive graph. Commit `6391345` removes that second inclusion. The successful ARM64 run above validates the corrected link graph, not a full executable engine runtime.
  
## Remaining gates

`FS_Startup()/FS_InitFilesystem()` are not yet invoked by the Android Activity. The real user-owned FastFiles and map have not been loaded by the application, the original renderer is not active, and touch commands are not driving the original live frame loop. No physical ARM64 gameplay is claimed. Diagnostic JNI packages and relocatable audit objects are not playable APKs. PR #4 must remain open and unmerged.


## Follow-up from the first link attempt

The first host link after moving the globals exposed duplicate diagnostic definitions in `iw3_android_fs_read_io.cpp` (`fs_fakeChkSum`, `fs_serverIwds`, `fs_numServerIwds`, and several dvar pointers) and in the generated lookup slice (`fs_ignoreLocalized`). These were test-only copies, so keeping them would have split the engine state again.

The follow-up removes those definitions. A one-time diagnostic initializer now binds the canonical `com_files_state.cpp` globals to fixture-only dvar objects before the smoke tests. It does not invoke engine startup or initialize a real game. The new regression test guards against reintroducing the duplicate owners.

The first post-change CI run completed 259 Python tests and both native CTest configurations at 23/23, but the ARM64 relocatable link failed because the standalone state object was also already included by the archive graph. This pass removes the second inclusion and strengthens the duplicate-owner test with exact declaration checks. The rerun is pending; the failed link is not counted as an ARM64 pass.
