# IW3 Android pass CP — sparse JNI touch-pointer IDs

Date: 2026-10-29

## Blocker found

The native platform touch adapter and Activity already accept Android MotionEvent
pointer IDs 0..31, while reserving only ten simultaneous native touch slots. The
JNI `nativeTouchSnapshot` wrapper incorrectly rejected IDs 10..31 by checking
`id >= 10`. As a result, a valid sparse pointer could be registered and applied
to the original `usercmd_s` adapter but its JNI observation immediately returned
an error. This contradicted the Activity and platform contracts and made
multi-touch diagnostics misleading for pointer IDs above 9.

## Change

- Added a named JNI boundary constant for the Android pointer-ID domain (32).
- Changed `nativeTouchSnapshot` to validate against that domain, not the number
  of internal simultaneous-touch slots.
- Added a Python regression that compares the JNI bound with the Activity and
  native platform declarations and rejects reintroduction of the old ten-ID
  limit.
- Existing native host coverage already exercises pointer ID 31 and verifies it
  remains independent of another active pointer; that behavior is now aligned
  with the JNI snapshot wrapper.

This is a real input-boundary bug fix, not a gameplay implementation. The
Android Activity still calls the diagnostic snapshot API; the original
`CL_CreateCmd` touch hook remains staged/compile-audited rather than invoked by
the running Android process.

## Validation boundary

The regression is included in the repository's `test_iw3_android_*.py` suite.
CI for the new commits must pass before this change is treated as validated.
The native host CTest that exercises pointer ID 31 remains part of the existing
Android portability workflow.

No renderer, real map/FastFile startup, original active client loop, weapon/actor
simulation, or physical ARM64 gameplay is claimed. The JNI APK remains
diagnostic only. PR #4 must remain open and unmerged.
