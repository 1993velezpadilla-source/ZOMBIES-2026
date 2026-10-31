# IW3 Android ARM64 — phase DE: imported game-data preflight

Date: 2026-10-29

## Baseline and next data-loading boundary

The current JNI Activity can import user-owned COD4 .iwd and .ff files into the app-private filesDir. Native diagnostics validate original IWD indexing and a read through the original filesystem functions, but FastFile parsing, BSP/map loading, renderer startup, and gameplay are not integrated. See the current status in the PR #4 conversation.

## This pass

Hardened GameDataImporter before using imported files as inputs to a future real FastFile/map loader:

- Requires at least one IWD under main/ and at least one FastFile under zone/english/, in addition to the existing main/ and zone/ root check.
- Enforces a 2 GiB per-file limit and a 12 GiB aggregate copy limit while streaming. Checks happen before each write, and an over-limit current file is discarded with the existing temporary-file cleanup path.
- Preserves the existing per-file temp-file, fsync, and same-filesystem rename behavior.
- Exposes the main IWD and English-zone FastFile counts in the Activity report so logs distinguish the expected zone layout from an arbitrary .ff elsewhere.

No assets are bundled, decrypted, modified, or redistributed. This is a data-import preflight, not a FastFile loader and not gameplay. Earlier successfully imported files may remain if a later file exceeds a limit; rerunning the import can replace them atomically one file at a time.

## Regression coverage

tests/test_iw3_android_game_data_import.py now guards the expected directory layout, the byte limits, and that both size checks precede output.write. The existing JNI integration workflow runs all test_iw3_android_*.py tests and builds the Android diagnostic APK. Its APK remains diagnostic-only.

## Remaining gates

- Integrate the authentic FastFile loader with the original filesystem and data root.
- Load a real single-player map and its collision data.
- Connect the original renderer and client/server bootstrap.
- Route touch events into the active CL_CreateCmd and simulation path.
- Demonstrate movement, weapon fire, impacts/damage, and actors on a physical ARM64 device.

Keep PR #4 open and unmerged until these gates are proven. Expected status remains IW3_REAL_MAP_LOADED=false, IW3_GAMEPLAY_PROVEN=false, and IW3_PLAYABLE_APK=false.
