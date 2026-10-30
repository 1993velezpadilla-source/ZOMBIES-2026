from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FastFilePosixIoRegressionTests(unittest.TestCase):
    def test_reader_uses_positioned_posix_io_and_retries_eintr(self):
        header = (ROOT / "third_party/KisakCOD/src/database/db_fastfile_posix_io.h").read_text()
        self.assertIn("pread(", header)
        self.assertIn("savedError == EINTR", header)
        self.assertIn("std::numeric_limits<off_t>::max()", header)
        self.assertIn("DBFastFilePosixFdFromOpaque", header)
        self.assertIn("DBFastFilePosixOpaqueFromFd", header)

    def test_original_loader_has_android_read_path_and_keeps_windows_path(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        read_data = source.split("int32_t __cdecl DB_ReadData()", 1)[1].split(
            "void __stdcall DB_FileReadCompletion", 1
        )[0]
        self.assertIn("#if defined(__ANDROID__)", read_data)
        self.assertIn("DBFastFilePosixReadAt", read_data)
        self.assertIn("ReadFileEx", read_data)
        self.assertIn("posixBytesRead", source)
        self.assertIn("posixReadError", source)
        self.assertIn("posixEof", source)

    def test_android_stream_accounts_for_short_reads_and_truncated_eof(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        wait_stage = source.split("int32_t DB_WaitXFileStage()", 1)[1].split(
            "void __cdecl DB_LoadedExternalData", 1
        )[0]
        self.assertIn("g_load.posixBytesRead", wait_stage)
        self.assertIn("g_load.stream.avail_in +=", wait_stage)
        self.assertIn("Unexpected end of FastFile", source)
        self.assertIn("if (!DB_ReadData() && g_load.posixReadError != 0)", source)
        self.assertIn("posixEof", source)

    def test_android_file_metadata_and_close_use_posix_services(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        self.assertIn("fstat(fd, &fileStat)", source)
        self.assertIn("close(fd)", source)
        self.assertIn("CloseHandle(g_load.f)", source)

    def test_generator_is_explicitly_a_source_body_harness_not_runtime(self):
        generator = (ROOT / "tools/iw3_android/prepare_real_engine_db_read_posix.py").read_text()
        self.assertIn("extract_function", generator)
        self.assertIn("DB_ReadData", generator)
        self.assertIn("DB_WaitXFileStage", generator)
        self.assertIn('"playable_apk": False', generator)
        self.assertIn("ReadFileEx", generator)

    def test_original_header_and_asset_deserialization_are_retained(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        self.assertIn("DB_ParseFastFileHeader", source)
        self.assertIn("DB_AllocXZoneMemory", source)
        self.assertIn("DB_InitStreams", source)
        self.assertIn("Load_XAssetArrayCustom", source)
        self.assertIn("DB_FinishGeometryBlocks", source)

    def test_windows_callback_declaration_is_guarded_only_for_android(self):
        header = (ROOT / "third_party/KisakCOD/src/database/database.h").read_text()
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        self.assertIn("#if !defined(__ANDROID__)\nvoid __stdcall DB_FileReadCompletion", header)
        self.assertIn("#if !defined(__ANDROID__)\nvoid __stdcall DB_FileReadCompletion", source)


if __name__ == "__main__":
    unittest.main()
