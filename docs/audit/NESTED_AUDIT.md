# Nested archive and native engine audit

**Scope:** every nested COD4 `.iwd` in the 7.02 GB PC archive, every nested `.iwd` and `.zip` in the Android APK, and headers of packaged `.ff` and native binaries. Static only; no games were run.

## Original PC Call of Duty 4 package
- IWD containers inspected: **0**.
- Files *inside* IWD archives: **0**.
- Errors reading nested archives: **104**.
- Fastfiles identified (.ff): **0**. These are engine-specific binary packages, not Godot-compatible scenes.
### Most common internal file types
| Extension | Files |
| --- | --- |

### Every IWD container
| Container | Files | Declared uncompressed bytes |
| --- | --- | --- |

### Potentially interesting names (filenames only; do not establish functionality)
- `zombie`: 0 displayed examples.
- `nacht`: 0 displayed examples.
- `mp40`: 0 displayed examples.
- `weapon`: 0 displayed examples.
- `animation`: 0 displayed examples.
- `perk`: 0 displayed examples.
- `scripts/`: 0 displayed examples.
- `sound/`: 0 displayed examples.
- `images/`: 0 displayed examples.
- `xmodel`: 0 displayed examples.
- `materials/`: 0 displayed examples.
- `maps/`: 0 displayed examples.
- `menu`: 0 displayed examples.
- `ui/`: 0 displayed examples.
- `hud`: 0 displayed examples.
- `player`: 0 displayed examples.

## Android package internal archives
| Package | Files | Declared uncompressed bytes |
| --- | --- | --- |
| assets/drivers/packages/PanVK-Kbase-Android-g615-v11-csf-v0.1.0-beta.18-rc1-5a07217f.adpkg.zip | 8 | 23457111 |
| assets/drivers/packages/PanVK-Kbase-Android-g615-v11-csf-v0.1.0-rc3-5a07217f.adpkg.zip | 8 | 23885631 |
| assets/drivers/packages/mali-panvk-26.3.0-devel-r4.zip | 3 | 16222557 |
| assets/drivers/packages/mesa-turnip-android-26.2.4.zip | 1 | 19473960 |
| assets/drivers/packages/radv-xclipse-26.3.0-devel-313870e.zip | 3 | 18904275 |
| assets/cod4x/jcod4x_00.iwd | 55 | 1245234 |

### Native shared libraries
| Path | Bytes | CPU | ELF header |
| --- | --- | --- | --- |
| lib/arm64-v8a/libcod4first.so | 10927256 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libcod4mp.so | 10982264 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libc4vk.so | 951544 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libc4icd_hal.so | 378112 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libhook_impl.so | 278520 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libmain_hook.so | 4216 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libfile_redirect_hook.so | 4000 | aarch64 | 7f454c46 |
| lib/arm64-v8a/libgsl_alloc_hook.so | 4312 | aarch64 | 7f454c46 |
| assets/angle/libEGL_angle.so | 713088 | aarch64 | 7f454c46 |
| assets/angle/libGLESv2_angle.so | 6119784 | aarch64 | 7f454c46 |

### Included metadata documents
| Document | Bytes | JSON keys |
| --- | --- | --- |
| assets/drivers/bootstrap-v1.json | 652 | autoActivate, autoDownload, families, panvk, schema, signedCatalog, source |
| assets/drivers/catalog-v2.json | 4680 | autoActivate, autoDownload, builtAt, candidateFamilies, entries, schema, signaturePolicy, source |
| assets/cod4x/LICENSE.md | 884 |  |
| assets/licenses/ANGLE/prebuilt-source.json | 804 | archive_sha1, binaries, files_origin, package, reference_source_tree, revision, source_component, source_url |


## Compatibility assessment
- The 7GB archive contains the packaged **PC Call of Duty 4: Modern Warfare game**, not editable Unreal or Godot project source.
- The Android APK contains native ARM64 game libraries, graphics/driver packages and a small set of COD4X support files. It does **not** include the 7 GB PC asset archive internally.
- `.iwd` files are themselves ZIP-like asset containers; the nested inventories reveal internal assets, but their proprietary formats may require a lawful conversion step.
- `.ff` game fastfiles are compiled/packed engine assets; listing their names is not equivalent to extracting editable models, animations or maps.
- No automatic coordinate conversion tool can turn those engine-specific packages directly into Godot scenes without intermediate decoders and reauthoring.
- Do not redistribute proprietary assets without permission. This repository is public.

## Machine-readable records
- [C4 IWD file-by-file inventory](c4-iwd-file-inventory.json).
- [Nested audit JSON, including APK driver packages](nested-audit-data.json).
### Container errors
- Call of Duty 4 Modern Warfare/Mods/ModWarfare/7za.exe: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/Mods/ModWarfare/mod.ff: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/_Redist/DirectX/dxwebsetup.exe: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/binkw32.dll: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/iw3mp.exe: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/iw3sp.exe: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_00.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_01.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_02.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_03.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_04.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_05.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_06.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_07.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_08.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_09.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_10.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_11.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
- Call of Duty 4 Modern Warfare/main/iw_12.iwd: AttributeError: 'SplitReader' object has no attribute 'seekable'
