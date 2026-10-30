# Phase DK — publish FastFile EOF on a final short POSIX read (NOT GAME)

Date: 2026-10-29 UTC

## Baseline inspected

The current Android branch of the original `DB_ReadData()` calls
`DBFastFilePosixReadAt()` for a 256 KiB chunk. That helper retries positive
short `pread()` results until it has filled the request or reached physical
EOF. The caller previously published `posixEof` only when a *later* read
returned zero bytes. This delayed EOF state after a final short chunk and
caused an unnecessary read attempt beyond the file boundary before the
inflater could diagnose a truncated stream.

## Change

In `third_party/KisakCOD/src/database/db_file_load.cpp`, the original
`DB_ReadData()` now sets:

```cpp
g_load.posixEof = bytesRead < 0x40000u;
```

after a successful POSIX read. This is valid because the shared helper loops
through short positive reads and returns a short count only after `pread()`
reports EOF. A full 256 KiB read does not set EOF; a final short read does.
The original Windows `ReadFileEx` branch remains unchanged.

The extracted-function harness in
`tools/iw3_android/prepare_real_engine_db_read_posix.py` now asserts that the
short final chunk publishes EOF immediately. The source regression also
requires this exact state transition.

## Validation scope

The existing `iw3-fastfile-posix-read-arm64.yml` workflow watches all changed
paths. It runs Python source regressions, compiles and executes a host harness
made from the exact original `DB_ReadData()` and `DB_WaitXFileStage()`
bodies under `__ANDROID__`, and compiles the POSIX harness for ELF64/AArch64.

This does **not** compile/link the full `db_file_load.cpp` translation unit
into an Android game runtime. It does not prove that a FastFile was
deserialized, a BSP/map loaded, a renderer frame presented, or gameplay
executed. Any JNI APK remains diagnostic and is not a playable game.

## Next gate

Compile the original database registry and loader translation units in the
actual Android runtime target, resolve their service dependencies without
no-op stubs, then demonstrate authentic FastFile deserialization and BSP/map
initialization before claiming rendering or gameplay progress. Keep PR #4 open
and unmerged.
