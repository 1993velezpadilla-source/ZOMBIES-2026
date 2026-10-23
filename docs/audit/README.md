# ZOMBIES-2026 — static asset audit

**Method:** Read-only inspection of GitHub release binaries; no APK installation, execution, scene import, or complete decompression.
**Integrity:** Original archive byte sizes and SHA-256 match the import manifests (both PASS).

## C4-Mocs.zip
- Archive bytes: 7,021,386,357 bytes (6,696.12 MiB); stored in 4 GitHub Release parts.
- ZIP entries: 234; files: 215; dirs: 19.
- Declared total uncompressed size: 7,078,126,218 bytes (6,750.23 MiB).
- Declared total compressed entry bytes: 7,021,333,827 bytes (6,696.07 MiB).
- Encrypted examples: 0; path traversal examples: 0; duplicate entry examples: 0.
- ZIP CRC validation: **not performed for every file**; listing and central directory parsed.

### Largest extension groups
| Extension | Files |
| --- | --- |
| .ff | 73 |
| .bik | 53 |
| .iwd | 22 |
| .htm | 20 |
| .jpg | 9 |
| .txt | 5 |
| .exe | 5 |
| .flt | 4 |
| .cfg | 3 |
| .dat | 3 |
| [none] | 2 |
| .dll | 2 |
| .ico | 2 |
| .bmp | 2 |
| .log | 2 |
| .asi | 2 |
| .gif | 1 |
| .pdf | 1 |
| .bat | 1 |
| .csv | 1 |
| .svg | 1 |
| .inf | 1 |

### High-level asset categories (overlapping)
| Category | Files |
| --- | --- |
| cod_legacy | 98 |
| textures | 11 |
| code_and_config | 3 |

### Largest files inside C4
| Path | Uncompressed bytes | Compressed bytes |
| --- | --- | --- |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw01.iwd | 168326412 | 168076658 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw02.iwd | 168263689 | 168031667 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw03.iwd | 168255430 | 168008701 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw00.iwd | 168238863 | 167990142 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw04.iwd | 168143122 | 167939482 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw05.iwd | 168008742 | 167901490 |
| Call of Duty 4 Modern Warfare/main/iw_01.iwd | 167885112 | 167353834 |
| Call of Duty 4 Modern Warfare/main/iw_00.iwd | 167780172 | 167315803 |
| Call of Duty 4 Modern Warfare/main/iw_06.iwd | 167754503 | 167517960 |
| Call of Duty 4 Modern Warfare/main/iw_04.iwd | 167682009 | 167434125 |
| Call of Duty 4 Modern Warfare/main/iw_08.iwd | 167544651 | 167544651 |
| Call of Duty 4 Modern Warfare/main/iw_05.iwd | 167489996 | 167276841 |
| Call of Duty 4 Modern Warfare/main/iw_09.iwd | 167076481 | 167047365 |
| Call of Duty 4 Modern Warfare/main/iw_02.iwd | 166957774 | 166338586 |
| Call of Duty 4 Modern Warfare/main/iw_03.iwd | 166904484 | 166408422 |
| Call of Duty 4 Modern Warfare/main/iw_10.iwd | 165389824 | 165379994 |
| Call of Duty 4 Modern Warfare/main/iw_07.iwd | 162987361 | 162987361 |
| Call of Duty 4 Modern Warfare/main/video/attract.bik | 155322180 | 152303409 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw06.iwd | 151520102 | 151451606 |
| Call of Duty 4 Modern Warfare/main/iw_11.iwd | 151420446 | 151344135 |

### Top-level directories
| Directory | Files | Declared uncompressed bytes |
| --- | --- | --- |
| Call of Duty 4 Modern Warfare | 215 | 7078126218 |


## COD4.apk
- APK bytes: 51,760,726 bytes (49.36 MiB).
- ZIP entries: 45; files: 45.
- Declared total uncompressed size: 56,774,836 bytes (54.14 MiB).
- APK is a ZIP container; this alone does NOT prove authenticity, safe installation, proper licensing, or full game source.
### Android package metadata
| Field | Value |
| --- | --- |
| package | com.cod4.firstmission |
| app_name | COD4 |
| version_name | 0.5.9-r6-integrated-alpha |
| version_code | 26 |
| min_sdk | 24 |
| target_sdk | 36 |
| main_activity | com.cod4.firstmission.MainActivity |
| signature | {'v1': 'True', 'v2': 'True', 'v3': 'False'} |

### Requested Android permissions
- `android.permission.ACCESS_NETWORK_STATE`
- `android.permission.INTERNET`
### APK extension groups
| Extension | Files |
| --- | --- |
| [none] | 11 |
| .so | 10 |
| .zip | 5 |
| .txt | 3 |
| .json | 3 |
| .ff | 3 |
| .xml | 2 |
| .arsc | 1 |
| .dex | 1 |
| .gz | 1 |
| .md | 1 |
| .iwd | 1 |
| .sf | 1 |
| .rsa | 1 |
| .mf | 1 |

### APK engine signatures (heuristics only)
| Engine | Signature detected |
| --- | --- |
| unity | False |
| unreal | False |
| godot | False |
| cocos | False |

### APK largest entries
| Path | Uncompressed bytes |
| --- | --- |
| lib/arm64-v8a/libcod4mp.so | 10982264 |
| lib/arm64-v8a/libcod4first.so | 10927256 |
| assets/angle/libGLESv2_angle.so | 6119784 |
| assets/drivers/packages/PanVK-Kbase-Android-g615-v11-csf-v0.1.0-rc3-5a07217f.adpkg.zip | 5851150 |
| assets/drivers/packages/PanVK-Kbase-Android-g615-v11-csf-v0.1.0-beta.18-rc1-5a07217f.adpkg.zip | 5720955 |
| assets/drivers/packages/radv-xclipse-26.3.0-devel-313870e.zip | 4380303 |
| assets/drivers/packages/mesa-turnip-android-26.2.4.zip | 3857923 |
| assets/drivers/packages/mali-panvk-26.3.0-devel-r4.zip | 3423629 |
| lib/arm64-v8a/libc4vk.so | 951544 |
| assets/cod4x/jcod4x_00.iwd | 860805 |
| assets/angle/libEGL_angle.so | 713088 |
| assets/licenses/ANGLE/Android16-NOTICE.xml.gz | 713013 |
| assets/cod4x/cod4x_patchv2.ff | 550611 |
| assets/cod4x/cod4x_ambfix.ff | 496286 |
| classes.dex | 435940 |
| lib/arm64-v8a/libc4icd_hal.so | 378112 |
| lib/arm64-v8a/libhook_impl.so | 278520 |
| assets/cod4x/cod4x_patch.ff | 26284 |
| assets/drivers/HAL-ADAPTER-NOTICE.txt | 11811 |
| assets/licenses/ANGLE/SPIRV-Cross-LICENSE | 11358 |


## Compatibility and next steps
- Unreal/Godot coordinate transforms cannot be validated from archive names alone. Verify source units, handedness, forward axis, pivot and transforms on individual asset specimens.
- Static APK metadata cannot prove that assets, map layouts, animations or control systems can be imported into Godot.
- Before reusing third-party game assets, confirm rights and license; this audit does not grant permission.
- Detailed file-by-file ZIP inventories: [C4](c4-mocs-file-inventory.json), [APK](cod4-apk-file-inventory.json).
- Complete JSON audit metadata: [audit-data.json](audit-data.json).
