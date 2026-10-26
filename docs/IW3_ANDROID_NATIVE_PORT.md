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
- `z2026_platform_touch_event()`, `touch_snapshot()`, and `touch_reset()` track bounded multi-touch state. The Activity now forwards MotionEvents into an adapter that fills the original `usercmd_s` layout; connecting those commands to `CL_CreateCmd` and player simulation remains pending.

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

**Not yet implemented:** mounting/loading actual IW3 IWD/FF archives through `FS_*`, building a 3D renderer, running the real single-player `G_RunFrame`, wiring the touch-to-`usercmd_s` adapter into `CL_CreateCmd` and player simulation, or an Android ARM64 playable zombies APK. The Activity remains explicitly diagnostic; it is not a game or a substitute engine. Do not treat CI passing these gates as proof of gameplay.

## Phase D — authentic IW3 SP combat hit-location pointer fix: verified

`src/game/g_combat.cpp::G_HitLocStrcpy` previously computed a destination-minus-source pointer delta and **stored it in a 32-bit `int`**, then indexed from the source address. This is unsafe on 64-bit Android and is undefined behavior for unrelated pointers even on 32-bit systems. The actual vendored KisakCOD function now performs the **same forward NUL-terminated byte copy** with incremented `unsigned char*` / `const char*` pointers, without a truncated integer address. No weapon damage behavior was invented or replaced.

The native source staging script extracts the exact corrected original SP function into a disposable translation unit, preserving its body; Python tests reject the old pointer arithmetic. The native library compiles the function on ARM64 and the ABI wrapper calls it in host/Android diagnostics; the host test exercises a real 64-bit buffer with canaries and empty strings.

**October 25 verification:**
- [ARM64 original-source gauntlet 40210356905](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210356905): **5/5 CTest GREEN**, ELF64 AArch64 linked, native `z2026_iw3_hitloc_copy_smoke` exported.
- [ARM64 JNI diagnostic build 40210356891](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210356891): **GREEN**, signed diagnostic APK contains real IW3 native modules and JNI data-root entrypoint.
- [Android x86_64 emulator 40210343051](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40210343051): **GREEN**, original engine JNI probe, app-private native file-root I/O, traversal rejection and touchscreen event logged PASS.

**All three are component/infrastructure proofs, not a working game.** The next high-priority blockers remain linking and executing full `G_RunFrame`, authentic archive/map loading, native IW3 rendering, and wiring the usercmd adapter into real player gameplay.

## Phase E — Authentic IW3 IWD filename lookup staged for Android (25 Oct 2026)

**Blocker addressed:** The game cannot find `.iwd` archive members without reproducing its *real* filename lookup semantics. Rather than inventing a replacement archive index, the Android native module now compiles **verbatim** `FS_HashFileName`, `FS_FilenameCompare`, and `FS_ConvertPath` from the vendored original `src/universal/com_files.cpp`, plus the original `I_islower` from `src/universal/q_shared.cpp`. `tools/iw3_android/prepare_real_engine_iwd_names.py` extracts those exact bodies to a disposable translation unit, records source/function SHA-256 and rejects unexpected engine changes. It never modifies the original files.

`android/iw3-native/iwd_names_native_test.cpp` tests real map, script and weapon paths, mixed case, Windows/Unix separators, original archive hash values, equality/inequality and `FS_ConvertPath`. The same engine functions are linked into the ARM64 library and the Android JNI diagnostic `z2026_iw3_iwd_names_smoke`; emulator evidence now **requires** `IW3_JNI_IWD_NAMES_PASS`. The native CMake target fails closed if the staged original source is absent.

**Verification status — native host + ARM64 GREEN:** [GitHub Actions 40212690694](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690694) completed **SUCCESS** at source SHA `91a7df2316bb4c65a25f5bd40b39caba42d0a552`. Both Release and ASAN/UBSAN host configurations passed **7/7 CTest**, including original IW3 archive-name routines; the ELF64 AArch64 native library linked with the original code and exported `z2026_iw3_iwd_names_smoke`. **This does not establish Android device runtime or APK gameplay.** The [JNI ARM64 APK workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690774) and [Android emulator runtime workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40212690668) must complete independently before their respective gates can be called GREEN.

**Still missing:** actual `FS_*` IWD ZIP archive opening, archive member streaming, fastfile (`.ff`) loading, IW3 map/BSP load, full single-player `G_RunFrame`, renderer, and wiring touch-derived `usercmd_s` into actual gameplay. The signed Android JNI APK is **not playable**. This phase only ports original archive filename hashing/normalization; it does not claim game content is mounted or rendered.

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

**Host build + CTest + ASAN/UBSAN passed (8/8 CTest cases), and the ARM64 ELF64/AArch64 native library linked** in [run 40222518391](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40222518391); it includes the new archive-reader test. The ARM64 JNI diagnostic APK package/signature and symbol checks passed in [run 40222518411](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40222518411). The actual archive-parser smoke then **executed successfully inside an Android x86_64 emulator**, with explicit `IW3_JNI_UNZIP_PARSER_PASS`, Activity lifecycle and touch readback evidence in [run 40222518427](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40222518427). This is not ARM64 physical-device gameplay and none of these artifacts is a playable game.

Strict limit: this is still an isolated archive-parser dependency, not the engine's `FS_LoadZipFile` search-path system. Fastfile/IWD search-path initialization, actual map loading, native renderer, linked SP frame services, and consumption of the touch-derived `usercmd_s` by gameplay remain unimplemented. The JNI APK remains diagnostic only.


## Phase C — Android touch mapped to original IW3 SP usercmd layout

The Android platform boundary now compiles the authentic `usercmd_s` declaration and `BUTTON_*` constants from `third_party/KisakCOD/src/qcommon/msg.h`. `iw3_android_usercmd_compat.h` adapts only the header's MSVC integer spellings; compile-time guards enforce the original 56-byte structure and field offsets. Touch roles map a left drag to signed forward/right movement, a right drag to the original packed angle representation, and fixed touch zones to the original attack, ADS, jump, reload, use, melee, crouch, and prone button bits. Host CTest checks each action, multi-touch aggregation, release behavior, bounds, and reset.

The Android Activity queries the real `usercmd_s` fields after every Android MotionEvent. The emulator runner taps the attack zone using the actual screenshot dimensions and requires logcat evidence that `BUTTON_ATTACK` (bit 0 from the original header) reaches the command snapshot. The runtime evidence parser now rejects a touch test if this bit is missing.

**Strict boundary:** this is a platform input adapter using the authentic command ABI; it is **not yet wired into original `CL_CreateCmd`, `SV_GetUsercmd`, `G_RunFrame`, or player simulation**. The emulator remains x86_64 and this is still diagnostic code. No map, renderer, ARM64-device gameplay, or playable APK is claimed. The next gate is to connect Android input to the original SP client/serverless frame path without bypassing real player movement, weapon, actor, and damage functions.


### Phase C verification evidence (commit `00969eaa`)

- [Native host + ARM64 source gate](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40225028631) — **SUCCESS**: 23 Python source/runtime-evidence tests; 8/8 host CTest tests; ASAN/UBSAN 8/8; original `G_RunFrame` archive audit and Android ARM64 ELF build passed.
- [Signed Android ARM64 JNI package build](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40225028685) — **SUCCESS**: original KisakCOD source linked into a signed diagnostic APK. This is still not a game APK.
- [Android emulator input-to-usercmd runtime check](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40225028656) — was still running when this note was written; do not count the runtime gate as passed until its log proves a real ADB attack touch sets original `BUTTON_ATTACK` in the `usercmd_s` snapshot.


## Phase D — Android touch merge into the original client command path

