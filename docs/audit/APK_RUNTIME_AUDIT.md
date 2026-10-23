# COD4.apk — runtime path and feature reference audit

Read-only inspection of printable strings in `classes.dex` and native Android `.so` files. **A string match is evidence of a literal being present in compiled binary data, not proof the feature works.**

| Binary | Bytes | Game content path refs | Storage refs | Graphics refs | Controls refs | Modes refs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `classes.dex` | 435,940 | 45 | 9 | 220 | 54 | 44 |
| `lib/arm64-v8a/libcod4first.so` | 10,927,256 | 23 | 23 | 220 | 220 | 220 |
| `lib/arm64-v8a/libcod4mp.so` | 10,982,264 | 73 | 11 | 220 | 220 | 220 |
| `lib/arm64-v8a/libc4vk.so` | 951,544 | 0 | 0 | 168 | 3 | 3 |
| `lib/arm64-v8a/libc4icd_hal.so` | 378,112 | 0 | 0 | 97 | 1 | 3 |
| `lib/arm64-v8a/libhook_impl.so` | 278,520 | 0 | 0 | 98 | 1 | 0 |
| `lib/arm64-v8a/libmain_hook.so` | 4,216 | 0 | 0 | 0 | 0 | 0 |
| `lib/arm64-v8a/libfile_redirect_hook.so` | 4,000 | 0 | 0 | 0 | 0 | 0 |
| `lib/arm64-v8a/libgsl_alloc_hook.so` | 4,312 | 0 | 0 | 0 | 0 | 0 |

