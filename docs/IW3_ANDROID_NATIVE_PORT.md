# IW3 native Android port — engineering gates

## Complete original SP frame separated from Windows graphics

The complete original `G_RunFrame` moved from `game/g_main.cpp` into
`game/g_runframe.cpp`, selected by the real Windows SP build as well as the
native Android CMake target. `game/g_level.h` shares the original state
fields with bootstrap; `server/server_frame.h` shares its enum. There are
no alternate entities, simulated frame, no-op gameplay callbacks or fake
renderer. All original frame phases and call order are preserved. The only
new body corrections convert two classname string IDs through the original
`SL_ConvertToString` instead of interpreting small integers as addresses.
The preservation test verifies the entire 303-line pre-move function hash
with those two corrections normalized back.

Original pointer-bearing types now have explicit 32/64-bit layout checks
(`SpawnVar`, parser state, string table, entity handles). Fixed-layout wire
and trigger checks remain active. Standard alignment replaces MSVC-only
syntax for the types reached by the frame, retaining Win32 alignment and
respecting native pointer/long-double requirements. GCC and Clang compiled
the full frame against these **actual** engine declarations without Win32,
Miles or Direct3D headers. Compiler dependency files and actual archive
symbols are audited; original gameplay service references remain unresolved
and are listed explicitly. No callback implementations are invented to make
the frame link or appear to run.

`libiw3_sp_frame.a` is a compiled engine module, **not linked into the JNI
APK** and not a playable engine. Source-only verification cannot mark its
Android compilation as passed; the ARM64 ELF/symbol/dependency audit must
finish on the pushed commit. Windows SP build and real original SP runtime
checks also run to protect the refactor. Temporary instrumentation follows
the new frame file and still calls the original weapon/actor APIs.

Local validation: complete frame compiles with GCC 13 and Clang 18;
59 Python tests and 7 existing native CTest checks. CI results are pending
until the actual runs finish. Next: resolve the actual remaining services,
bootstrap/data loading and native renderer, then observe gameplay on ARM64.

## Current verification pass — native rounding and physics pool integration

The actual `qcommon.h` unconditionally included Intel SSE and MSVC intrinsics.
Its `SnapFloatToInt` and `SnapFloat` now live in the engine's small
`qcommon/snap_float.h` header. The x86 instruction remains the original
implementation; ARM64 uses a checked current-rounding-mode conversion with
the same integer results (including NaN, Infinity and out-of-range inputs).
The host regression compares the portable path against actual x86 CVTSS2SI
for **4,000,000 bit-pattern/mode combinations** in four rounding modes.
The native Android library and JNI diagnostic compile/use this same header.

Auditing `Pool_Init` callers also exposed a missed 64-bit defect in the real
`Phys_Init`: it still used `0x70` as the item stride. `PhysObjUserData` is
120 bytes on the tested 64-bit ABI, rather than the original 112 bytes.
The genuine engine caller now uses `INIT_STATIC_POOL` and `sizeof` via its
original macro. Its payload declaration moved unchanged in field order to
`physics/phys_userdata.h` (32-bit enum explicitly preserved), allowing both
engine and tests to consume the real type. CTest allocates, writes, exhausts
and frees all 512 original physics payloads. The JNI pool smoke also uses
this real payload instead of a synthetic slot type.

The Android emulator gate now requires native touch DOWN **and** UP for the
same pointer, finite valid coordinates, successful native return values,
and actual Activity resume/pause/resume. Runtime failures override passing
markers. Nine parser regression tests reject incomplete or failing logs;
their fixtures are not device evidence. Every original-source edit now
re-triggers all three native/Android workflows.

Local validation: 57 Python tests, 6/6 host CTest cases, and 6/6 ASAN/UBSAN
cases passed. LeakSanitizer cannot inspect `/proc/.../task` in this local
runtime, so local leak detection was disabled; the CI sanitizer step enables
it. Android ARM64 compilation and emulator results for this change must be
checked on its exact pushed commit before calling those gates passed.

