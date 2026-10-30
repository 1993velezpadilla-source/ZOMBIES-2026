# IW3 Android phase DH — POSIX FastFile read seam

Date: 2026-10-29.

## Finding

The authentic DB_LoadXFileInternal() path still uses the Windows asynchronous
file API through DB_ReadData() (ReadFileEx, OVERLAPPED, SleepEx, and
GetFileSize). That makes the original loader's input path unavailable to an
Android file descriptor even though the FastFile header parser itself is now
alignment-safe.

## Change

Added db_fastfile_posix_io.h, a POSIX positioned-read helper intended for the
Android branch of the original DB_ReadData() path. It uses pread() rather than
changing a shared file cursor, retries EINTR, accumulates short positive reads,
reports the exact final short chunk, distinguishes EOF from I/O failure, and
rejects invalid descriptors and offsets that cannot fit off_t.

The original db_file_load.cpp is intended to use an Android-only read path and
Android state for byte counts, error numbers, EOF and file offset. The Windows
branch retains ReadFileEx and its original overlapped semantics. The Android
stream path must add the exact byte count to zlib's avail_in, rather than
assuming every read supplied 256 KiB, and treat unexpected compressed-stream
EOF as a loader error. The original FastFile header parser, inflate calls, zone
allocator, stream initialization and XAsset deserialization must remain in
place.

The Android branch expects DB_LoadXFile()'s opaque f argument to be encoded
with DBFastFilePosixOpaqueFromFd(fd); the caller that opens the FastFile must
still be connected to this contract. This pass does not yet integrate that
caller into the full Android runtime.

## Verification

The dedicated workflow runs a host executable against a real temporary file
and cross-compiles the same test translation unit for ELF64/AArch64. The tests
cover full 256-KiB reads, final short reads, EOF, invalid descriptors, offset
overflow, zero-capacity reads and opaque descriptor encoding.

This is a portability slice, not proof that db_file_load.cpp as a whole builds
or runs on Android. The translation unit still depends on Windows declarations
and Direct3D finalization (DB_FinishGeometryBlocks, delayed image loading), and
the engine has not yet wired an Android file opener to DB_LoadXFile(). No
FastFile/map/gameplay success is claimed. Keep PR #4 open and unmerged.
