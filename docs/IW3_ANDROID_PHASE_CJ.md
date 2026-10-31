# Phase CJ — malformed IWD fail-closed regression

**Baseline inspected:** PR #4 head `7f85567bdb95d95d5f3a45b024985e5980b98593`, with the latest successful CI set attached to that head. The Android app remains a JNI diagnostic, not a playable game.

## Concrete change

Extended the native fixture that already calls the authentic KisakCOD `FS_LoadZipFile` body. In addition to the signed global-counter overflow case and a valid two-entry archive, it now writes a ZIP32 fixture whose central-directory filename contains an embedded NUL byte. The original loader must reject the archive during its sizing pass, before index allocation/publication, and leave `fs_iwdFileCount` and `fs_checksumFeed` unchanged.

On Android, a dedicated log marker `IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS` is emitted only when this negative-path check and the existing valid-index/cleanup checks all pass. The emulator script requires that marker, so a successful job cannot rely solely on APK compilation or the older generic fixture marker.

Files:
- `android/iw3-native/iw3_unzip_native_smoke.cpp`
- `tools/iw3_android/run_emulator_probe.sh`
- `tests/test_iw3_android_iwd_fail_closed.py`

Code commits:
- `5a3f36354b5e4b023af5b208143a139945434726` — malformed IWD fixture and Android marker.
- `39656e269bc5a8e924ee34cda8bef0c60a861ab9` — correct the C++ embedded-NUL fixture literal.
- `d99a63e1fec643d316e58445febbb628c86da7b8` — require the marker in emulator evidence.
- `36fa30a9790f8b1ed8b5454bee0cdd8d9ef3c3d9` — source and CI regression tests.

## Validation completed on code commit `866f378c93d756ea393963d3384d07f0a54f2d59`

- Preflight: [40787292165](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292165) — **PASS**.
- Native ARM64/source audit: [40787292168](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292168) — **PASS**; 220 Python tests, CTest Release 22/22, ASan/UBSan CTest 22/22, original FS_LoadZipFile compiled as AArch64, original startup dependency audit retained the explicit `IW3_FS_STARTUP_RUNTIME_INVOKED=false` marker.
- JNI package: [40787292213](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292213) — **PASS**; Android APK contains `lib/arm64-v8a/libiw3_sp_math.so`, ELF64/AArch64 and exported JNI symbols. Artifact [12859254508](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292213/artifacts/12859254508) is explicitly a diagnostic APK, not the game.
- Android emulator execution: [40787292208](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292208) — **PASS**; log contains `IW3_JNI_MALFORMED_IWD_REJECTED_AND_CLEANUP_PASS`, original ZIP/IWD index and read markers, touch-to-`usercmd_s`, sprint/slide and pause/resume. Artifact [12859728152](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292208/artifacts/12859728152) preserves the log/screenshots. Emulator ABI is **x86_64**, not physical ARM64.
- Original Windows SP build: [40787292140](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292140) — **PASS**.
- Killhouse SP smoke: [40787292232](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40787292232) — workflow **PASS**, but the report still says `actual_weapon_fire_callback=false`, `bullet_fire_dispatched=false`, `actor_damage_callback=false`, `actor_death_callback=false`, and `actual_graphics_verified=false`.

## Scope boundary / next blocker

This pass strengthens the real IWD indexer's failure-path evidence; it does **not** invoke `FS_Startup()` or `FS_InitFilesystem()` in the app. The full startup/command graph, authentic FastFile/map load, original renderer, live frame/input loop and physical ARM64 gameplay remain unproven. The JNI package remains diagnostic. Keep PR #4 open and unmerged; `IW3_PLAYABLE_APK=false`.