CI on commit `844c1d1` confirmed the six native tests, ASAN/UBSAN with
leak detection enabled, Android AArch64 ELF and signed ARM64 JNI package.
The stricter emulator test correctly failed because no touch DOWN/UP was
observed, despite successful JNI/component execution. The follow-up wakes
and unlocks the emulator, locates the real visible TextView through Android
UI hierarchy, injects a real ADB touchscreen tap at its center, and captures
screenshots/window state even on failure. The readback requirement remains
strict. The evidence reader validates the latest Activity instance after
initial landscape recreation, and rejects stale touches from older instances.
The Windows build exposed a `min/max` macro collision in the new
header; parenthesized numeric-limit calls and a macro-enabled host compile
regression correct that issue. Both checks must pass on the follow-up commit.

**Full-game blocker now:** the frame is a portable source module, but its
original script, actor/entity-update and client services still need native
Android linkage and execution. The bootstrap `g_main.cpp` and graphics/data
systems retain Windows dependencies. Map loading and the real renderer are
still required before gameplay is possible. Compiling the frame archive is
not evidence of a running Android game.

**Objective:** actual **KisakCOD IW3 Single-Player C++ source** running on
Android ARM64, not a replacement Godot game, PC emulator, Android shell,
or CoD4 multiplayer/Steam. Base source:
`third_party/KisakCOD` (upstream `SwagSoftware/KisakCOD`).

## Proven baseline before this branch

Windows x86 native IW3-SP: C++ executable ran a real SP game frame,
spawned NPC actors, equipped an original registered weapon, and dispatched
`FireWeapon` and `Bullet_Fire`. These were direct runtime trace callbacks
in CI [40141908316](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40141908316).
No custom zombie level/gameplay, actual video render, impacts, or ARM64
were confirmed by that test.

## Evidence gates (strict)

| Gate | Status | Proof required |
| --- | --- | --- |
| 0. Real Windows IW3 SP runs and fires | PASS | Native executable traces from 40141908316 |
| A. Genuine IW3 SP C++ on Android ABI | **PASS — [run 40154663973](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40154663973)** | NDK builds ELF64 AArch64 .so directly from vendored `com_math_anglevectors.cpp` (only include shim); same source executes mathematically correct host smoke |
| B. Android entry point / lifecycle | OPEN | JNI/NativeActivity loads engine subsystem and handles native Android input; instrumentation proves actual source callbacks, not mocked |
| C. IW3-SP systems in Android process | OPEN | Serverless original SP actor, weapon, frame update functions execute on ARM64, no Steam |
| D. Portable renderer | OPEN | Direct3D9-specific `gfx_d3d` dependencies replaced by original-engine-adapted GLES/Vulkan backend; draws a correct frame |
| E. Original playable level / touch | OPEN | Licensed/original map loads on device; touch movement, ADS, attack, hit, damage, rounds verified |
| F. First **IW3 engine** Android APK | OPEN | Full Android app actually runs integrated IW3 engine (not Godot) on a physical Android device |

**Do not call Gate A a playable Android IW3 port.** It links only
original IW3 aim/orientation calculations as the first transplanted
translation unit. Other gates remain unproven.

## Why an Android APK cannot be built by simply switching CMake targets

KisakCOD root CMake explicitly sets `KISAK_PLATFORM win32` and the SP
CMake target lists `GFX_D3D`, `WIN32_SRC`, `MSSLIB` and `STEAM_HEADERS`.
`src/win32/win_main.cpp` includes `<Windows.h>`, Windows window/message
APIs and `gfx_d3d/r_init.h`. The codebase was authored for 32-bit MSVC
and DirectX9 and relies on Windows runtime DLLs for Miles/Bink/Steam.
An Android NDK compiler cannot link these libraries or D3D9 into a
native ARM64 game. Source-level platform, renderer, audio, ABI, input and
asset-loader work is required.

Changing Steam startup behavior on Windows is **not** a platform port.

## First verified source-level action

