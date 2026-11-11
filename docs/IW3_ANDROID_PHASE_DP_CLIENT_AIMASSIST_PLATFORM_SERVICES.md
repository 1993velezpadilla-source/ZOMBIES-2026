# Android ARM64 pass DP — original client aim-assist platform services

Date: 2026-10-30

## Starting point

The current-head ARM64 audit (41016149290) successfully compiled and relocatably linked the original SP client command chain through:

- CL_CreateCmd and its Android touch hook;
- CL_FinishMove and CL_MouseMove;
- original CL_KeyMove, CL_CmdButtons, stance helpers and ClampChar;
- original aim-assist mouse input, predicted player-state access, tweakable/ADS helpers, and auto-melee helpers.

The resulting object still had three genuine service edges: MyAssertHandler, scrPlaceView, and the server-owned player_meleeRange dvar pointer. The first two are platform/client services that can be supplied without substituting aim-assist or client logic.

## Changes

### Android fatal assertion provider

Added android/iw3-native/iw3_android_assert.cpp, which defines the original MyAssertHandler symbol for Android. It formats the original filename, line, type and variadic message; writes a fatal Android log entry through logcat; then aborts. The host branch writes the same context to stderr and aborts.

This is intentionally not a no-op assert stub. Continuing after an engine invariant failure would risk corrupt client, database or gameplay state. The original Win32 assertive.cpp remains unchanged and is not compiled as the Android provider.

A host regression forks a child, invokes the provider, and requires both SIGABRT and the formatted assertion context.

### Original screen placement

Added an Android ARM64 object-only compile gate for the complete original third_party/KisakCOD/src/client/screen_placement.cpp translation unit. Its real ScreenPlacement scrPlaceView[1] storage and viewport setup routines are preserved. The source is not linked into the JNI diagnostic package and its zero-initialized global is not claimed to be initialized at runtime.

### Combined dependency audit

The native ARM64 workflow compiles the original screen-placement translation unit and the Android fatal-assert provider, then relocatably links both with the already-audited original client/aim-assist object. It requires MyAssertHandler and scrPlaceView to move from undefined to defined.

The server-owned player_meleeRange remains deliberately unresolved. This pass does not register its dvar, initialize CGame or screen placement, link the client runtime, load a map, or prove gameplay.

## Validation

The host CTest target iw3_android_assert_provider_abort_semantics validates fatal assertion behavior and message formatting.

The ARM64 workflow must emit:

IW3_ORIGINAL_CLIENT_AIMASSIST_PLATFORM_SERVICE_EDGES_RESOLVED_AARCH64_GREEN

The associated artifact contains ELF64/AArch64 objects and symbol reports only; it is not an APK.

## Remaining boundary

- Client runtime linked: false.
- Screen placement runtime initialized: false.
- Aim-assist dvars registered: false.
- CGame initialized: false.
- Real map loaded: false.
- Gameplay proven: false.
- Playable APK: false.

PR #4 remains open and unmerged.
