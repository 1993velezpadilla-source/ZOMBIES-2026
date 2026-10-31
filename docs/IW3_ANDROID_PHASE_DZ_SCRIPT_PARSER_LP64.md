# Android ARM64 pass DZ — original script-parser LP64 allocation safety

Date: 2026-10-30

## Starting point

Reviewed PR #4 at commit 287790770b64b09e9164f18465ba71af7b38419d and the current ARM64 source workflow. The original SP frame archive still has unresolved script scheduler services, including Scr_RunCurrentThreads() and Scr_IncTime(). The next portability prerequisite is the original script parser's runtime bookkeeping layout.

## Defect corrected

The original parser records in third_party/KisakCOD/src/script/scr_parser.h contain native pointers, but their assertions only accepted Win32 sizes:

- OpcodeLookup: 24 bytes on Win32, 32 bytes on LP64.
- SourceBufferInfo: 44 bytes on Win32, 56 bytes on LP64.
- SaveSourceBufferInfo: 8 bytes on Win32, 16 bytes on LP64.
- scrParserGlob_t: 0x34 on Win32, 0x50 on LP64.
- scrParserPub_t: 0x10 on Win32, 0x20 on LP64.

These are live parser/compiler bookkeeping records, not serialized FastFile records. The fields and order are unchanged. The header now asserts the expected size for both pointer widths.

The original TRACK_scr_parser() in scr_parser.cpp also passed literal sizes 52 and 16 to track_static_alloc_internal(). On LP64, those allocations are smaller than the actual globals. It now passes sizeof(scrParserGlob) and sizeof(scrParserPub), so the allocation tracker receives the native object sizes on both ABIs.

## Verification added

- tests/test_iw3_android_lp64_script_layouts.py checks both ABI sizes and prevents the hard-coded Win32 allocation lengths from returning.
- android/iw3-native/script_parser_layout_native_test.cpp includes the original header and asserts the concrete AArch64 sizes and pointer offsets.
- android/iw3-native/CMakeLists.txt builds that fixture as an Android-only OBJECT target, separate from JNI.
- .github/workflows/iw3-original-native-android.yml verifies ELF64/AArch64, the fixture anchor symbol, and archives the object and reports.

## Boundary

This fixes a real pointer-width allocation bug and verifies the original parser header layout. It does not compile or link the complete script VM, invoke Scr_RunCurrentThreads()/Scr_IncTime(), load FastFiles/maps, render a frame, or prove gameplay. The parser layout object is evidence, not a playable APK. Keep PR #4 open and unmerged until the authentic Android runtime and gameplay gates pass.
