from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/GameDataImporter.java"
HELPER = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/FastFileHeader.java"
PORTABLE_HEADER = ROOT / "third_party/KisakCOD/src/database/db_fastfile_header.h"
NATIVE_TEST = ROOT / "android/iw3-native/db_fastfile_header_native_test.cpp"
CMAKE = ROOT / "android/iw3-native/CMakeLists.txt"
WORKFLOW = ROOT / ".github/workflows/iw3-original-android-jni.yml"
ENGINE = ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp"


class FastFileHeaderPreflightTests(unittest.TestCase):
    def test_preflight_contract_matches_original_loader(self):
        engine = ENGINE.read_text(encoding="utf-8")
        helper = HELPER.read_text(encoding="utf-8")

        # The original loader calls the portable parser; policy still rejects
        # the secure/authenticated variant after parsing.
        portable = PORTABLE_HEADER.read_text(encoding="utf-8")
        self.assertIn('#include "db_fastfile_header.h"', engine)
        self.assertIn("DB_ParseFastFileHeader(", engine)
        self.assertIn("DBFastFileHeaderStatus::UnsupportedVersion", engine)
        self.assertIn("fileIsSecure = parsedHeader.secure;", engine)
        self.assertIn('failureReason = "authenticated file not supported";', engine)
        self.assertNotIn("*(uint32_t *)magic", engine)
        self.assertNotIn("*(uint32_t *)&magic[4]", engine)
        self.assertNotIn("*(uint32_t *)g_load.stream.next_in", engine)
        self.assertIn('"IWff0100"', portable)
        self.assertIn('"IWffu100"', portable)
        self.assertIn("((uint32_t)data[11] << 24)", portable)
        self.assertIn("memcpy(out->magic, data, sizeof(out->magic))", portable)

        self.assertIn('SUPPORTED_MAGIC = "IWffu100"', helper)
        self.assertIn("SUPPORTED_VERSION = 5", helper)
        self.assertIn("HEADER_BYTES = 12", helper)
        self.assertIn("Truncated IW3 FastFile header", helper)
        self.assertIn("Unsupported IW3 FastFile magic", helper)
        self.assertIn("Unsupported IW3 FastFile version", helper)

    def test_importer_validates_ff_before_writing_consumed_prefix(self):
        importer = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("FastFileHeader.readAndValidate(input, source.relativePath)", importer)
        self.assertIn("if (!source.iwd)", importer)
        validate = importer.index("FastFileHeader.readAndValidate(input, source.relativePath)")
        write_prefix = importer.index("output.write(header)", validate)
        stream_copy = importer.index("while ((read = input.read(buffer)) != -1)", write_prefix)
        self.assertLess(validate, write_prefix)
        self.assertLess(write_prefix, stream_copy)
        self.assertIn("output.getFD().sync()", importer)
        self.assertIn("Os.rename(partial.getAbsolutePath(), target.getAbsolutePath())", importer)

    def test_preflight_is_not_mislabeled_as_fastfile_loading(self):
        helper = HELPER.read_text(encoding="utf-8")
        importer = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("does NOT load or mount a FastFile", helper)
        self.assertIn("does not", importer.lower())
        self.assertNotIn("DB_LoadXFileInternal(", importer)
        self.assertNotIn("DB_LoadXAssets(", importer)
    def test_portable_header_parser_is_exercised_by_host_and_arm64_gates(self):
        native_test = NATIVE_TEST.read_text(encoding="utf-8")
        cmake = CMAKE.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("unaligned + 1", native_test)
        self.assertIn("IW3_FASTFILE_HEADER_PORTABILITY_PASS", native_test)
        self.assertIn("iw3_fastfile_header_native_test", cmake)
        self.assertIn("iw3_fastfile_header_aarch64_compile", cmake)
        self.assertIn("aarch64-linux-android35-clang++", workflow)
        self.assertIn("db_fastfile_header_native_test.cpp", workflow)


if __name__ == "__main__":
    unittest.main()
