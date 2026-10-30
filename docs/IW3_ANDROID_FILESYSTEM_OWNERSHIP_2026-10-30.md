# Original filesystem ownership and command dispatch

This pass continues PR #4 from `85abf96f48ab6b331816bb9fa56dc47be2d07920`.
Android gameplay, complete bootstrap, real map loading and rendering remain
unverified. The diagnostic APK is not a playable game.

## Filesystem defect and change

The Android `Sys_ListFiles` adapter allocated a flat `Z_Malloc` buffer and
provided a competing `FS_FreeFileList` that called `Z_Free`. The full original
filesystem instead expects the HunkUser owner immediately before the returned
pointer array and destroys that reservation. Mixing the adapter with the full
filesystem therefore introduced both duplicate symbols and invalid ownership.

`Sys_ListFiles` now allocates with the original HunkUser allocator, stores its
owner at `list[-1]`, includes a NULL terminator, and uses native pointer widths.
The original `FS_FreeFileList` releases both Android enumeration results and
original engine lists. Extension/filter/directory behavior, root confinement,
symlink rejection and the IWD over-limit warning signal are preserved.

The seven HunkUser functions moved verbatim into `com_memory_hunk_user.cpp`;
the destructor moved verbatim into `com_files_list.cpp`. All eight bodies were
compared with the parent commit and are unchanged. Both Windows source lists
and Android targets use these same engine modules. The diagnostic library now
links the real allocator instead of its incompatible list-free substitute.

The full-filesystem ARM64 link audit uses a platform-only archive rather than
the slice archive containing duplicate filesystem bodies. Its final symbol
checks still require the original free function and single state owners.
The startup tokenizer audit now runs after its symbol reports are generated.

## Command defect and change

`Cmd_ExecuteSingleCommand` tested `itr->next` rather than `itr` in its registry
loop. That skipped a sole or last registered command and dereferenced NULL
when the registry was empty. The loop now visits every existing node safely.

Five executable host regressions compile the original dispatcher, registration,
argument accessors, tokenizer and string comparisons. Instrumented external
services exist only in the temporary unit-test executable; they do not enter
JNI or establish a running engine. Four tests failed before the one-line fix;
all five passed afterward, including nested-command argument restoration.

## Validation before commit

- 423 Python tests passed, including the five executable command regressions.
- The complete configured host build passed 26/26 CTest tests.
- The new filesystem test executes real directory reads and original
  allocation/free functions, repeated frees, extension and wildcard matching,
  subdirectories, symlink/traversal rejection, empty results and 1,026 IWD names.
- Both modified workflow files parse as YAML; all 31 embedded shell scripts
  pass `bash -n`.
- ASAN/UBSAN passed for all five command cases and both native HunkUser/list
  tests. LeakSanitizer cannot inspect `/proc`
  in this local executor, so local sanitizers use `detect_leaks=0`; GitHub CI
  retains `detect_leaks=1` for the native and command tests.

GitHub check runs on the resulting commit are the authority for Android ARM64,
emulator and Windows validation. No merge or playable-APK completion is claimed.
