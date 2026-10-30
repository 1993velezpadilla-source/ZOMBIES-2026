# Android ARM64 pass DQ — original BGame melee dvar service

Date: 2026-10-30

## Starting point

After pass DP, the relocatable original client/aim-assist object had these service edges:

- MyAssertHandler — resolved by the Android fatal assertion provider.
- scrPlaceView — defined by the complete original screen_placement.cpp object.
- player_meleeRange — still undefined because its original storage and registration live in BGame bg_misc.cpp.

The last edge is not a generic Android API. It belongs to the original BGame dvar registry.

## Change

Added tools/iw3_android/prepare_real_engine_melee_dvar_services.py. It reads the original third_party/KisakCOD/src/bgame/bg_misc.cpp and stages:

- the original pointer definitions for player_meleeRange, player_meleeWidth, player_meleeHeight, and player_meleeChargeFriction;
- the exact original DvarLimits setup and Dvar_RegisterFloat statements for all four values, copied from BG_RegisterDvars.

The generated function is named z2026_android_register_original_melee_dvars. It is an audit slice containing the original registration statements, not a replacement for the full BG_RegisterDvars function. It is not called by the diagnostic app.

The ARM64 workflow compiles the generated source, checks ELF64/AArch64, then relocatably links it with the original client/aim-assist and DP platform-service object. It requires all four melee dvar globals to be defined and no longer undefined. Dvar_RegisterFloat remains unresolved as a real runtime service.

## Validation

The Python regression regenerates the source from bg_misc.cpp, verifies the exact four pointer definitions and registration blocks, and checks that runtime registration remains false.

The ARM64 workflow must emit:

IW3_ORIGINAL_BGAME_MELEE_DVAR_PROVIDER_EDGE_RESOLVED_AARCH64_GREEN

The uploaded artifact contains the generated source, report, AArch64 object and symbol tables only. It is not an APK.

## Remaining boundary

- BG_RegisterDvars invoked: false.
- Melee dvars registered in a live Dvar system: false.
- Client runtime linked: false.
- CGame initialized: false.
- Real map loaded: false.
- Renderer frame proven: false.
- Gameplay proven: false.
- Playable APK: false.

PR #4 remains open and unmerged.