The platform adapter previously produced a diagnostic snapshot of usercmd_s; the original client never consumed it. The genuine src/client/cl_input.cpp::CL_CreateCmd source now has an Android-only call to z2026_platform_apply_touch_to_usercmd(result, clients[0].viewangles) after the existing keyboard/mouse command collection and before the original CL_FinishMove(result). Windows input remains unchanged.

The new platform function mutates the actual usercmd_s fields from qcommon/msg.h: combines movement with saturating signed-char arithmetic, maps attack/ADS/jump/reload/use/melee/crouch/prone to the original BUTTON_* values, and applies accumulated look deltas to the original client viewangles exactly once before CL_FinishMove packs the angles. Crouch/prone are made mutually exclusive, with prone taking precedence. Touch state remains synchronized and resets pending deltas on lifecycle reset.

Host regression tests now exercise this actual struct mutation (movement + attack + look), verify that a second frame does not reapply the same look delta, and verify attack release. A source-structure test requires the call to exist inside the original CL_CreateCmd and before CL_FinishMove.

**Important boundary:** this is a source-level integration and a compiled/tested platform bridge. The current Android CMake target still does not compile/link the original client/cl_input.cpp, whose remaining Win32/D3D/UI dependencies must be ported. Therefore the Android JNI APK still cannot exercise this hook in the real client, and no playable APK or in-game touch control is claimed. Next: split/port the client input TU's platform dependencies, link the original client command generation with the serverless/local SP frame, then bootstrap real game data and port the renderer.


## Current pass — original ZIP/IWD reads are confined to the Android data root

The previous ZIP32 regression only exercised the original KisakCOD `unzOpen` parser against an absolute temporary pathname. That proved decompression and ZIP32 field sizes, but did **not** prove that the reader could use the app's configured IW3 data directory. The old Android adapter also called unrestricted `fopen(filename, "rb")`.

This pass adds `z2026_platform_open_read_fd()`, `z2026_platform_write_file()`, and `z2026_platform_unlink_file()` to the POSIX boundary. Each path is relative to the retained app-owned root descriptor; component-by-component `openat` uses `O_NOFOLLOW`, rejects absolute paths, backslashes, empty/dot/dot-dot components, and requires regular files for reads. The write path also refuses symlink targets and removes partial files on write failure.

The adapter implementing the original `FS_FileOpenReadBinary` interface now wraps the descriptor in `fdopen`; it no longer uses unrestricted `fopen(filename, "rb")`. The native smoke writes a temporary ZIP under the configured data root and opens it through the **original KisakCOD `unzOpen(relativePath)`** code path, then removes it through the confined unlink API. The Android activity points the parser smoke at the same app-private `filesDir` that contains the configured data root. Host regressions cover descriptor reads, nested paths, traversal, absolute paths, symlink reads/writes, and cleanup.

This is a real platform I/O improvement and a prerequisite for opening IWD archives from app-owned storage. It is **not yet an engine searchpath mount**: `FS_Startup`/IWD enumeration, `searchpath_s` population, FastFile loading and BSP/map loading are still not connected to Android. The ZIP smoke fixture is generated test data, not a COD archive or map.

The final code fix for the POSIX `close()` declaration is in commit `f2486fb00bff5314faaeedc4d14795a4c99f1c20`. On that exact commit:
- [Original-source/ARM64 workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40233218648) passed: **8/8 host CTest checks**, ASAN/UBSAN, native ARM64 ELF link, and complete original `G_RunFrame` archive/type checks.
- [Android ARM64 JNI package](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40233218609) built and passed APK signature, AArch64 ELF and symbol checks.
- [Android emulator runtime](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40233218612) passed. Its evidence explicitly confirms `original_iw3_zip32_stored_and_deflate_parser_executed: true`, touch DOWN/UP translated to the original `usercmd_s` adapter, and lifecycle resume/pause/resume. It explicitly records `arm64_device_execution_proven: false` and `gameplay_proven: false`: this is an x86_64 emulator diagnostic, not a playable game or physical ARM64 proof. The offline Windows SP runtime diagnostic is separate from Android proof.

**Next concrete gate:** port the original engine's IWD searchpath initialization to consume these rooted descriptors and demonstrate opening a real licensed IWD entry from app storage without replacing the original archive parser. After that, tackle the original FastFile and map loader. No playable Android APK exists yet.


## Follow-up — original FS_BuildOSPath and IWD discovery boundary (2026-10-25)

The rooted Android file bridge now supports the path forms the original desktop
filesystem emits. `z2026_platform_open_engine_path_fd` accepts relative paths or absolute
paths beneath the configured app-owned root spelling. The retained descriptor
is opened on the canonicalized directory; absolute-prefix matching only
produces a relative suffix that is then resolved with `openat` beneath that
descriptor. Sibling prefixes, outside absolute paths, traversal components,
and symlinks remain rejected. It normalizes the original Windows-style
backslash separators before component validation, so `FS_BuildOSPath` paths
can be consumed without weakening root confinement. The original ZIP/IWD adapter
`FS_FileOpenReadBinary` now uses this engine-path entry point instead of the
relative-only descriptor function.

A second platform primitive, `z2026_platform_list_iwd_files`, enumerates
regular `.iwd` files in a root-confined directory, supports both rooted
relative and `FS_BuildOSPath` absolute directory forms, filters symlink entries,
sorts results deterministically, and rejects insufficient output buffers
without partial results. Root-directory scans use a fresh `openat(".", ...)`
descriptor rather than `dup(rootFd)`, because duplicated directory descriptors
share a stream offset and would make a second IWD scan appear empty. A host
regression repeats the same root scan through relative and absolute paths.
The original ZIP32 parser smoke now creates a valid IWD-named fixture, discovers
it via that listing primitive, then opens it
through the original `unzOpen` using both relative and absolute paths.

Host regression coverage includes Windows-style separators, prefix attacks,
dot-dot traversal, symlinked directories, regular-file filtering, deterministic
single-entry results, repeated scans and buffer-overflow rejection. CI on
commit `500df941` reports **8/8 CTest passed**, including the original ZIP32
reader and portable platform tests, followed by **ASAN/UBSAN GREEN**:
[host/ARM64 port workflow](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40240635779).
The same source revision also passed the Android ARM64 JNI package gate:
AArch64/ELF64, exported JNI symbols and v2 APK signature verified in
[JNI build run 40240635788](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40240635788)
(artifact `12616977484`). The x86_64 Android emulator then passed the actual
Activity/JNI smoke in [runtime run 40240635813](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40240635813)
(artifact `12616297536`): the original parser opened the IWD-named fixture by
relative and absolute rooted paths, discovered it through the new directory
listing API, observed touch DOWN/UP and an attack bit in the original
`usercmd_s`, and passed pause/resume. The verifier explicitly records
`arm64_device_execution_proven: false` and `gameplay_proven: false`; these
remain diagnostic gates, not gameplay proof.

**This is not yet the original search-path mount.** `FS_AddIwdFilesForGameDirectory`
and `FS_LoadZipFile` from `universal/com_files.cpp` are still not part of the
Android library; the full engine filesystem startup, IWD hash-table construction,
FastFile loader, map loader and renderer remain unlinked. The generated IWD is
only a ZIP32 test fixture, not game content. The diagnostic must not be described
as an IWD mounted into the game or as gameplay evidence.

Next: port the real `Sys_ListFiles`/directory enumeration dependency and link
the original `FS_AddIwdFilesForGameDirectory` + `FS_LoadZipFile` code with its
real allocator/checksum/string services, then mount a user-provided IWD and
prove a real asset lookup before advancing to FastFiles/maps. Keep PR #4 open.

## Native-width IWD searchpath allocation and invalid archive handling (2026-10-25)

