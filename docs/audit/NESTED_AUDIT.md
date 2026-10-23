# Nested archive and native engine audit

**Scope:** every nested COD4 `.iwd` in the 7.02 GB PC archive, every nested `.iwd` and `.zip` in the Android APK, and headers of packaged `.ff` and native binaries. Static only; no games were run.

## Original PC Call of Duty 4 package
- IWD containers inspected: **22**.
- Files *inside* IWD archives: **24,104**.
- Errors reading nested archives: **0**.
- Fastfiles identified (.ff): **73**. These are engine-specific binary packages, not Godot-compatible scenes.
### Most common internal file types
| Extension | Files |
| --- | --- |
| .wav | 16992 |
| .iwi | 6566 |
| [none] | 271 |
| .cfg | 129 |
| .mp3 | 119 |
| .accu | 15 |
| .gsc | 10 |
| .csv | 2 |

### Every IWD container
| Container | Files | Declared uncompressed bytes |
| --- | --- | --- |
| Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd | 11 | 456419 |
| Call of Duty 4 Modern Warfare/main/iw_00.iwd | 1053 | 295442529 |
| Call of Duty 4 Modern Warfare/main/iw_01.iwd | 1455 | 305301652 |
| Call of Duty 4 Modern Warfare/main/iw_02.iwd | 1295 | 307408431 |
| Call of Duty 4 Modern Warfare/main/iw_03.iwd | 669 | 300971342 |
| Call of Duty 4 Modern Warfare/main/iw_04.iwd | 764 | 259944222 |
| Call of Duty 4 Modern Warfare/main/iw_05.iwd | 715 | 240010020 |
| Call of Duty 4 Modern Warfare/main/iw_06.iwd | 413 | 250130228 |
| Call of Duty 4 Modern Warfare/main/iw_07.iwd | 32 | 181906653 |
| Call of Duty 4 Modern Warfare/main/iw_08.iwd | 63 | 189088286 |
| Call of Duty 4 Modern Warfare/main/iw_09.iwd | 443 | 210685000 |
| Call of Duty 4 Modern Warfare/main/iw_10.iwd | 222 | 189527410 |
| Call of Duty 4 Modern Warfare/main/iw_11.iwd | 433 | 164627287 |
| Call of Duty 4 Modern Warfare/main/iw_12.iwd | 33 | 13262228 |
| Call of Duty 4 Modern Warfare/main/iw_13.iwd | 265 | 46154812 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw00.iwd | 2895 | 173354956 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw01.iwd | 2958 | 172127066 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw02.iwd | 2761 | 175892894 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw03.iwd | 2931 | 176936816 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw04.iwd | 2213 | 178441316 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw05.iwd | 1448 | 177618734 |
| Call of Duty 4 Modern Warfare/main/localized_spanish_iw06.iwd | 1032 | 161699998 |

### Potentially interesting names (filenames only; do not establish functionality)
- `zombie`: 0 displayed examples.
- `nacht`: 0 displayed examples.
- `mp40`: 0 displayed examples.
- `weapon`: 50 displayed examples: `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_weapons.gsc`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hud_weaponmode_full.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hud_weaponmode_semi.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/icbm_decal_usweaponposter.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/icbm_decal_usweaponposter_bump.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/mtl_weapon_colt1911_col.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/mtl_weapon_m40a3_camo_col.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/mtl_weapon_m40a3_col.iwi`
- `animation`: 0 displayed examples.
- `perk`: 0 displayed examples.
- `scripts/`: 0 displayed examples.
- `sound/`: 50 displayed examples: `Call of Duty 4 Modern Warfare/main/iw_06.iwd :: sound/airplane/fuselage_stress.wav`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_ac130_int0v2_lr.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_ac130_int0v2_lsrs.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_aftermath0v2_lr.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_aftermath0v2_lsrs.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_airplane0v1_lr.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_airplane0v1_lsrs.mp3`, `Call of Duty 4 Modern Warfare/main/iw_07.iwd :: sound/ambient/amb_airplane5v1_lr.mp3`
- `images/`: 50 displayed examples: `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: images/logo_cod2.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/$black.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/$identitynormalmap.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/$white.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/1story_house_01.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/2story_house.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/2story_house_01.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/2story_motel.iwi`
- `xmodel`: 0 displayed examples.
- `materials/`: 0 displayed examples.
- `maps/`: 10 displayed examples: `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_class.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_globallogic.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_hardpoints.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_healthoverlay.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_menus.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_missions.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_modwarfare.gsc`, `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_rank.gsc`
- `menu`: 10 displayed examples: `Call of Duty 4 Modern Warfare/Mods/ModWarfare/z_modwarfare.iwd :: maps/mp/gametypes/_menus.gsc`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button_fade.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button_faderight.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button_faderight_selected.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button_fade_selected.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_button_selected.iwi`, `Call of Duty 4 Modern Warfare/main/iw_02.iwd :: images/menu_caret_closed.iwi`
- `ui/`: 0 displayed examples.
- `hud`: 50 displayed examples: `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/ac130_hud_target.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/ac130_hud_target_flash.iwi`, `Call of Duty 4 Modern Warfare/main/iw_00.iwd :: images/ac130_hud_target_offscreen.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hudcolorbar.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hudicon_american.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hudicon_neutral.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hudicon_opfor.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/hud_40mmgrenade.iwi`
- `player`: 12 displayed examples: `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/clipplayer.iwi`, `Call of Duty 4 Modern Warfare/main/iw_01.iwd :: images/compassping_player.iwi`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/assault_rifle.accu`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/default.accu`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/mg.accu`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/noweapon.accu`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/pistol.accu`, `Call of Duty 4 Modern Warfare/main/iw_11.iwd :: accuracy/aivsplayer/rpg.accu`

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
