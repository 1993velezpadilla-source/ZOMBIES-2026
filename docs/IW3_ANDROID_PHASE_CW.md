# IW3 Android ARM64 phase CW — canonical filesystem state ownership

Date: 2026-10-29

## Concrete change

The previous successful source/link audit still had engine-owned filesystem globals unresolved in the combined original FS startup/IWD object. This pass moves the original zero-initialized filesystem globals from `com_files.cpp` into the existing shared-state translation unit `com_files_state.cpp`, which is already part of the original engine's common source list.

Moved state includes the original dvar pointers, server-IWD checksum/name tables, write-log event slots, fake checksum, and `lastValidBase`/`lastValidGame`. Declarations for the latter three state names were made explicit in `com_files.h`. No values are fabricated beyond the original zero-initialized storage; runtime registration and startup remain separate gates.

The Android full-filesystem compile target now compiles `com_files.cpp`, `com_files_state.cpp`, and `com_files_handle_table.cpp`. The ARM64 workflow compiles the same canonical state TU and includes that object in the combined relocatable FS/Dvar/IWD link. It fails if any of the listed original state symbols is absent from the defined-symbol table or remains undefined.

## Validation

CI is triggered by the source, CMake and regression-test changes. The intended success marker is `IW3_ORIGINAL_FS_STATE_OWNERSHIP_AARCH64_LINK_GREEN`; this proves only original state ownership and dependency resolution in a relocatable object, not an executable engine runtime.

## Remaining gates

`FS_Startup()/FS_InitFilesystem()` are not yet invoked by the Android Activity. The real user-owned FastFiles and map have not been loaded by the application, the original renderer is not active, and touch commands are not driving the original live frame loop. No physical ARM64 gameplay is claimed. Diagnostic JNI packages and relocatable audit objects are not playable APKs. PR #4 must remain open and unmerged.