The latest source review found two hard-coded 28-byte allocations in the genuine
`FS_AddIwdFilesForGameDirectory` and `FS_AddGameDirectory` functions. That size
matches `searchpath_s` only in the original 32-bit Win32 ABI; the structure
contains three pointers plus four integers and grows on a 64-bit target. Both
allocations now use `sizeof(searchpath_s)`, preserving the original 28-byte
Win32 size while preventing heap overwrite on 64-bit builds.

The original `FS_LoadZipFile` also passed a failed `unzOpen` result directly
to `unzGetGlobalInfo`. It now returns cleanly on a null archive, closes an
opened archive if directory metadata is invalid, verifies that the central
directory can be positioned before indexing, and refuses to publish a partial
index when the second pass cannot read every advertised entry. Partial index
allocations and the ZIP handle are released on that failure path. The global
IWD entry count is incremented only after a complete index is built.

A source regression was added to `tests/test_iw3_android_source.py` to prevent
the Win32-sized searchpath allocation from returning and to retain the corrupt
archive guards. This improves the authentic filesystem source's 64-bit safety,
but it does **not** mean that `com_files.cpp` is linked into Android yet.
The current JNI APK still does not call the real `FS_AddIwdFilesForGameDirectory`
or mount a game IWD; FastFiles, maps, renderer, and gameplay remain open gates.

A follow-up audit caught a second Win32 assumption in the same authentic mount
path: `FS_AddIwdFilesForGameDirectory` sorted an array of `char*` using a
hard-coded four-byte `qsort` element width. On ARM64 that would partially swap
pointers and corrupt the sorted IWD list before mounting. It now passes
`sizeof(s0[0])`. The source regression explicitly rejects the old four-byte
sort and both 28-byte searchpath allocations.

The archive-index loops now validate every advertised central-directory entry
and the entry-position lookup. Empty archives are rejected before any zero-size
allocation or null-based pointer arithmetic; failed reads free the partial
index and close the ZIP handle. These changes are covered by the source gate
and the Android/Windows build workflows triggered by the latest branch commits.
They remain portability hardening of original code, not proof that the real
IWD searchpath is linked or that a map/game is running on Android.

## Native-width IWD indexer hardening and compile gate (2026-10-25)

A fresh audit of the original `FS_LoadZipFile` found that its fixed 256-byte
filename buffer was not checking `unz_file_info_s::size_filename`, and that
untrusted ZIP entry counts/name bytes flowed into signed-int `Z_Malloc` sizes.
The authentic function now rejects truncated names, guards entry-count and
name-buffer arithmetic before allocation, and handles failures from each of
the three index allocations by releasing earlier allocations and closing the
archive. It still builds the original `iwd_t` hash table and CRC checksum
array; the function was hardened in place rather than replaced.

`tools/iw3_android/prepare_real_engine_iwd_mount.py` stages the original
`FS_LoadZipFile` function body verbatim with only an include adapter.
`android/iw3-native/CMakeLists.txt` now compiles that translation unit into
an isolated static archive, `iw3_sp_iwd_mount`, for both host and Android
ABIs. The archive intentionally retains unresolved allocator/checksum
services and is **not linked into the JNI APK**. This gate proves the actual
function's C++/ABI compatibility only; it does not yet mount an IWD or prove
an asset lookup. The parser's generated test ZIP is still only a fixture.

The regression suite verifies exact function-body preservation, source
non-mutation, native-width allocation guards, null-allocation cleanup, and the
explicit not-a-game/not-mounted status. The ARM64 source-module gate completed
successfully in [run 40247789995](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247789995):
27 Python tests passed; CTest passed 8/8; ASAN/UBSAN/leak checks passed; the
original `FS_LoadZipFile(char*, char*)` symbol was found in
`libiw3_sp_iwd_mount.a` built with the Android NDK AArch64 toolchain; and the
original frame ABI object passed the ELF64/AArch64 checks. The artifact
[12619201727](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247789995/artifacts/12619201727)
contains the static module and source provenance reports. The archive is
explicitly **not linked into the JNI APK**. The Android ARM64 JNI build also
completed successfully in [run 40247741699](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247741699),
including APK signature, AArch64 ELF, JNI symbol and package checks; artifact
[12619771079](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247741699/artifacts/12619771079)
is the diagnostic-only package and provenance bundle. The separate x86_64 emulator runtime probe then completed successfully in
[run 40247741674](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247741674):
the Android Activity/JNI ran the original ZIP32 stored/deflate parser,
sandboxed file operations, original IWD-name functions, touch DOWN/UP
readback, the native usercmd adapter, and pause/resume. Its proof report
explicitly records `arm64_device_execution_proven: false` and
`gameplay_proven: false`. Artifact
[12619940202](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40247741674/artifacts/12619940202)
contains the runtime log/proof. Neither success proves a real map, renderer,
client/gameplay linkage, or physical ARM64 execution.

Remaining gates are unchanged: wire the module to the actual engine allocator,
checksum/string services and Android file-searchpath startup; mount a real
user-supplied IWD and verify an original asset lookup; then integrate FastFiles,
map loading, the original renderer, real client commands, and gameplay. Keep
PR #4 open and unmerged.


## Offline SP combat probe: bounded aim at an existing actor

The current Windows-only disposable SP diagnostic reaches the original
`FireWeapon` and `Bullet_Fire` callbacks, but the last evidence did not reach
`G_Damage` for an actor. The input probe now directs its finite test-only
attack commands toward the nearest already-existing live damageable actor
from the original SP `g_entities` list. It does not spawn an actor, relocate
entities, invoke weapon/damage callbacks directly, or modify the vendored game
source. Aim is capped at the same 12 generated attack commands. The runtime
report separately records `test_aimed_at_existing_actor`, actual actor damage,
and actor death; aiming or bullet dispatch alone never counts as a hit.

The workflow now runs when this input-probe script, its test, or the runtime
probe changes. This remains a Windows SP diagnostic only; it does not prove
Android client linkage, graphics, map rendering, ARM64-device execution, or a
playable Android APK. The next CI result must determine whether real traces
actually hit the existing actor; if not, preserve that failure as a blocker.

## Offline SP combat probe compile regression (2026-10-26)

The first bounded-aim runtime workflow after adding the target-selection hook failed at
the **Windows-only disposable source build**, not in Android. Compiler errors
C2065 reported `level` and `g_entities` were undeclared in the
temporarily instrumented `client/cl_input.cpp`. That translation unit includes
`game/g_local.h`, but that header does not expose the shared level/entity
globals declared by `game/g_level.h`.

Fixed the disposable instrumentation generator to add the explicit
`#include <game/g_level.h>` to its temporary copy before compiling the
test-only actor-aim code. The checked-in KisakCOD source remains untouched by
the probe. Added a regression assertion that the generated copy includes this
declaration header; the existing test still compares the vendored input source
before/after and rejects modifying it.

