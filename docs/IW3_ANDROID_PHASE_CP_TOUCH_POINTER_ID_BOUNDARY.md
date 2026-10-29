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

The Activity now performs a bounded startup smoke using pointer ID 31: press,
read the JNI snapshot, release, verify the released state, and reset all touch
state. The emulator script requires `IW3_JNI_SPARSE_POINTER_ID_31_PASS` in
logcat, so the test exercises the exact JNI wrapper that previously rejected
valid IDs. This remains diagnostic input plumbing, not a live game command.

## Validation boundary

The regression is included in the repository's `test_iw3_android_*.py` suite.
Validation on code/documentation head `41fa9aa` (2026-10-29):

- [Source preflight](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40901939379): PASS.
- [Original-source Android ARM64 audit](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40901939625): PASS; the log reports 269 Python tests passed and retains explicit `IW3_CLIENT_RUNTIME_LINKED=false`, `IW3_TOUCH_ADAPTER_RUNTIME_INVOKED=false`, `IW3_REAL_MAP_LOADED=false`, and `IW3_PLAYABLE_APK=false` markers.
- [JNI diagnostic build/signing](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40901939360): PASS; artifact is a signed diagnostic package, not a game.
- [Android emulator runtime proof](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40901939446): PASS on x86_64. Logcat contains `IW3_JNI_SPARSE_POINTER_ID_31_PASS down=1 up=0`, `IW3_JNI_SLIDE_CHORD_USERCMD_PASS`, and `IW3_ORIGINAL_CPP_EXECUTED_INSIDE_ANDROID_EMULATOR_GREEN`. [Evidence artifact 12908793878](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40901939446/artifacts/12908793878) contains the emulator logs/screenshots.

The native host CTest also exercises pointer ID 31. The emulator run is diagnostic only and does not prove physical ARM64 execution, a real map load, rendering, or gameplay.

No renderer, real map/FastFile startup, original active client loop, weapon/actor
simulation, or physical ARM64 gameplay is claimed. The JNI APK remains
diagnostic only. PR #4 must remain open and unmerged.
