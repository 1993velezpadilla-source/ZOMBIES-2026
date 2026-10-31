# IW3 Android Phase FF — pure-server IWD name bounds (2026-10-30)

## Baseline / scope

- PR #4, `feature/iw3-native-android-arm64-20261025`; baseline head `73e93cc6cf790f103748140250d800db001c88ac`.
- Before this pass, the previous ARM64 source/host CI at [41151016730](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41151016730) completed **SUCCESS**. That was not Android gameplay.
- Target is the authentic `third_party/KisakCOD/src/qcommon/files.cpp`, not a replacement engine. This pass does **not** link Android `Com_Init` or run `FS_Startup`.

## Blocking defect and implementation

Two pure-server IWD-name classification routines copied externally supplied paths into 68-byte stack arrays without checking the length:

1. `FS_serverPak(const char*)` copied the entire server-supplied name byte by byte into `szFile[68]` before searching for `_svr_`.
2. `FS_iwIwd(char*, char*)` copied the entire name into `szFile[68]`, wrote a localized-prefix terminator at an unchecked offset, and then copied the localized suffix again into the same array.

On a 64-bit Android process these unchecked writes are memory-corruption risks during pure-server IWD comparisons and can interfere with future original filesystem integration. The fix rejects null and overlong names before copying, validates the localized prefix offset, and preserves original `main/iw_00` through `main/iw_24` and localized `_iw00` through `_iw24` classifications.

- Original-source fix: [e161907d](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/e161907d1160232b59b32fcb16942c5df1e066f1).
- Extracted-original host regression: [8b0599f2](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/8b0599f2af8b90747cd7becdc8b2f42dad281e51).
- Focused sanitizer workflow: [f528c394](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/f528c3948448ae20b6d4c75fc2480ca203b62852).

## Verified results

[Focused run 41154496206](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41154496206) completed **SUCCESS** at `f528c394`. Inspected job `124398188555`: `test_original_pure_iwd_name_bounds ... ok`, `Ran 1 test in 1.440s`, `OK`. The test compiles the **actual function bodies extracted from the original source** with host ASan/UBSan and checks normal server packs, case handling, standard/localized IWD names, 67-byte boundary, overlong inputs, and null inputs. Test-only `va`/comparison helpers are not linked into the Android application.

The existing IWD pointer-width host sanitizer [41154496185](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41154496185) and source preflight [41154496193](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41154496193) also completed **SUCCESS** on the same head. The full native ARM64 source workflow [41154496204](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41154496204) was pending at this inspection; do not count it as passing until finished.

## Remaining gameplay gates

`IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false`
`IW3_FS_STARTUP_RUNTIME_INVOKED=false`
`IW3_REAL_MAP_LOADED=false`
`IW3_RENDERER_FRAME_PROVEN=false`
`IW3_ORIGINAL_TOUCH_CLIENT_PROVEN=false`
`IW3_GAMEPLAY_PROVEN=false`
`IW3_PLAYABLE_APK=false`

The next **major** blocker is native ARM64 linkage and invocation of the original `Com_Init`, `Cmd_Init`, `Dvar_Init`, and `FS_Startup` in an actual Android process with legally supplied IWD content. The original renderer, real map, live touch consumption and actor/weapon gameplay must be observed in that same genuine engine runtime before any APK is called playable. Keep PR #4 open and do not merge to `main`.
