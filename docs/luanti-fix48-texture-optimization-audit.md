# FIX48 – Texture optimization audit (Android ARM64)

Source: FIX47 `fix47-zombies-registration-prefix-repair-arm64` (APK SHA-256 `8555b9caf078452d029a0d4bed28c74baeff81f090a5cecfc65182688fcf9d40`).

## Scope
- The shipping FIX47 game used XsRealism render textures largely at 192×192, while preserving 112 original high-resolution photographic texture sources in the `games/voxelibre/world_detail36/images` editor catalog.
- FIX48 recovered those 112 original photographic sources to produce native 256-pixel construction textures and selected 512-pixel priority building surfaces; other already-existing XsRealism textures remain as fallback.
- Rescaled 112 high-resolution editor-catalog images to 256 and updated the catalog index dimensions while retaining all original filenames and entries.
- All weapon and zombie meshes, weapon texture atlases, audio files, mod Lua, Gothic Cathedral map database, and world/editor functions unchanged.
- Original 1024 assets remain available in the preserved FIX47 release.

## Integrity
- Nested game archive paths: **9,663 before and 9,663 after**.
- Files changed: **229**, all limited to the expected texture/catalog/provenance files.
- Files untouched: **9,434**.
- APK entries: **419**, unchanged.
- Compact ZIP comment: `XZ-ASSETS-1:9663`.
- Android APK Signature Scheme v2: regenerated using the same private build key and signing certificate as FIX47; independently verified RSA signature and content-chunk digest.
- SHA-256 FIX48: `53c38034989ebf7fcea87cbe8bceed19ec0f72a0337f016a29bc5dc57be20552`.
- APK FIX48: **623,521,666 bytes**, compared with FIX47 **750,548,042 bytes**.
- Reduction: **127,026,376 bytes (16.92%)**.

## Licenses and boundaries
- XsRealism: MIT license and attribution retained inside the APK.
- **LynxArt is NOT included in FIX48.** No LynxArt material was downloaded or packaged; this is an XsRealism optimization test build, not the previously contemplated two-pack hybrid.
- No physical Android device run has yet been completed; installation and launch testing required before this can be called stable. Back up worlds before updating.