## External storage and game data strings (candidate references, not verified runtime paths)
### `classes.dex`
- `DRIVER_IMPORT_ZIP_UNSAFE`
- `getExternalFilesDir`
- `getFilesDir`
- `getSafeInsetBottom`
- `getSafeInsetLeft`
- `getSafeInsetRight`
- `getSafeInsetTop`
- `Safehouse`
- `Unsafe driver ZIP`
- `!Installing official COD4x assets`
- `#COD4x asset exceeds the size limit.`
- `%Cannot back up previous COD4x asset:`
- `&Lcom/cod4/firstmission/Cod4xResources;`
- `(.ff. Import the complete campaign files.`
- `)Installing missing official COD4x assets`
- `+Missing campaign assets common.ff or ui.ff.`
- `-Lcom/cod4/firstmission/Cod4xResources$Source;`
- `.cod4x-bundle-`
- `.cod4x-staging-`
- `5Missing code_post_gfx.ff in the zone language folder.`
- `9lambda$installCod4x$24$com-cod4-firstmission-MainActivity`
- `9lambda$installCod4x$25$com-cod4-firstmission-MainActivity`
- `9lambda$installCod4x$26$com-cod4-firstmission-MainActivity`
- `9lambda$installCod4x$27$com-cod4-firstmission-MainActivity`
- `@COD4x assets installed. The server must still allow this client.`
- `@Lcom/cod4/firstmission/Cod4xResources$$ExternalSyntheticLambda0;`
- `CCOD4x assets updated. Previous files are kept in the backup folder.`
- `COD4x asset verification failed.`
- `COD4x installation failed:`
- `cod4x-backup-`
- `COD4x-preflight`
- `COD4x-resources`
- `COD4x.`
- `COD4x:`
- `cod4x_ambfix.ff`
- `cod4x_patch.ff`
- `cod4x_patchv2.ff`
- `cod4xReady`
- `Cod4xResources.java`
- `code_post_gfx.ff`
- `code_post_gfx.ff.`
- `code_post_gfx_mp.ff`
- `common.ff`
- `common_mp.ff`
- `Install official COD4x assets`
- `installCod4x`
- `jcod4x_00.iwd`
- `localized_chinese_iw15`
- `main/iw_00.iwd`
- `main/localized_chinese_iw15.iwd`
- `RA different COD4x version is already installed. Back up and move this file first:`
- `ui_mp.ff`
- `Use your own Steam 2007 game files. The localized_chinese_iw15 fonts and Chinese encoding are detected automatically. Keep the full main and zone folders when importing the Chinese patch.`
- `zone/english`
### `lib/arm64-v8a/libcod4first.so`
- `!p->avctx->hwaccel || p->hwaccel_threadsafe`
- `ai_debugGrenadeFailSafe`
- `allow potentially unsafe hwaccel frame output that might require special care to process successfully`
- `center_safearea`
- `clearfixednodesafevolume`
- `Display grenade fail safe debug information`
- `Draw the goal volume and fixed node safe volume for an AI`
- `Enable error resilience on damaged frames (unsafe)`
- `Error resilience with slice threads is enabled. It is unsafe and unsupported and may crash. Use it at your own risk`
- `exec safemode.cfg`
- `fixednodesaferadius`
- `getfixednodesafevolume`
- `GLES_BINDS skipped_buffers=%llu skipped_constants=%llu safe_uploads=%d`
- `ignoreforfixednodesafecheck`
- `MagicGrenade: None of the methods worked (probably distance or blocked)...need a good failsafe or remove this print?`
- `node_not_safe`
- `p_dst->hwaccel_threadsafe || (!dst->hwaccel && !dst->internal->hwaccel_priv_data)`
- `safeAreaRatioHorz not in [0, 1]`
- `safeAreaRatioVert not in [0, 1]`
- `safeNode`
- `safetochangescript`
- `setfixednodesafevolume`
- `unsafe_output`
- `" +set fs_homepath "`
- `%s\%s\%s.ff`
- `%s\zone\%s\%s.ff`
- `+set fs_basepath "`
- `+set fs_game "`
- `/main/localized_chinese_iw15.iwd`
- `cinematic IW_logo`
- `Corrupted iw0.iwd: %u`
- `fs_basepath`
- `fs_homepath`
- `FS_SV_FOpenFileRead (fs_basepath): %s`
- `FS_SV_FOpenFileRead (fs_homepath): %s`
- `Loading mp_patch.ff from disc, not from the update drive`
- `localized_`
- `main/iw_00.iwd`
- `Main/Snd:6/Volume Falloff Curves/%s:%d`
- `Select Main/Left channel`
- `update:\mp_patch.ff`
- `WARNING: Localized assets iwd file %s/%s/%s has invalid name (bad language name specified). Proper naming convention is: localized_[language]_iwd#.iwd`
- `WARNING: Localized assets iwd file %s/%s/%s has invalid name (no language specified). Proper naming convention is: localized_[language]_iwd#.iwd`
- `zone/%s/%s.ff`
- `zone/italian`
- `zone/italian/code_post_gfx.ff`
### `lib/arm64-v8a/libcod4mp.so`
- `!p->avctx->hwaccel || p->hwaccel_threadsafe`
- `allow potentially unsafe hwaccel frame output that might require special care to process successfully`
- `center_safearea`
- `Enable error resilience on damaged frames (unsafe)`
- `Error resilience with slice threads is enabled. It is unsafe and unsupported and may crash. Use it at your own risk`
- `exec safemode_mp.cfg`
- `GLES_BINDS skipped_buffers=%llu skipped_constants=%llu safe_uploads=%d`
- `p_dst->hwaccel_threadsafe || (!dst->hwaccel && !dst->internal->hwaccel_priv_data)`
- `safeAreaRatioHorz not in [0, 1]`
- `safeAreaRatioVert not in [0, 1]`
- `unsafe_output`
- `" +set fs_homepath "`
- `%s/iw_%02d`
- `%s/localized_`
- `%s\%s\%s.ff`
- `%s\zone\%s\%s.ff`
- `+set fs_basepath "`
- `+set fs_game "`
- `/main/localized_chinese_iw15.iwd`
- `\fs_game\\`
- `cinematic IW_logo`
- `cod4master.cod4x.ovh`
- `CoD4x configstring out of range`
- `CoD4x download checksum mismatch`
- `CoD4x extended gamestate overflow`
- `CoD4x file verification command is too long`
- `CoD4x file verification: %u archives, server id %d`
- `CoD4x master request failed; retaining cached servers`
- `CoD4x master: %d compatible candidates of %d listed (%d rejected or unverified)`
- `CoD4x redirect checksum failed for %s; requesting server download`
- `CoD4x redirect without checksum metadata`
- `CoD4x reliable channel ready`
- `CoD4x reliable gamestate: %d bytes`
- `CoD4x reliable send overflow`
- `CoD4x reliable service %d, %d bytes`
- `CoD4x statistics encryption failed`
- `CoD4x verification %s: bytes %zu/%d CRC32 %08x/%08x read error %d`
- `CoD4x verification could not open %s`
- `CoD4x verification missing metadata for %s`
- `CoD4x: authentication rejection saved for the server browser filter`
- `CoD4x: server asked for Steam authentication; reported that Steam is unavailable on this platform`
- `CoD4x: short optional reliable service %d ignored`
- `CoD4x: unsupported reliable service %d`
- `cod4x_ambfix`
- `cod4x_patchv2`
- `cod4x_servers.txt`
- `Corrupted iw0.iwd: %u`
- `Could not save CoD4x download (check free space)`
- `Downloaded CoD4x file failed checksum verification`
- `fs_basepath`
- `fs_gameDirVar`
- `fs_homepath`
- `FS_SV_FOpenFileRead (fs_basepath): %s`
- `FS_SV_FOpenFileRead (fs_homepath): %s`
- `Implemented CoD4x compatibility version`
- `Incomplete CoD4x download`
- `Info string length exceeded key: fs_game Info string: %s`
- `Invalid CoD4x client data`
- `Invalid CoD4x config sequence`
- `Invalid CoD4x download checksum block`

## Limitations
- Native dynamic behavior, function call graphs and actual file lookups are NOT tested.
- Strings may include errors, log labels, debug-only code, and unused legacy data.
- Download and archive validation do not establish APK safety or rights to redistribute proprietary game assets.
- Do not treat a Windows install archive as a ready-made Godot project or assume asset path compatibility.
- Full machine-readable match list: [apk-runtime-strings.json](apk-runtime-strings.json).
