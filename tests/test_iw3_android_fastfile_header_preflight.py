from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/GameDataImporter.java"
HELPER = ROOT / "android/iw3-native/android_app/app/src/main/java/org/z2026/iw3nativeprobe/FastFileHeader.java"
ENGINE = ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp"


class FastFileHeaderPreflightTests(unittest.TestCase):
    def test_preflight_contract_matches_original_loader(self):
        engine = ENGINE.read_text(encoding="utf-8")
        helper = HELPER.read_text(encoding="utf-8")

        # DB_LoadXFileInternal is authoritative: this tree accepts the unsecure
        # magic/version and explicitly rejects the authenticated variant.
        self.assertIn('memcmp(magic, "IWff0100", 8u)', engine)
        self.assertIn('memcmp(magic, "IWffu100", 8u)', engine)
        self.assertIn("if (version != 5)", engine)
        self.assertIn('fileIsSecure = memcmp(magic, "IWffu100", 8u) != 0;', engine)
        self.assertIn('failureReason = "authenticated file not supported";', engine)

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


if __name__ == "__main__":
    unittest.main()
