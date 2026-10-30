# IW3 Android ARM64 pass DR — resolve the original client/dvar writer-gate edges

Date: 2026-10-30

## Starting point

The current PR head had already compiled and relocatably linked the original client command/aim-assist chain, the Android fatal assertion provider, original screen-placement storage, the original BGame melee-dvar registration slice, and the full original `dvar.cpp` archive.

The prior combined symbol report deliberately showed two remaining dependencies from the original dvar code:

- `Sys_LockWrite(FastCriticalSection*)`
- `Sys_UnlockWrite(FastCriticalSection*)`

These were not missing engine algorithms. The repository already had a tested Android/POSIX provider in `android/iw3-native/iw3_android_fs_lock_io.cpp`, introduced for the authentic filesystem read path. That provider preserves the original eight-byte `FastCriticalSection` counter layout, uses sequentially-consistent compiler atomics to preserve the Win32 full-barrier semantics, and yields with `sched_yield()` while contended.

## Changes

The native Android workflow now:

1. Cross-compiles that same provider source with the Android NDK for AArch64.
2. Checks the resulting object is ELF64/AArch64.
3. Verifies both real C++ symbols in the provider object.
4. Performs a relocatable link of the existing client + original dvar combined object with the provider object.
5. Requires both writer-gate symbols to be defined and absent from the combined object's undefined-symbol report.
6. Uploads the provider object, ELF/symbol reports, combined-link reports, and a JSON evidence manifest.

The old check that expected the two symbols to remain undefined was replaced with a fail-closed check that requires them to resolve. No no-op lock functions were added, and the provider is not linked into the diagnostic JNI APK by this change.

A Python regression protects the workflow wiring and the provider's algorithm contract. The existing host CTest already exercises the same provider with a held reader gate and eight contending writers (12,000 protected increments per thread).

## Validation result (verified 30 Oct 2026)

The current native Android workflow completed successfully:

- [ARM64 source audit, run 41062716885](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41062716885) — **SUCCESS**.
- Python regression suite: **387 tests passed**.
- Host CTest: **25/25 passed** in both configured test passes, including the sanitizer pass.
- The provider object was confirmed ELF64/AArch64 and defined both `Sys_LockWrite(FastCriticalSection*)` and `Sys_UnlockWrite(FastCriticalSection*)`.
- The relocatable client/dvar/provider object defined both symbols and no longer listed either as undefined.
- Required marker: `IW3_ORIGINAL_BGAME_MELEE_DVAR_WRITER_GATE_EDGES_RESOLVED_AARCH64_GREEN`.
- Evidence artifact: [12981675408 — ARM64 audit objects and reports, NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/41062716885/artifacts/12981675408).

The report retains the negative scope markers:

- `IW3_CLIENT_RUNTIME_LINKED=false`
- `IW3_REAL_MAP_LOADED=false`
- `IW3_GAMEPLAY_PROVEN=false`
- `IW3_PLAYABLE_APK=false`

## Boundary

This closes two symbols in a relocatable client/dvar dependency audit. It does not invoke the dvar registration functions, initialize the client, link the Android game runtime, mount licensed game data, load a FastFile/BSP, initialize the renderer, or prove physical ARM64 gameplay. The JNI APK remains diagnostic. PR #4 must remain open and unmerged.