Failure evidence: [offline SP runtime run 40250674916](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40250674916),
job log showed C2065 at the injected `level` / `g_entities` references.
Fix commits: [0febe32](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/0febe32faa1957fe2eaaeb270cb63bca7ed538a3)
and [20fac77](https://github.com/1993velezpadilla-source/ZOMBIES-2026/commit/20fac77c4059caaea6fb46b1968639e18a306e3f).
CI for the fix must pass the Windows SP build before any runtime hit/damage
result can be interpreted. This is a test-harness compile fix only; it is not
Android engine linkage, not an IWD mount, and not evidence of playable gameplay.


## Offline SP aim probe: compensate snapshot delta angles (2026-10-26)

The completed Windows SP runtime probe now builds and runs, but its latest evidence
still reports `weapon_fired_verified: true` and
`aimed_weapon_damage_verified: false`. The original `FireWeapon` and
`Bullet_Fire` callbacks ran, and the test aimed at an existing actor; neither
fact proves that the authoritative shot intersected that actor. The run's
metadata-only report is [40257038556](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40257038556),
artifact [12623062805](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40257038556/artifacts/12623062805).

A source review found a concrete input-probe error: the disposable
`CL_CreateCmd` hook wrote world-space target angles directly into the client's
command-space `viewangles`. `CL_FinishMove` packs those angles into the
usercmd, while the server reconstructs the authoritative view by adding the
snapshot's `delta_angles`. The probe therefore could systematically miss even
when its target-angle calculation was correct.

The disposable probe now subtracts each snapshot `delta_angles` component
from the desired world-space pitch/yaw/roll before `CL_FinishMove` packs the
command. A regression test requires all three compensations. This change is
confined to the temporary Windows-only diagnostic copy; vendored KisakCOD
gameplay source remains untouched. The next runtime CI result must show whether
this removes the aim offset. Damage/death remain unverified until the report
observes the original `G_Damage` callback on an actor.

This is not Android client linkage, not a map-rendering milestone, and not a
playable APK. The IWD indexer remains a separate static module with unresolved
allocator/checksum services; the native Android library still does not mount
real IWD searchpaths, load FastFiles/maps, or run the original client/game loop.
Keep PR #4 open and unmerged.


## Original IWD loader: bounds-safe extension trimming (2026-10-26)

A source-level audit of the genuine `FS_LoadZipFile` found an out-of-bounds
path expression in the vendored engine:
`iwdFilename[strlen(iwdBasename) + 252]`. Since `iwdFilename` is a 256-byte
array and normal archive basenames such as `pak0.iwd` are longer than four
characters, that index can exceed the field boundary. The expression could
read unrelated fields and could write outside the filename buffer when the
extension comparison happened to match.

The original function now computes the copied full-path length, checks that at
least four characters are present, compares the suffix at
`iwdFilename + filenameLength - 4`, and truncates at that same checked index.
The archive parser, hash-table builder, checksum collection, and returned
`iwd_t` remain the original engine implementation; only the unsafe extension
offset was corrected. The staging generator requires the new bounds-safe
markers and rejects the old expression, and the source regression checks both
conditions.

Changes are in [`com_files.cpp`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/blob/feature/iw3-native-android-arm64-20261025/third_party/KisakCOD/src/universal/com_files.cpp),
[`prepare_real_engine_iwd_mount.py`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/blob/feature/iw3-native-android-arm64-20261025/tools/iw3_android/prepare_real_engine_iwd_mount.py),
and [`test_iw3_android_source.py`](https://github.com/1993velezpadilla-source/ZOMBIES-2026/blob/feature/iw3-native-android-arm64-20261025/tests/test_iw3_android_source.py).
The CI runs triggered by these changes must still confirm compilation and
regression success before this fix is considered validated.

This removes a concrete memory-safety blocker from the original IWD loader,
but does **not** yet prove that `FS_LoadZipFile` is linked into the Android
JNI library or that an IWD is mounted into the engine's live searchpath list.
FastFiles/maps, renderer, real client input consumption, and ARM64 gameplay
remain unverified. Keep PR #4 open and unmerged.


## Offline SP fire probe: distinguish client hook from server weapon state (2026-10-26)

The latest source-built Windows SP runtime (run 40267449933, commit
`4656362`) built and launched the authentic Single-Player executable; it
kept the process alive at 40 seconds, ran the original frame and actor AI, and
confirmed the test loadout was granted/equipped. But the report had
`test_client_attack_button_injected=false`, `test_aimed_at_existing_actor=false`,
and an empty `input_trace`. Thus the prior 120-command warm-up did not start:
the condition depended on `clients[0].snap.ps.weapon`, which stayed empty even
though the live server playerState had a weapon. The previous pass therefore
did not test a real shot.

The disposable `CL_CreateCmd` probe now logs `TEST_CL_CREATECMD_REACHED`
on its first invocation, separately logs when
`g_entities[0].client->ps.weapon` confirms the server-side weapon, waits 120
client commands, then injects at most 12 attack usercmds through the normal
client command path. The aim code uses the same live playerState's
`delta_angles`, rather than relying on a possibly empty snapshot. The runtime
report distinguishes hook entry, server weapon readiness, warm-up completion,
button injection, aim, real `FireWeapon`/`Bullet_Fire` callbacks, damage,
and death. No combat callback is called directly and no actor is created or
moved by this probe.

This correction is still test instrumentation, not an Android gameplay
milestone. The next Windows runtime must first show the hook/weapon/warm-up
markers; then it must show the original weapon callbacks before any damage
claim is valid. The Android target still does not link the original IWD mount
module or run the client/frame/render/map stack. Keep PR #4 open and unmerged.


## IWD central-directory name integrity — 26 Oct 2026

The original `FS_LoadZipFile()` now rejects empty ZIP entry names and names
whose C-string length differs from the central-directory `size_filename`.
That difference indicates an embedded NUL: without this guard, the indexer
could size one archive name but hash/copy only its prefix, making a different
ZIP entry appear under the truncated engine path. The check runs in both the
initial allocation-sizing pass and the second hash-index construction pass,
so the two passes cannot disagree about accepted names.

The source-staging gate requires this exact guard and the source regression
checks that it appears twice and precedes both name-buffer sizing and CRC /
hash-index insertion. This is a correctness hardening change to the authentic
KisakCOD IWD indexer; it does **not** mount a real game IWD in the Android
searchpath, load FastFiles/maps, or establish gameplay. CI must pass on the
resulting commit before this source-level guard is considered verified.

## Phase F — execute the original IWD indexer in the Android JNI diagnostic (26 Oct 2026)

The next concrete portability blocker was not another parser-only test: the exact `FS_LoadZipFile()` body existed in an ARM64 static audit archive but was not linked to the Android JNI library, because its original string, allocation, zeroing and checksum services were unresolved.

This pass adds `tools/iw3_android/prepare_real_engine_iwd_services.py`. It extracts the original KisakCOD bodies for `I_strncpyz`, `I_stricmp`, `I_strnicmp`, `I_strlwr`, `I_isupper`, `_copyDWord`, `Com_Memset`, `Z_TryMallocGarbage`, `Z_TryMalloc`, `Z_Malloc`, `Z_Free`, and `Com_BlockChecksumKey32` from their original translation units. The staged translation unit uses a standard `assert` adapter for the isolated string-helper assertions; it does not invent an allocator or checksum algorithm. The original `fs_iwdFileCount` and `fs_checksumFeed` globals are emitted as the state used by the authentic indexer.

CMake and the Android Gradle arguments now include both the verbatim `FS_LoadZipFile()` body and these services in `libiw3_sp_math.so`. The separate `libiw3_sp_iwd_mount.a` remains available as a source/ABI audit artifact; it is not mistaken for a game.

The Android native smoke extends the existing generated ZIP fixture to call the original `FS_LoadZipFile()`, then checks the returned `iwd_t`, entry count, lowercase member names, hash-bucket membership, filename-extension handling, and checksum/pure-checksum consistency. It closes the original ZIP handle and releases the original index allocations before deleting the fixture. A distinct `IW3_JNI_IWD_MOUNT_PASS` marker is required by the emulator evidence validator.

**Verified evidence for this pass (26 Oct 2026):**

- [Native/ARM64 workflow #205](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873913) succeeded. The host suite passed 8/8 in Release and 8/8 under ASAN/UBSAN; the ARM64 outputs were verified as ELF64/AArch64, and the original `FS_LoadZipFile(char*, char*)` symbol was present in the ARM64 audit archive.
- [Android JNI build #169](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873914) succeeded and signed the diagnostic APK.
- [Android emulator runtime #153](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873921) succeeded on an **x86_64 emulator**, not an ARM64 device. Its log contains `IW3_JNI_UNZIP_PARSER_PASS`, `IW3_JNI_IWD_MOUNT_PASS`, and touch DOWN/UP readback where `usercmd_s` attack transitions 0 → 1 → 0. The evidence validator reported `original_fs_loadzipfile_indexed_fixture_executed: true`, while `arm64_device_execution_proven` and `gameplay_proven` remained false.

Artifacts: [ARM64 native modules — NOT an APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873913/artifacts/12631614602); [signed JNI diagnostic APK — NOT the game](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873914/artifacts/12631584994); [Android emulator runtime log — NOT the game](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40280873921/artifacts/12632118691).

This is runtime evidence for the original IWD index builder on a generated fixture, **not** mounting a licensed game IWD into `fs_searchpaths`. It does not load FastFiles or a BSP/map, render the game scene, link the original SP frame services, or prove weapons/actors/gameplay. The APK remains diagnostic only.

**Next portability blocker:** integrate the original `FS_AddIwdFilesForGameDirectory()` and `FS_AddSearchPath()` with the Android directory enumerator and the real `fs_searchpaths` state. That is required before claiming an original IWD is mounted for game asset lookup; FastFiles, map loading, renderer and gameplay remain later blockers.


## Phase G — original searchpath insertion on Android diagnostic (26 Oct 2026)

This pass integrates the original \`FS_AddSearchPath()\` body into the native
diagnostic target and calls it with the \`iwd_t\` produced by original
\`FS_LoadZipFile()\` on the generated ZIP/IWD fixture. The smoke verifies that
the returned \`searchpath_s\` node is linked into \`fs_searchpaths\`, points at
that indexed IWD, and is unlinked before the test frees the archive/index
allocations.

A 64-bit portability issue in the original list traversal was corrected in
\`third_party/KisakCOD/src/universal/com_files.cpp\`: the decompiled cast
\`pSearch = (searchpath_s **)*pSearch\` is now
\`pSearch = &(*pSearch)->next\`. Localized/nonlocalized insertion order remains
unchanged. The staging gate extracts the original function from the vendored
source and rejects the unsafe cast. CI must prove the source tests, host
sanitizers, Android link and emulator marker before this pass is verified.

This still mounts only a generated fixture, not a licensed game IWD discovered
from the actual game directory. The full \`FS_AddIwdFilesForGameDirectory()\`
scan, real asset lookup through \`FS_OpenFile\`, FastFiles/maps, renderer,
client frame loop, physical ARM64 execution and gameplay remain unproven.
The diagnostic APK is not a playable game; keep PR #4 open and unmerged.

## Latest verified IWD directory-scan execution — 26 Oct 2026

Commit `0ac0182617c1b51aafe540b91f1e04cdba0e5aae` advances the archive path from “scanner source staged” to executing the **original** `FS_AddIwdFilesForGameDirectory()` against an isolated generated `.iwd` fixture.

The diagnostic creates a temporary directory below the app-private data root, writes one ZIP32 fixture there, and calls the vendored directory scanner with the real root/game-folder path. The original scanner then goes through the rooted `Sys_ListFiles` platform boundary, its native-width sort and filename/language handling, original `FS_LoadZipFile()`, and original `FS_AddSearchPath()`. The test checks the inserted list node, basename/game-folder fields, entry count, hash buckets and checksums, then restores global search-path/checksum counters and closes/frees the fixture-owned objects.

A separate CI configuration defect was fixed in the same pass: the ARM64 CMake invocation had omitted `IW3_EXTRACTED_IWD_DIRECTORY`, so CMake stopped before compiling the module. The ARM64 workflow now passes the generated original scanner source and archives its provenance report.

**Verified evidence on this commit:**

- [Native/ARM64 workflow 40300544114](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544114) — SUCCESS. Host Release CTest **8/8**, ASAN/UBSAN CTest **8/8**, NDK output validated as ELF64/AArch64, full original `G_RunFrame` and original IWD indexer compiled as separate native modules. The frame still has nine unresolved gameplay services and is not linked into a running game.
- [ARM64 JNI package workflow 40300544062](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544062) — SUCCESS. Signed ARM64 diagnostic APK with the native components; **not a playable game**.
- [Android emulator runtime 40300544065](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544065) — SUCCESS on **Android x86_64 emulator**, not an ARM64 device. Logcat confirms `IW3_JNI_IWD_MOUNT_PASS`, `IW3_JNI_IWD_SEARCHPATH_PASS`, `IW3_JNI_IWD_DIRECTORY_SCAN_PASS`, native touch DOWN/UP, and attack-bit readback through the diagnostic `usercmd_s` adapter. The evidence validator explicitly returns `arm64_device_execution_proven=false` and `gameplay_proven=false`.

Artifacts are labelled honestly: [ARM64 module archive — NOT APK](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544114/artifacts/12640057787), [signed JNI diagnostic APK — NOT GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544062/artifacts/12639219830), and [Android x86_64 runtime log — NOT GAME](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40300544065/artifacts/12639324934).

**Limit remains strict:** the test indexes only its generated fixture; it does not mount licensed/original game IWD packages into a complete game session. FastFiles/maps, original renderer output, touch consumption by the real `CL_CreateCmd`/player simulation, weapons/actors in an Android game frame, and physical ARM64 gameplay remain unproven. No playable IW3 APK is claimed. Keep PR #4 open and unmerged.


## Original FS_AddGameDirectory Android integration pass — 26 Oct 2026

The latest code pass stages and calls the vendored KisakCOD `FS_AddGameDirectory(path, dir, 0, 0)` function, not just its child `FS_AddIwdFilesForGameDirectory`. The fixture test now verifies the resulting searchpath order: the indexed IWD node precedes the original directory node, which precedes the pre-existing searchpath list. It checks the original `directory_t` path/game-folder fields and `fs_gamedir`, then restores globals and frees the fixture-owned IWD/directory/searchpath allocations.

Platform prerequisites added for this original path:
- A rooted `z2026_platform_directory_has_contents()` implementation for the original `Sys_DirectoryHasContents` boundary. It rejects paths outside the retained app-data root and symlink traversal; an unreadable directory fails closed.
- An adapter for the original `Com_sprintf` signature using bounded `vsnprintf`.
- An assertion adapter for the otherwise unreachable invalid-language assertion path; it aborts rather than silently suppressing an engine assertion.
- Regression coverage for empty/non-empty/missing and symlinked directories, source-preservation of the original `FS_AddGameDirectory`, searchpath-chain layout, and the new explicit `IW3_JNI_IWD_GAME_DIRECTORY_PASS` marker.

The first JNI CI attempt at commit `4a2e3fd` failed in a Python source test because it still expected the old direct call to `FS_AddIwdFilesForGameDirectory`. Commit `379a719` corrected that stale expectation. JNI build run `40308239783` **passed** source generation, Gradle ARM64 compilation, ELF64/AArch64 checks, required JNI symbols, APK integrity and signing; [artifact 12644005107](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40308239783/artifacts/12644005107) is explicitly **DIAGNOSTIC NOT GAME**. The latest JNI rerun `40308839955` on commit `6c8a2f2` also **passed**, including the regression that forbids the stale TextView title selector; its diagnostic artifact is [12644420097](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40308839955/artifacts/12644420097), again **NOT A GAME**.

Native ARM64 run `40308839914` also **passed**: host CTest **8/8** in Release and **8/8** under ASAN/UBSAN; the original `FS_LoadZipFile` symbol was present in an AArch64 static archive; the full original `G_RunFrame` compiled against real ARM64 state headers. The report still lists nine unresolved gameplay services and explicitly says the frame is not linked to a working runtime. [Artifact 12643159590](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40308839914/artifacts/12643159590) is a native module archive, **NOT APK**.

The first updated emulator run `40308239790` reached and logged `IW3_JNI_IWD_GAME_DIRECTORY_PASS`, but failed later because the UI automation searched for an obsolete TextView title. The selector was fixed in `34d7036` and guarded by a regression in `6c8a2f2`. Rerun `40308840330` **passed**: logcat shows `IW3_JNI_IWD_GAME_DIRECTORY_PASS` and `IW3_JNI_USERCMD attack=1 buttons=1`; the evidence validator confirms touch DOWN/UP, the attack bit reaching the original IW3 `usercmd_s` layout, and pause/resume. [Artifact 12642639749](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40308840330/artifacts/12642639749) contains the emulator log/screenshots and is explicitly **NOT GAME**. The validator still reports `arm64_device_execution_proven=false` and `gameplay_proven=false`: this is an x86_64 emulator exercising the filesystem/input diagnostic, not an ARM64 device or playable game.

**Scope remains diagnostic:** this exercises a generated ZIP32 fixture in the original searchpath structures. It does not mount licensed/original game assets, resolve real map/fastfile resources, render the game, or run player/weapon/actor gameplay. Physical ARM64 device gameplay and a playable APK remain unproven; keep PR #4 open and unmerged.
## Phase H — original searchpath lookup branch (26 Oct 2026)

This pass moves the Android file-system work one step beyond registering a generated IWD fixture: it extracts the authentic lookup-only prefix of FS_FOpenFileReadForThread() from third_party/KisakCOD/src/universal/com_files.cpp, ending immediately before the original FS_HandleForFile(thread) handle-allocation path.

The staged prefix preserves the original filename sanitizer, FS_UseSearchPath(), FS_HashFileName(), FS_FilenameCompare() hash-chain walk, and directory fallback. Its smoke runs while the real original FS_AddGameDirectory() fixture searchpaths are installed and checks three outcomes: an existing IWD member returns found, a missing member returns not found after the directory fallback, and a ../ traversal name is rejected by the original sanitizer. The fallback file boundary is mapped to a rooted Android adapter using z2026_platform_open_engine_path_fd(); the adapter does not allow unrestricted absolute paths or symlink traversal.

The first compile attempt exposed a real header-boundary mismatch: this source snapshot declares FS_FileClose(iobuf*) in com_files.h, while the original lookup branch uses its FILE* file-access boundary. The generated lookup translation unit now maps those two original call sites to explicitly named rooted FILE* adapters, avoiding a conflicting declaration and preserving the extracted source text. The first source-test attempt also found that FS_SanitizeFilename and FS_UseSearchPath have both prototypes and definitions; the staging generator now selects the single definition before running the brace parser.

The native smoke, JNI report, emulator evidence validator and regression tests now require IW3_JNI_IWD_LOOKUP_PASS. The evidence schema explicitly keeps original_fs_read_handle_path_executed: false.

Scope limit: this is only the original lookup branch, not the complete public FS_FOpenFileReadForThread() implementation. It does not allocate an engine file handle, execute the original FS_Read(), mount licensed game assets, load FastFiles/maps, render a game scene or prove gameplay. It is not a playable APK. The post-adapter CI runs on the current head must finish before this pass is called green; see the branch Actions runs for native host/ASAN, ARM64 compilation, JNI package and x86_64 emulator evidence.

### Phase H follow-up — original absolute path semantics

Inspection of the authentic FS_BuildOSPathForThread() and FS_ReplaceSeparators() bodies revealed an additional portability defect: they convert the leading slash of a POSIX filesDir path into a leading backslash. The previous rooted adapter only recognized paths beginning with '/', so a directory fallback could falsely report a disk resource missing.

The Android path normalizer now converts backslashes before its absolute-path/root-boundary check. A new native regression verifies that a leading-backslash absolute path beneath the configured data root opens successfully, while a leading-backslash /etc/passwd path is rejected. The JNI smoke also creates a real file under the registered game directory and requires the original lookup branch to find it through the directory fallback, in addition to an IWD-member hit, an absent-file miss, and traversal rejection.

The current-head native workflow has passed the host compile/CTest stage and the ASAN/UBSAN stage, then advanced to Android NDK setup. The ARM64 ELF build, JNI packaging, and x86_64 emulator execution are still running; do not treat those as green until their run conclusions and runtime evidence are available. This is still a lookup-only test, not FS_Read or a playable APK.

### Phase H validation results — 26 Oct 2026

The path-normalization and disk-fallback test revision (code commit a9c820295111b24a7d7672672bada2d19f9d727b) completed its relevant CI gates:

- Native ARM64 workflow 40315452085: Release CTest passed 8/8; ASAN/UBSAN CTest passed 8/8; the output ELF was verified as ELF64/AArch64; FS_LoadZipFile(char*, char*) was present in the ARM64 static archive. The original G_RunFrame() also compiled with real ARM64 engine state headers, but its evidence still lists nine unresolved gameplay services and explicitly says frame execution/gameplay are not proven. Artifact 12647235802 is a native module bundle, not an APK.
- JNI integration workflow 40315452368: passed the ARM64 JNI link/package/signature gate and emitted ORIGINAL_IW3_ANDROID_JNI_DIAGNOSTIC_APK_BUILT. Artifact 12647240759 is explicitly diagnostic, not a playable game.
- Android emulator runtime workflow 40315451991: passed and emitted IW3_JNI_IWD_LOOKUP_PASS. The evidence validator reports original_fs_fopenfileread_searchpath_lookup_branch_executed=true, original_fs_read_handle_path_executed=false, arm64_device_execution_proven=false, and gameplay_proven=false. Artifact 12645814971 contains the x86_64 emulator log and evidence, not a game APK.

This proves the original lookup-only branch can find an IWD member, find a real file through the directory searchpath fallback, reject a missing file and reject traversal input in the Android diagnostic process. It does not prove that a licensed game IWD/FastFile/map is mounted or that the original FS_Read handle lifecycle is integrated. PR #4 remains intentionally unmerged.


### Phase I — preserve reopenable IWD archive paths (26 Oct 2026)

A review of the original `FS_FOpenFileReadForThread()` and `unzReOpen()` uncovered a portability regression in the earlier path hardening: `FS_LoadZipFile()` removed the final `.iwd` from `iwd->iwdFilename`, but the original `unzReOpen(path, handle)` passes that stored path directly to `ZIP_fopen(path)`. Indexing could therefore succeed while the later cloned-handle open failed because it tried to open a path without the archive extension.

The fix keeps the complete, already length-validated path (including `.iwd`) in the original `iwd_t` field. The JNI IWD fixture now checks that the stored name exactly matches the archive path, calls original `unzReOpen(iwd->iwdFilename, iwd->handle)`, seeks to the indexed first entry, opens it and verifies the exact payload before closing the cloned archive. The mount smoke fails if clone reopen or payload verification fails. Source regressions were updated to reject the old extension-trimming behavior.

This is a concrete prerequisite for the original file-handle path, not yet the complete `FS_FOpenFileReadForThread` / `FS_Read` lifecycle. The generated lookup bridge still stops before handle allocation, and the diagnostic still uses a synthetic IWD fixture rather than licensed game assets. Validation for this correction is running through the existing native ARM64, JNI packaging and Android emulator workflows; do not call it green until their new run conclusions and logs are inspected. The emulator gate is x86_64 diagnostic-only, not ARM64 device gameplay. No playable APK is available, and PR #4 must remain unmerged.


#### Phase I CI update — 26 Oct 2026

The source regression and generator contract were corrected after the first native gate exposed stale expectations for the removed extension-trimming behavior. On head `449ea041608d6f64757abc3c238574d70522539e`:

- Preflight `40317221172`: **PASS**.
- Native ARM64 workflow `40317213185`: **PASS**. Source/provenance checks, host build/tests, sanitizer build/tests, Android NDK setup, ARM64 ELF link, original frame compile, IWD archive compile/symbol audit and artifact upload all completed successfully. Artifact `12647606725` is a native-module bundle, explicitly **not an APK**.
- JNI Android integration `40317213202`: still running at this checkpoint.
- Android emulator runtime `40317213167`: still running at this checkpoint; this gate uses Android x86_64 and cannot prove physical ARM64 execution.
- Windows SP build/runtime regression checks `40317221188` and `40317221216`: still running at this checkpoint.

Thus the corrected source and native ARM64 module compile are verified, but the new cloned-IWD reopen/read smoke has not yet received its final Android runtime result. The original file-handle allocation plus `FS_Read` lifecycle remains unported, as do FastFiles/maps, renderer integration and real gameplay. There is still no playable APK; keep PR #4 unmerged.

### Phase I follow-up — Android directory adapter escape correction (26 Oct 2026)

Inspection of the completed Android emulator job for head `449ea041608d6f64757abc3c238574d70522539e` showed three Clang `-Wmultichar` warnings in `android/iw3-native/iw3_android_iwd_directory_io.cpp`: the `Com_sprintf` terminators were written as multi-character literals `'\\\\0'`, and the assertion adapter used `'\\\\n'`. Those are not the C++ NUL/newline escapes; they can truncate to an ordinary character (the previous build specifically warned that the literal value 23600 converted to character '0').

Commit `4097f4e9d62778f18c2aa92ebec8cfbd12271054` corrects these to `'\\0'` and `'\\n'`. New regression tests in `tests/test_iw3_android_directory_adapter.py` require the intended literals and reject the doubled-backslash forms. The follow-up is wired into the existing `test_iw3_android_*.py` workflow discovery; CI for the new commits must still finish before this correction is called green.

The latest completed runtime evidence on the prior code is Android x86_64 diagnostic run [40317213167](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40317213167): original ZIP parser, IWD index, searchpath insertion, directory scan, game-directory registration and lookup-only branch passed; native touch DOWN/UP reached the original `usercmd_s`. The evidence explicitly records `original_fs_read_handle_path_executed=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. Its smoke directly calls original `unzReOpen`/ZIP-member read; it does not exercise the engine's `FS_FOpenFileReadForThread` handle allocation plus `FS_Read`/close lifecycle. That is the next file-I/O gate.

No game map, renderer, full client/server frame linkage or playable APK has been proven. The generated IWD remains a synthetic fixture, the emulator is x86_64, and PR #4 remains intentionally unmerged.



### Phase J — wire original file-read lifecycle source audit into ARM64 JNI CI (26 Oct 2026)

The latest branch head `cae083c` passed the Android x86_64 JNI runtime diagnostic, including the original ZIP32 parser, IWD indexing, searchpath insertion, game-directory registration, lookup-only branch, native touch DOWN/UP readback, and Activity pause/resume. Its evidence still explicitly records `original_fs_read_handle_path_executed=false`, `arm64_device_execution_proven=false`, and `gameplay_proven=false`. This is diagnostic evidence only.

A prior JNI integration run failed its source-test step because the newly added `prepare_real_engine_iwd_read.py` staging gate was present in the emulator workflow but absent from the separate ARM64 JNI integration workflow. The ARM64 workflow now runs the same generator, writes `iw3-original-iwd-read-lifecycle.json`, and archives that report alongside the diagnostic APK and provenance. A regression test requires the workflow to label this output `STAGED_NOT_LINKED` and rejects any claim that the original read-handle path is already executing.

This is a CI/provenance correction, not a runtime port of `FS_HandleForFile`, `FS_FOpenFileReadForThread`, `FS_Read`, or `FS_FCloseFile`. The extracted translation unit remains an audit artifact and is not linked into the APK. The next actual engine task remains resolving the native ABI/global/service dependencies and exercising the original handle allocation/read/close path against the registered IWD fixture. FastFiles/maps, renderer, complete frame/service linkage, physical ARM64 execution, and playable gameplay remain open. Keep PR #4 unmerged.


### Phase J follow-up — carry the original read-lifecycle audit through all Android gates (26 Oct 2026)

The source-only audit for `FS_HandleForFile`, `FS_FOpenFileReadForThread`, `FS_Read`, and `FS_FCloseFile` is now generated and archived by the emulator diagnostic, the ARM64 JNI package gate, and the native ARM64 module workflow. Regression tests require each workflow to run `prepare_real_engine_iwd_read.py` and retain `iw3-original-iwd-read-lifecycle.json`. Each workflow labels it `STAGED_NOT_LINKED` so the evidence cannot be mistaken for runtime execution.

This closes a CI coverage gap: a previous ARM64 JNI integration run failed because the lifecycle generator was not invoked by that workflow, even though the emulator workflow had the staging step. The staging source is now consistently audited on the AArch64 build gate as well. The report intentionally keeps `android_abi_and_service_linkage_proven=false`, `runtime_handle_path_executed=false`, and `playable_apk=false`. No original file-handle lifecycle is yet linked into the JNI runtime. Next work remains the actual native ABI/service integration and runtime test against the registered IWD fixture, followed by real FastFiles/map loading and renderer/gameplay integration.


## 2026-10-26 — compile-time ABI gate for the original FS_Read body

The previous pass only staged the upstream `FS_Read` body and recorded its
source hash; it did not compile that function. This pass adds a separate
`iw3_sp_fs_read` static archive built by the host, Android ARM64, and Android
emulator configurations. The `FS_FileForHandle` and `FS_Read` bodies are extracted verbatim from
`third_party/KisakCOD/src/universal/com_files.cpp`; the existing original
lookup module already supplies `FS_CheckFileSystemStarted`. Compile-time
assertions check the native 64-bit `fileHandleData_t` layout (`sizeof == 304`,
`zipFile` offset 32, and `name` offset 44).

The separate archive is an ABI/dependency audit and is not linked into
`libiw3_sp_math.so`. The same verbatim helper/read source is also compiled
directly into the diagnostic JNI library together with
`iw3_android_fs_read_io.cpp`, which provides a zero-initialized native-width
`fileHandleData_t fsh[65]` table for the isolated IWD fixture. The runtime
now executes the original `FS_Read` ZIP branch against a reopened IWD entry
while an authentic `FS_AddSearchPath` node is present; the bytes returned by
`unzReadCurrentFile` are compared with the fixture payload. The ARM64 archive
audit still exposes unresolved `fsh`, because the original `fsh[65]` is
file-local static inside upstream `com_files.cpp`. The diagnostic table is
not the original full filesystem table, and the original
`FS_FOpenFileReadForThread -> FS_Read -> FS_FCloseFile` handle lifecycle is
still not integrated. No fake read routine is used, and no gameplay claim is
made.

The preceding runtime gate on commit `95aae9c` passed on Android x86_64 for
the ZIP/IWD fixture and touch adapter only. It explicitly does not prove ARM64
device execution, FastFiles/maps, rendering, or gameplay. After this read-branch gate, the next real integration step is to port the
owning original filesystem translation unit or a genuine handle-table accessor,
then exercise the complete `FS_FOpenFileReadForThread -> FS_Read ->
FS_FCloseFile` lifecycle against an IWD entry.
The playable-APK gate remains closed.


### Phase K — original file-handle close uses the native record size (26 Oct 2026)

Review of the authentic FS_FCloseFile() body found a 32-bit portability assumption: it cleared exactly 284 bytes, which is the Win32 fileHandleData_t size, while the current 64-bit ABI overlay asserts a 304-byte record. On ARM64, that left the final 20 bytes of the record uncleared. The original close routine now clears sizeof(fsh[h]); on Win32 this remains 284 bytes, while 64-bit builds clear the complete native record.

The same exact FS_FCloseFile() body is now extracted by prepare_real_engine_fs_read.py and compiled in the existing native/ARM64 audit archive and JNI diagnostic library. The only boundary adaptation maps the original FS_FileClose(FILE*) call to a POSIX fclose wrapper; ZIP close behavior remains in the original function.

The Android IWD fixture now routes the cloned ZIP handle through original FS_Read() and then original FS_FCloseFile(), checking that the payload matches and that all sizeof(fileHandleData_t) bytes are zero after close. This exercises the original close path on the current native-width fixture table, not the full original open/handle-allocation lifecycle.

Current head before this pass, 599ddff, passed the three Android CI gates:
- [Native ARM64 build and ABI archives — 40349187895](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40349187895)
- [ARM64 JNI diagnostic package — 40349187705](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40349187705)
- [Android x86_64 emulator runtime — 40349187759](https://github.com/1993velezpadilla-source/ZOMBIES-2026/actions/runs/40349187759), whose log emitted IW3_JNI_IWD_FS_READ_PASS.

Those results verify the original ZIP-branch FS_Read() on a synthetic IWD fixture; they do not verify the full FS_FOpenFileReadForThread -> FS_Read -> FS_FCloseFile lifecycle, real game assets, FastFiles/maps, rendering, physical ARM64 execution or gameplay. Validation on head bdee1dfd2da8a38bb549e2cfa704991a3db6bbfa completed on 26 Oct 2026:

- Preflight 40351532999: PASS, including the new native-width close regression tests.
- Native ARM64 build 40351524350: PASS. The compiled AArch64 audit archive defines FS_FCloseFile(int); artifact 12663543782 is a native-module bundle, not an APK.
- JNI package 40351524380: PASS. Artifact 12663658623 is the signed diagnostic APK, not the game.
- Android emulator runtime 40351524407: PASS. Logcat emitted IW3_JNI_IWD_FS_READ_PASS; in this revision that result requires the authentic FS_Read ZIP branch to return the exact fixture payload, the authentic FS_FCloseFile path to close the cloned archive, and all bytes in the 304-byte native-width handle record to be zero. Artifact 12663418140 is an x86_64 emulator log/evidence bundle, not a game APK.
- Original Windows SP build 40351532826: PASS.
- Windows killhouse runtime 40351532859: the process remained alive at 40 seconds, the killhouse map was requested, a registered bullet weapon was equipped, and actor AI think executed. The evidence still reports actual weapon-fire, damage, pain and death callbacks as false; this is not proof of a complete combat loop. Artifact 12664166888 contains metadata evidence only.

The first ARM64 attempt (40351393823) failed at the new source-regression step because the generator did not yet require the native-size marker. The generator contract was corrected in bdee1df and the rerun above passed.

The next blocker is still the complete original FS_FOpenFileReadForThread -> handle allocation -> FS_Read -> FS_FCloseFile lifecycle using the engine-owned handle table, followed by real FastFiles/map loading, renderer output, touch consumption by CL_CreateCmd/player simulation, and observed ARM64 gameplay. The current fixture uses a generated IWD and an Android x86_64 emulator. No licensed game assets, real map render, physical ARM64 execution, or playable APK are proven. PR #4 remains intentionally open and unmerged.


### Phase L — execute the original IWD handle lifecycle in Android diagnostic (26 Oct 2026)

The previous runtime only invoked the original FS_Read ZIP branch after manually preparing a diagnostic handle record. This pass extends the linked source generated by `prepare_real_engine_fs_read.py` to include the exact upstream bodies for `FS_HandleForFile()`, `FS_FOpenFileReadForThread()`, `FS_Read()`, and `FS_FCloseFile()`, plus the original extension/purity helpers and `Com_GetExtensionSubString()`.

The Android fixture now registers an authentic `FS_AddSearchPath` node, opens the same indexed IWD member twice through the original public file-open routine, verifies that the first handle owns the original archive and the second uses the original `unzReOpen` clone path, reads both payloads with original `FS_Read`, and closes both with original `FS_FCloseFile`. The test requires both records to be fully zeroed and `iwd->hasOpenFile` to return to zero. The new log markers are `IW3_JNI_IWD_FS_OPEN_READ_CLOSE_PASS` and `IW3_JNI_IWD_FS_CLONE_PASS`; the runtime evidence validator requires them and now reports the original handle path as executed only when they appear.

Scope is deliberately bounded: the exact engine functions run against the same native-width `fileHandleData_t` type in an Android-owned diagnostic table, because the full upstream `com_files.cpp` translation unit still owns its separate file-local `static fsh[65]` and is not linked into this target. Small platform/service adapters cover rooted file access, native atomic compare-exchange, thread-state queries and disabled copy-file behavior. This proves the original per-handle IWD open/read/clone/close path in the diagnostic process; it does **not** prove the complete upstream filesystem runtime, licensed game assets, FastFiles/maps, rendering, physical ARM64 device execution or gameplay.

The updated Android source regression, ARM64 module build, JNI package and x86_64 emulator runtime gates must all finish on the new head before this pass is called validated. The static ABI archive remains separate from the diagnostic APK. The PR remains intentionally open and unmerged; no playable APK is claimed.


### Phase M — original directory fallback through open/read/close (26 Oct 2026; CI pending)

Building on Phase L, the Android diagnostic now also creates a normal file beneath the fixture game directory registered by the original `FS_AddGameDirectory()` path. While the original directory and IWD searchpaths are live, it calls the original `FS_FOpenFileReadForThread()` for that disk-only member, requires a non-ZIP `FILE*` handle, obtains the length through the original `FS_filelength()` body and the narrow `fseek/ftell` platform adapter, reads bytes through original `FS_Read()`, closes through original `FS_FCloseFile()`, and verifies the complete native-width handle record is zeroed.

The JNI report adds `IW3_JNI_FS_DIRECTORY_OPEN_READ_CLOSE_PASS`; the runtime evidence validator requires that marker before reporting `original_fs_directory_fallback_read_executed=true`. The host smoke also requires the directory fallback result and prints `IW3_ORIGINAL_FS_DIRECTORY_READ_HOST_GREEN`. This complements the IWD primary/clone test: both the ZIP path and the ordinary directory-file path now use the original public file-open, read and close bodies in the diagnostic.

The change is intentionally scoped to a synthetic fixture under the Android app-private data root. It does not mount licensed game files, load FastFiles or a map, initialize the real renderer/client/server, prove execution on physical ARM64 hardware, or prove gameplay. The native-width `fsh[65]` table remains diagnostic-owned; `original_upstream_fsh_table_integrated=false` is still required.

Implementation commits include `c619a35` (directory read probe), `e4b3a35` (JNI marker/report), `310e8d8` (runtime evidence gate), `d4338eb` (source regression), `d92d2c7` (workflow scope clarification), `1e238b0` (host smoke), and `cdba2de` (host failure diagnostics). The source preflight passed on the current code line and the JNI integration/package succeeded on commit `cdba2de`. The native host CTest also passed with both `iwd_fs_read_ok` and `iwd_fs_disk_read_ok` required, so the directory fallback has executed successfully on the host. The Android ARM64 module build and Android x86_64 emulator execution for this new disk fallback path are still pending. Do not treat the prior Phase L IWD lifecycle runtime as proof of this new disk fallback path.
