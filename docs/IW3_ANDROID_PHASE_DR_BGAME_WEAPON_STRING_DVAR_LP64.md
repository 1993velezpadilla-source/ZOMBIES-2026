# Android ARM64 pass DR — BGame weapon string-dvar pointer width

Date: 2026-10-30

## Starting point

The current branch already stages the original BGame melee dvar registration statements from `bg_misc.cpp` (pass DQ). That audit still left `Dvar_RegisterFloat` unresolved even though the complete original `universal/dvar.cpp` archive is built for Android ARM64.

A separate source scan of the authentic `bgame/bg_weapons.cpp` found two remaining 32-bit pointer reads:

- `BG_ShutdownWeaponDefFiles()`
- `BG_LoadWeaponDef()`

Both read the string-valued `fs_gameDirVar` through `current.integer` and cast the truncated 32-bit integer to a byte pointer. This is not safe on LP64 Android.

## Changes

### Original BGame source correction

Both original weapon paths now inspect the native-width string member:

```cpp
fs_gameDirVar->current.string[0] != '\\0'
```

The original control flow is unchanged. The neighboring numeric `player_adsExitDelay->current.integer` accesses remain numeric.

### Original dvar service edge

The DQ audit now performs a second relocatable AArch64 link using:

- the staged exact BGame melee registration statements extracted from original `bg_misc.cpp`;
- the complete original `libiw3_sp_dvar_android.a` built from `dvar.cpp` and its existing Android providers;
- the previously audited original client/aim-assist object.

The gate requires `Dvar_RegisterFloat`, `Dvar_RegisterVariant`, and `Dvar_RegisterNew` to be defined and absent from the undefined-symbol table. It deliberately keeps `Sys_LockWrite` and `Sys_UnlockWrite` visible as unresolved runtime synchronization services. The registration slice is still not invoked.

### Full weapon translation-unit audit

The native workflow now compiles the complete original `bg_weapons.cpp` with the Android NDK and checks:

- ELF64 / AArch64 architecture;
- definitions for `BG_ShutdownWeaponDefFiles`, `BG_LoadWeaponDef`, and `BG_LoadWeaponDef_FastFile`;
- the real `fs_gameDirVar` global remains an external engine dependency.

The object is audit evidence only. It is not linked into the JNI diagnostic APK or a running game.

## Validation

The current-head native ARM64 workflow must emit:

- `IW3_ORIGINAL_BGAME_MELEE_DVARS_DVAR_REGISTER_FLOAT_EDGE_RESOLVED_AARCH64_GREEN`
- `IW3_ORIGINAL_BGAME_WEAPONS_AARCH64_OBJECT_PASS`

The Python regression checks both original weapon functions, rejects the old integer-member access, preserves the numeric ADS dvar access, and requires the ARM64 compile/link gates.

CI results are recorded in the PR follow-up after the run completes. Do not treat a source regression or object compilation as runtime evidence.

## Remaining boundary

- Original BGame string-dvar pointer truncation fixed: source change committed.
- Original BGame weapon translation unit compiled for AArch64: pending CI.
- Original Dvar_RegisterFloat service relocatably linked: pending CI.
- BG_RegisterDvars invoked in a live Dvar registry: false.
- Weapon definitions loaded: false.
- Client runtime linked: false.
- CGame initialized: false.
- Real FastFile/BSP map loaded: false.
- Original renderer frame presented: false.
- Touch consumed by live client command/frame loop: false.
- Weapon fire, damage, actor AI and death executed on Android ARM64: false.
- Playable APK: false.

PR #4 remains open and unmerged.
