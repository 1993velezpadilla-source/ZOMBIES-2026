# IW3 Android phase DG — alignment-safe original FastFile header parsing

Date: 2026-10-29. This pass targets a real portability defect in the vendored
KisakCOD source, not the JNI diagnostic app.

## Finding

DB_LoadXFileInternal() read the 8-byte FastFile magic and 32-bit version from
the zlib input buffer using pointer-cast loads such as
*(uint32_t *)g_load.stream.next_in. The buffer alignment is not part of the
parser contract, and the casts violate strict-aliasing rules. An ARM64 build
can tolerate many unaligned accesses, but that is not a safe C++ contract and
makes sanitizer/optimization behavior dependent on implementation details.

## Change

The original loader now calls db_fastfile_header.h, a small portable parser
used by DB_LoadXFileInternal() itself. It copies the magic with memcpy, decodes
the version byte-by-byte as little-endian, and reports the exact consumed-byte
boundary for valid, invalid, and truncated headers. The caller retains the
original error policy and messages: magic must be IWff0100 or IWffu100, version
must be 5, and the secure variant continues into the original
"authenticated file not supported" path. The Java import preflight remains
only an import guard; it is not a loader.

## Evidence gates added

- Host CTest runs an executable probe with deliberately unaligned input and
  checks both magic variants, little-endian versions 4/5/6, truncated input,
  invalid magic, and null arguments.
- Android CI cross-compiles that same probe to an ELF64/AArch64 object and
  checks its architecture.
- Python regression checks that DB_LoadXFileInternal() calls the portable
  helper and that the unsafe 32-bit pointer-cast reads are gone.
- No FastFile is mounted or deserialized by this helper. The generated ARM64
  object is a compile probe, not a gameplay module.

## Remaining blocker

The loader body is still coupled to Windows asynchronous file I/O
(ReadFileEx, OVERLAPPED, HANDLE), Windows compression/authentication services,
and Direct3D image/buffer finalization. The helper does not make
DB_LoadXFileInternal() Android-runnable. The next runtime milestone remains a
real Android platform I/O/inflate path integrated with the engine's zone-memory
and asset-registration lifecycle, then loading a licensed map and rendering
it. No playable APK is claimed; PR #4 remains open and unmerged.