`tools/iw3_android/prepare_real_engine_math.py` takes the **unchanged**
original `src/universal/com_math_anglevectors.cpp` and swaps *only*
its Win32-heavy include headers in a temporary build copy. All original
function bodies (AngleVectors, AnglesToAxis, Vec4Normalize, AnglesToQuat,
Com_SurfaceTypeFromName and Com_SurfaceTypeToName) and the original
60-entry IW3 surface/material table stay exactly as-is. `android/iw3-native/native_math_abi.cpp` provides
a tiny exported C ABI that calls the original `AngleVectors()` and
checks original angles/basis conventions and real IW3 surface class names
(including the engine's original foliage/foilage alias). Unused `AnglesToQuat`
and its `AxisToQuat` dependency are discarded at link time; no stub of
the engine function is used.

The CI **passed** real binary host smoke **and** a NDK cross-compile
in [run 40154663973](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40154663973),
validates AArch64 ELF64 with `llvm-readelf` and publishes only
`libiw3_sp_math.so` with source hashes and symbol evidence.
The binary is `libiw3_sp_math.so` (with math and surface C++ logic).
A shared engine-component library is **NOT an APK**, nor proof of an
entire Android gameplay runtime.

No game archive, assets, data files, proprietary maps or models are
required or redistributed for Gate A. Godot and the earlier misleading
APK are not built or used by this branch.

## Next implementation priorities

Android-native platform services (window lifecycle, monotonic clock,
threads, filesystem, usercmd input); removal of Direct3D and
Windows-only import assumptions; decoder/data-loading and render
backend; then remaining SP gameplay core and final on-device APK.
Each gate must compile, run, and report native code evidence. Never
replace the IW3 engine with a different engine while reporting progress.

## Phase A extended / platform primitives — GREEN (25 Oct 2026)

[GitHub Actions run **40159451519**](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40159451519) is **SUCCESS**. It ran the real source preservation tests, **two actual host CTest executables** with assertions enabled, and produced an NDK-linked `ELF64 AArch64` native library with the expected symbols.

**Original KisakCOD C++ (no gameplay reimplementation):**
- `com_math_anglevectors.cpp`: original `AngleVectors`, `AnglesToAxis`, `Vec4Normalize` and `AnglesToQuat` remain preserved, without header-level Win32 types.
- `surfaceflags.cpp`: original 60-row material/surface registry and lookup, including the original foliage alias.
- `com_constantconfigstrings.cpp`: original 833-entry IW3 config string declarations, hashing and lookup functions; the original C++ and its data table remain byte-identical except temporary platform include substitutions. Verified examples: `bg_aimSpreadMoveSpeedThreshold=20`, `player_sprintSpeedScale=96`, `specialty_rof=2034`.

**New Android/POSIX platform boundary (native C++, not an alternative engine):**
- `z2026_platform_monotonic_ns()`: `CLOCK_MONOTONIC` nanoseconds, verified advancing in a real host run.
- `z2026_platform_set_data_root()` / `z2026_platform_read_file()`: descriptor-rooted sandbox reads with `openat`, `O_NOFOLLOW`, safe relative paths, symlink/traversal and truncation rejection. Test uses only generated text under a temporary private directory.
- `z2026_platform_touch_event()`, `touch_snapshot()`, `touch_reset()`: bounded multi-touch input state with validation, thread synchronization and native ABI symbols. **No gameplay usercmd or Android Activity event forwarding yet**.

The compiled `libiw3_sp_math.so` now contains three **real KisakCOD engine source files** plus these native platform services. It has an Android arm64 ELF architecture and Android bionic link validation, **but the tests actually EXECUTED on the Linux host, not on an Android device**.

**No APK was generated**, no Godot project was used, and no COD4 proprietary game content was bundled. There is **no claim of player/game frame, 3D graphics, or zombies executing on Android**.

**Next concrete gate:** connect real Android Activity lifecycle and input events to these services, then port original SP engine frame, actor, weapon and renderer implementations. Android on-device execution must be observed separately before any IW3-native APK is called functioning.

## Android JNI integration — real IW3 source embedded (25 Oct 2026)

**ARM64 JNI build gate GREEN:** [Actions run 40160081942](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40160081942).

`android/iw3-native/android_app/` is a minimal **Android diagnostic Activity**, not a replacement game. Its only purpose is to call the **real KisakCOD C++ source** from within an Android package using JNI, then report strict individual results. It is not a re-implemented IW3 client or gameplay mock-up.

- `org.z2026.iw3nativeprobe.EngineBridge` uses `System.loadLibrary("iw3_sp_math")` for direct JNI calls to the native shared library.
- `android/iw3-native/iw3_android_jni.cpp` invokes original engine `AngleVectors`, `Com_SurfaceTypeFromName`, `CCS_InitConstantConfigStrings` and `CCS_GetConstConfigStringIndex` through native ABI wrappers, while the Activity provides actual Android lifecycle and multi-touch events.
- Native source remains the original vendored `com_math_anglevectors.cpp`, `surfaceflags.cpp`, and `com_constantconfigstrings.cpp`, staged in a disposable build directory with only portability include changes. JNI glue is separate.
- CI compiled a **signed debug ARM64 Android APK containing `lib/arm64-v8a/libiw3_sp_math.so`** and validated its `ELF64 AArch64` architecture, exported JNI symbols, APK signature and original engine C++ entry points. The binary is retained as a CI artifact named **IW3-original-code-JNI-Android-integration-NOT-A-GAME**.
- The app intentionally prints **"NO IW3 GAME FRAME OR RENDERER YET — THIS IS NOT A PLAYABLE GAME"**. It includes no 3D scene, map, shooting, actor, simulated zombie, original COD content or game assets.
- The build gate **does not establish Android runtime success**. It establishes only that JNI methods are packaged and link correctly for Android ARM64. On-device execution must be verified separately through ADB/logcat or a real device.

**Android runtime experiment:** The additional workflow `.github/workflows/iw3-original-android-emulator-jni.yml` targets Android emulator x86_64 to execute the **same original KisakCOD C++ code** in an Android process, record the native JNI result and touch events. Its x86_64 emulator path is strictly marked as diagnostic and is **not evidence of ARM64 runtime**, although the separate ARM64 native package is compiled and signed. The runtime gate is not GREEN until those logcat markers are observed.

**Still not proven:** native `G_RunFrame`, IW3 SP actor AI or `FireWeapon` on Android, true IW3 renderer or mobile GPU output, data/map loading, and a playable IW3 Android APK. Their gates are unchanged.

## Android process executes actual IW3 source — JNI Runtime Gate GREEN

**Verified 25 Oct 2026:** [Android emulator run **40160464233**](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40160464233) completed **SUCCESS**.

The runner created a genuine Android 35 **x86_64** emulator (booted in 30s), installed the APK that was compiled with actual KisakCOD `com_math_anglevectors.cpp`, `surfaceflags.cpp`, and `com_constantconfigstrings.cpp`, and started `org.z2026.iw3nativeprobe/.MainActivity`. The Activity directly invoked C++ via JNI, rather than displaying an invented status. Its logcat output was:

```text
IW3_JNI_LIFECYCLE_1
JNI_NATIVE_ENGINE_PROBE_PASS
IW3_JNI_ACTIVITY_STARTED PASS
IW3_JNI_LIFECYCLE_2
IW3_JNI_TOUCH id=0 pressed=1 coords=0.18421052,0.2962963
IW3_JNI_TOUCH id=0 pressed=0 coords=0.18421052,0.2962963
IW3_ORIGINAL_CPP_EXECUTED_INSIDE_ANDROID_EMULATOR_GREEN
```

The `JNI_NATIVE_ENGINE_PROBE_PASS` marker originates from the C++ JNI bridge *after* all four conditions actually return passing values: original IW3 `AngleVectors` calculations, original material/surface table, original IW3 configstring initialization and lookups (including `specialty_rof` ID 2034), and Android monotonic clock. Java `IW3_JNI_ACTIVITY_STARTED PASS` is logged only after the bridge returns its real validation report. Both touch down and touch up are observed in Java/Android logcat after actual ADB screen input.

**Physical Android ARM64 build separately GREEN:** [Actions **40160241820**](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40160241820) — signed ARM64 APK containing real C++ and exported JNI functions. The x86_64 emulator pass cannot be used as proof that the ARM64 app executes correctly on a phone.

This diagnostic Android APK is **NOT the requested playable IW3 game** and cannot yet execute `G_RunFrame`, `FireWeapon`, zombies, level/map loading or IW3's renderer. User's earlier Godot APK remains rejected. Never call this phase the finished port; next priority is to link real IW3 SP `G_RunFrame` and its dependent C++ runtime into Android, then implement render backend and data loading.

## Phase B: First real `G_RunFrame` 32→64-bit ABI source fix — 25 Oct 2026

In **the actual vendored KisakCOD** `third_party/KisakCOD/src/game/g_main.cpp`, the SP `G_RunFrame` animation recheck loop contained reverse-engineered x86 pointer arithmetic:

```cpp
p_inuse = &g_entities[1].r.inuse;
v17 = *((unsigned int *)p_inuse + 34);
G_DObjUpdateServerTime((gentity_s *)(p_inuse - 168), 1);
p_inuse += 628;
```

This assumed **628-byte `gentity_s`**, and offsets **168** and **136** from `r.inuse`. It is not portable to 64-bit because game structs contain actual pointers. The vendored original **`G_RunFrame` has now been changed in-place at this exact location** to use typed accesses `animEnt->r.inuse`, `animEnt->flags`, `G_DObjUpdateServerTime(animEnt, 1)`, `++animEnt`, and the existing `FL_REPEAT_ANIM_UPDATE` / `FL_NO_AUTO_ANIM_UPDATE` enums. Original loop semantics, entity iteration order, script callbacks, and break conditions remain intact. All other original frame stages and callbacks remain unchanged.

**Verified GREEN:** [GitHub Actions 40201927349](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40201927349) — **3/3 native CTest cases passed**, including the test compiling the **verbatim** corrected `G_RunFrame` entity-loop block on a deliberately incompatible host 64-bit struct. Android NDK separately compiled that exact block to an **ELF64 AArch64** object and `llvm-readelf` validated the target. No full-frame linkage or device execution is implied.

**Evidence harness:** The source preflight explicitly rejects legacy byte-stride expressions and checks the real function's call graph and staged source hash. The Python extraction tool also copies the **exact corrected C++ entity-loop block out of the actual `G_RunFrame` source** to `iw3_g_runframe_entity_loop.inc`; host CTest compiles **that exact block** against a deliberately *different* 64-bit entity layout with multiple pointer-size-sensitive fields, checks animation callbacks and break cases. These fixture types are *ABI regression tests only* and are not a new engine, game entities, or Android gameplay. The Android NDK can additionally cross-compile the verbatim source block into an AArch64 ELF object, without linking the entire SP game.

**Narrow proof limit:** The full real `G_RunFrame` **still does not compile/link or execute in Android**; this patch eliminates *one confirmed bad Win32 entity addressing assumption*, not the remaining Win32, renderer, actor, script VM, `gentity_s` layout and 32-bit `static_assert` incompatibilities in other SP modules. No playable IW3 Android APK or 3D frame exists. CI proof links will be added after each job actually finishes GREEN; a regression failure is RED, not a success.


## Phase B native memory — KisakCOD pool allocator repaired for 64-bit

The **actual original** `third_party/KisakCOD/src/universal/pool_allocator.cpp` `Pool_Init()` was writing next-pointer links as `uint32_t`: `*(uint32_t*)&pool[...] = (uint32_t)&pool[...]`. **This truncates pointer addresses** on Android ARM64/x86_64 and corrupts the free list. The real engine source now initializes typed `freenode*` links, with minimum slot-size and alignment guards. No synthetic game allocator was swapped in. The `Pool_Alloc`, `Pool_Free`, and `Pool_FreeCount` game functions remain original.

The native-port script `tools/iw3_android/prepare_real_engine_pool.py` stages a temporary copy of the **full real corrected `pool_allocator.cpp`**, replacing only Windows-dependent headers for Android. Python source-verification tests compare the complete remainder of the source byte-for-byte and fail if legacy 32-bit pointer-truncation lines return.

`android/iw3-native/pool_native_test.cpp` runs the original allocator at 64 bits on an aligned 97-item pool: verifies all allocated addresses, exhausted state, reverse frees, active/free counts, and reuse; the Android JNI diagnostic also calls a source-linked native `Pool_*` smoke. ARM64 NDK builds use the same real source module. This is a **dependency for future SP runtime**, not the full SP game loop.

**Host + ELF GREEN:** [Native build 40209841645](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40209841645): 4/4 CTest checks passed and ELF64 AArch64 artifact linked with corrected allocator.

Strict limits remain: no full `G_RunFrame` linked or executed on Android, no genuine IW3 graphics/game scene, and no playable IW3 Android APK. Diagnostic APKs must never be relabeled as working zombies games.


## Phase C — Android app-private file-root JNI gate (October 25, 2026)

The Android `MainActivity` now initializes the **native C++ platform file root** with `getFilesDir()` before calling the real-engine JNI smoke. The `nativeSetDataRoot` JNI method uses the existing `z2026_platform_set_data_root` descriptor-based POSIX adapter; `nativeReport` verifies actual file contents through `z2026_platform_read_file`. This is a necessary bridge for eventual IW3 map and fastfile access. A tiny explicitly diagnostic sentinel (`iw3-native-io-probe.bin`) is used **only for I/O verification**, not a fake map or game asset. Negative probes reject `../` traversal and too-small output buffers. The emulator CI now fails unless `IW3_JNI_SANDBOX_IO_PASS` is logged. Host CI additionally verifies `main/native-test.iwd` nested path access and rejects directory symlinks; the host test uses synthetic bytes strictly for sandbox behavior, not IW3 asset parsing.

**Not yet implemented:** mounting/loading actual IW3 IWD/FF archives through `FS_*`, building a 3D renderer, running the real single-player `G_RunFrame`, mapping touch into authentic `usercmd`, or an Android ARM64 playable zombies APK. The Activity remains explicitly diagnostic; it is not a game or a substitute engine. Do not treat CI passing these gates as proof of gameplay.

## Phase D — authentic IW3 SP combat hit-location pointer fix: verified

`src/game/g_combat.cpp::G_HitLocStrcpy` previously computed a destination-minus-source pointer delta and **stored it in a 32-bit `int`**, then indexed from the source address. This is unsafe on 64-bit Android and is undefined behavior for unrelated pointers even on 32-bit systems. The actual vendored KisakCOD function now performs the **same forward NUL-terminated byte copy** with incremented `unsigned char*` / `const char*` pointers, without a truncated integer address. No weapon damage behavior was invented or replaced.

The native source staging script extracts the exact corrected original SP function into a disposable translation unit, preserving its body; Python tests reject the old pointer arithmetic. The native library compiles the function on ARM64 and the ABI wrapper calls it in host/Android diagnostics; the host test exercises a real 64-bit buffer with canaries and empty strings.

**October 25 verification:**
- [ARM64 original-source gauntlet 40210356905](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210356905): **5/5 CTest GREEN**, ELF64 AArch64 linked, native `z2026_iw3_hitloc_copy_smoke` exported.
- [ARM64 JNI diagnostic build 40210356891](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210356891): **GREEN**, signed diagnostic APK contains real IW3 native modules and JNI data-root entrypoint.
- [Android x86_64 emulator 40210343051](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210343051): **GREEN**, original engine JNI probe, app-private native file-root I/O, traversal rejection and touchscreen event logged PASS.

**All three are component/infrastructure proofs, not a working game.** The next high-priority blockers remain linking and executing full `G_RunFrame`, authentic archive/map load, native IW3 rendering and usercmd gameplay input.

## Phase E — Authentic IW3 IWD filename lookup staged for Android (25 Oct 2026)

**Blocker addressed:** The game cannot find `.iwd` archive members without reproducing its *real* filename lookup semantics. Rather than inventing a replacement archive index, the Android native module now compiles **verbatim** `FS_HashFileName`, `FS_FilenameCompare`, and `FS_ConvertPath` from the vendored original `src/universal/com_files.cpp`, plus the original `I_islower` from `src/universal/q_shared.cpp`. `tools/iw3_android/prepare_real_engine_iwd_names.py` extracts those exact bodies to a disposable translation unit, records source/function SHA-256 and rejects unexpected engine changes. It never modifies the original files.

`android/iw3-native/iwd_names_native_test.cpp` tests real map, script and weapon paths, mixed case, Windows/Unix separators, original archive hash values, equality/inequality and `FS_ConvertPath`. The same engine functions are linked into the ARM64 library and the Android JNI diagnostic `z2026_iw3_iwd_names_smoke`; emulator evidence now **requires** `IW3_JNI_IWD_NAMES_PASS`. The native CMake target fails closed if the staged original source is absent.

**Verification status — native host + ARM64 GREEN:** [GitHub Actions 40212690694](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690694) completed **SUCCESS** at source SHA `91a7df2316bb4c65a25f5bd40b39caba42d0a552`. Both Release and ASAN/UBSAN host configurations passed **7/7 CTest**, including original IW3 archive-name routines; the ELF64 AArch64 native library linked with the original code and exported `z2026_iw3_iwd_names_smoke`. **This does not establish Android device runtime or APK gameplay.** The [JNI ARM64 APK workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690774) and [Android emulator runtime workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690668) must complete independently before their respective gates can be called GREEN.

**Still missing:** actual `FS_*` IWD ZIP archive opening, archive member streaming, fastfile (`.ff`) loading, IW3 map/BSP load, full single-player `G_RunFrame`, renderer, touch-to-`usercmd` and gameplay. The signed Android JNI APK is **not playable**. This phase only ports original archive filename hashing/normalization; it does not claim game content is mounted or rendered.

## Phase C — authentic ZIP32/IWD archive reader on 64-bit (25 Oct 2026)

The next asset-loading dependency is now ported as a real engine module:
`third_party/KisakCOD/src/qcommon/unzip.cpp` and its original `unzip.h`.
The old Windows ABI used 32-bit `unsigned long`; LP64 Android widens it to
64 bits. Active ZIP32 fields and public offsets/sizes now use `uint32_t`,
preserving their original Win32 width and the 80-byte `unz_file_info`
layout. The actual parser's little-endian readers decode the 2- and 4-byte
archive fields explicitly, support both fixed-width record fields and native
zlib counters, and reject short field reads. The IWD filename-position call
in `com_files.cpp` now passes the real `uint32_t` field directly.

The Android adapter implements the original `FS_File*` calls required by
this parser using POSIX `FILE*` I/O and retains KisakCOD's non-stdio seek
enum (0=current, 1=end, 2=absolute). The old int-sized file API deliberately
rejects archives over `INT_MAX`; ZIP64 and full search-path integration are
not claimed. The source-staging script replaces only the Windows-heavy
include pair and verifies the actual vendored parser body/hash. It does not
synthesize a second ZIP reader.

The host/ASAN test generates a disposable two-entry ZIP fixture (one stored,
one raw-deflate), then calls the actual `unzOpen`, central-directory
enumeration, current-file open/read/close and end-of-list APIs. The Android
JNI diagnostic runs the same native parser smoke in app-private cache and
requires an explicit `IW3_JNI_UNZIP_PARSER_PASS` log marker. This fixture is
test data only, not a game asset.

**Host build + CTest + ASAN/UBSAN passed** in [run 40222518391](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40222518391); it includes the new archive-reader test. The exact ARM64 link and Android emulator runtime gates must also pass before calling this phase fully green.

Strict limit: this is still an isolated archive-parser dependency, not the engine's `FS_LoadZipFile` search-path system. Fastfile/IWD search-path initialization, actual map loading, native renderer, linked SP frame services, touchscreen-to-`usercmd` mapping and gameplay remain unimplemented. The JNI APK remains diagnostic only.
