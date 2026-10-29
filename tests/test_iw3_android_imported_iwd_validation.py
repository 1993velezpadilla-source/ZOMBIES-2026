"""Verify real original IWD indexing is wired to the Android data-import flow."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "android/iw3-native/iw3_unzip_native_smoke.cpp"
JNI = ROOT / "android/iw3-native/iw3_android_jni.cpp"
BRIDGE = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/EngineBridge.java"
ACTIVITY = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/MainActivity.java"
WORKFLOW = ROOT / ".github/workflows/iw3-original-android-jni.yml"
NATIVE_WORKFLOW = ROOT / ".github/workflows/iw3-original-native-android.yml"
MOUNT_SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
MOUNT_GENERATOR = ROOT / "tools/iw3_android/prepare_real_engine_iwd_mount.py"
EMULATOR = ROOT / "tools/iw3_android/run_emulator_probe.sh"


def function_body(source: str, signature: str) -> str:
    # Some C++ functions have a forward declaration before the definition.
    # Skip declarations whose semicolon appears before the next opening brace.
    start = source.index(signature)
    while True:
        opening = source.find("{", start)
        semicolon = source.find(";", start)
        if opening < 0:
            raise AssertionError(f"function body not found: {signature}")
        if semicolon < 0 or opening < semicolon:
            break
        start = source.find(signature, start + len(signature))
        if start < 0:
            raise AssertionError(f"function definition not found: {signature}")
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening + 1:index]
    raise AssertionError(f"unterminated function: {signature}")


class ImportedIwdValidationTests(unittest.TestCase):
    def test_real_indexer_uses_original_fs_loader_and_releases_archive_state(self):
        source = SMOKE.read_text(encoding="utf-8")
        body = function_body(source, "bool validate_original_iwd_index(")
        self.assertIn("FS_LoadZipFile(path_copy, basename_copy)", body)
        self.assertIn("iwd->buildBuffer", body)
        self.assertIn("iwd->hashTable", body)
        self.assertIn("unzClose(reinterpret_cast<unzFile>(iwd->handle))", body)
        self.assertIn("Z_Free(iwd->buildBuffer, 3)", body)
        self.assertIn("fs_iwdFileCount = old_count", body)
        self.assertIn("fs_checksumFeed = old_feed", body)
        self.assertIn("if (ok) ok = read_first_indexed_member_via_original_fs(iwd);", body)

    def test_imported_iwd_validation_reads_via_original_searchpath_and_handle_lifecycle(self):
        source = SMOKE.read_text(encoding="utf-8")
        body = function_body(source, "bool read_first_indexed_member_via_original_fs(")
        for marker in (
            "FS_AddSearchPath(search)",
            "FS_FOpenFileReadForThread(",
            "FS_Read(sample.data(), requested, handle)",
            "FS_FCloseFile(handle)",
            "fsh[handle].zipFile != iwd",
            "fs_searchpaths = previous_searchpaths",
            "iwd->hasOpenFile == 0",
        ):
            self.assertIn(marker, body)
        self.assertIn("IMPORTED_IWD_INDEX_AND_FS_READ_%s", JNI.read_text(encoding="utf-8"))
        self.assertIn("IW3_JNI_IMPORTED_IWD_INDEX_AND_FS_READ_%s", JNI.read_text(encoding="utf-8"))
        self.assertIn("IW3_PLAYABLE_APK=false", NATIVE_WORKFLOW.read_text(encoding="utf-8"))

    def test_original_loader_rejects_global_count_overflow_before_allocation(self):
        source = MOUNT_SOURCE.read_text(encoding="utf-8")
        body = function_body(source, "iwd_t *__cdecl FS_LoadZipFile(")
        guard = body.index("if (fs_iwdFileCount < 0 ||")
        allocation = body.index("buildBuffer = (fileInIwd_s*)Z_Malloc")
        self.assertLess(guard, allocation)
        self.assertIn(
            "gi.number_entry > static_cast<uint32_t>(INT_MAX - fs_iwdFileCount)",
            body,
        )

        smoke = SMOKE.read_text(encoding="utf-8")
        fixture = function_body(smoke, "bool run_imported_iwd_index_fixture(")
        self.assertIn("fs_iwdFileCount = INT_MAX;", fixture)
        self.assertIn("overflow_guard_ok", fixture)
        generator = MOUNT_GENERATOR.read_text(encoding="utf-8")
        self.assertIn("iwd_entry_count_overflow_rejected_before_allocation", generator)
        self.assertIn(
            "gi.number_entry > static_cast<uint32_t>(INT_MAX - fs_iwdFileCount)",
            generator,
        )

    def test_imported_scan_is_rooted_and_scans_main_and_zone_iwds(self):
        source = SMOKE.read_text(encoding="utf-8")
        body = function_body(source, "extern \"C\" IW3_UNZIP_EXPORT int z2026_iw3_validate_imported_iwds(")
        self.assertIn('const char *directories[] = {"main", "zone"}', body)
        self.assertIn("z2026_platform_set_data_root(root)", body)
        self.assertIn("z2026_platform_list_iwd_files", body)
        self.assertIn("validate_original_iwd_index(relative_path.c_str(), &entries)", body)
        self.assertIn("1000000 - entries", body)
        self.assertIn("no root-level IWD files", body)

    def test_emulator_fixture_exercises_original_iwd_indexer_without_gameplay_claims(self):
        source = SMOKE.read_text(encoding="utf-8")
        body = function_body(source, "bool run_imported_iwd_index_fixture(")
        self.assertIn("make_zip(archive_bytes, entries)", body)
        self.assertIn("z2026_iw3_validate_imported_iwds", body)
        self.assertIn("archives == 1 && indexed_entries == 2", body)
        self.assertIn("root_restored && fixture_root_removed", body)
        self.assertIn("IW3_PLAYABLE_APK=false", NATIVE_WORKFLOW.read_text(encoding="utf-8"))
        self.assertIn("return ok ? 1 : 0", source)

    def test_import_result_invokes_original_indexer_after_staging(self):
        activity = ACTIVITY.read_text(encoding="utf-8")
        bridge = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("GameDataImporter.importTree(this, treeUri, getFilesDir())", activity)
        self.assertIn("EngineBridge.nativeValidateImportedIwds(", activity)
        self.assertIn("Original FS/FastFile/map loading is still pending.", activity)
        self.assertIn("nativeValidateImportedIwds(String appPrivateRoot)", bridge)
        self.assertIn("does not initialize", bridge)
        self.assertIn("persistent game searchpath", bridge)
        self.assertIn("Original FS/FastFile/map loading is still pending.", activity)
        jni = JNI.read_text(encoding="utf-8")
        report_body = function_body(
            jni, "Java_org_z2026_iw3nativeprobe_EngineBridge_nativeReport(")
        self.assertLess(
            report_body.index("z2026_iw3_iwd_index_fixture_smoke(directory)"),
            report_body.index("ReleaseStringUTFChars(writableDirectory, directory)"))

    def test_ci_requires_jni_and_original_index_symbols_and_runtime_marker(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        emulator = EMULATOR.read_text(encoding="utf-8")
        self.assertIn("Java_org_z2026_iw3nativeprobe_EngineBridge_nativeValidateImportedIwds", workflow)
        self.assertIn("z2026_iw3_validate_imported_iwds", workflow)
        self.assertIn("z2026_iw3_iwd_index_fixture_smoke", workflow)
        self.assertIn("IW3_JNI_IMPORTED_IWD_INDEX_FIXTURE_PASS", emulator)


if __name__ == "__main__":
    unittest.main()
