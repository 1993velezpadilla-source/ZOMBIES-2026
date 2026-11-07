# IW3 Android Phase DF — FastFile header preflight

Date: 2026-10-29

## Baseline and blocker

PR #4 head before this pass was `f6ab8f7c9593d0d20c96765d08e00e7753be0360`. The SAF importer already required a `main/` IWD and a `zone/english/` FastFile, but it trusted the `.ff` suffix and copied arbitrary bytes. A corrupt, wrong-version, or unsupported authenticated FastFile could therefore be staged and fail much later during startup.

## Source-derived correction

Added the package-private Java helper `FastFileHeader` and call it from `GameDataImporter` before copying any `.ff` payload. The contract is copied from the vendored upstream `third_party/KisakCOD/src/database/db_file_load.cpp::DB_LoadXFileInternal`:

- 8-byte magic must be `IWffu100`.
- The little-endian 32-bit version must be `5`.
- `IWff0100` is recognized by the original loader but marked secure; this vendored loader explicitly rejects the authenticated variant as unsupported.
- A short header, wrong magic, or wrong version aborts the import and the existing temporary-file cleanup removes the partial destination.
- The 12 consumed header bytes are written back unchanged before streaming the remaining payload, preserving the original file bytes. The helper reads only the fixed header and handles short/zero-length reads defensively.

Added a host-JVM test compiled with Java 17 in the JNI workflow. It checks a valid header, exact prefix preservation, payload position, short/zero reads, truncated input, bad magic, secure magic, and wrong version. A Python regression guards the helper against drift from the actual upstream loader contract and verifies the importer validates before writing the prefix.

## Validation status

The new workflow run is triggered by the branch commits. Results must be read from GitHub Actions for the final head; do not infer success from the source edit or from prior green runs. Expected marker: `IW3_FASTFILE_HEADER_TESTS_PASS`.

## Scope boundary

This is a bounded import preflight only. It does **not** inflate or load a FastFile, call `DB_LoadXFile` / `DB_LoadXFileInternal`, register assets, load a BSP/map, initialize the original renderer, or run the original client/server frame. It uses no replacement engine and bundles no game assets. The APK remains diagnostic until the authentic startup/runtime path and physical ARM64 gameplay are demonstrated. Keep PR #4 open and unmerged.
