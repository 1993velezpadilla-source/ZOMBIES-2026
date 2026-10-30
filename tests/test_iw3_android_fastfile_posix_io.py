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
        self.assertIn("g_load.posixEof = bytesRead < 0x40000u;", source)
        self.assertIn("Unexpected end of FastFile", source)
        self.assertIn("if (!DB_ReadData() && g_load.posixReadError != 0)", source)
        load_data = source.split("void __cdecl DB_LoadXFileData", 1)[1].split(
            "void DB_ReadXFileStage", 1
        )[0]
        eof_path = load_data.split(
            "if (!g_load.stream.avail_in && g_load.posixEof && !g_load.outstandingReads)", 1
        )[1].split("#endif", 1)[0]
        self.assertIn("DB_CancelLoadXFile();", eof_path)
        self.assertLess(eof_path.index("DB_CancelLoadXFile();"), eof_path.index("Com_Error("))
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

    def test_android_read_error_cleans_up_before_err_drop(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        # rindex selects the definition rather than the forward declaration.
        start = source.rindex("void DB_ReadXFileStage()")
        read_stage = source[start:].split("int32_t __cdecl DB_ReadData()", 1)[0]
        android_error = read_stage.split(
            "if (!DB_ReadData() && g_load.posixReadError != 0)", 1
        )[1].split("#else", 1)[0]
        self.assertIn("const int readError = g_load.posixReadError;", android_error)
        self.assertIn("DB_CancelLoadXFile();", android_error)
        self.assertLess(
            android_error.index("DB_CancelLoadXFile();"),
            android_error.index("Com_Error("),
        )
        self.assertIn("g_load.filename, readError", android_error)
        # The original Win32 error path must remain unchanged.
        windows_error = read_stage.split("#else", 1)[1].split("#endif", 1)[0]
        self.assertIn('Com_Error(ERR_DROP, "Read error of file', windows_error)
        self.assertNotIn("DB_CancelLoadXFile();", windows_error)

    def test_android_fastfile_header_failures_release_fd_before_dispatch(self):
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        start = source.index("void __cdecl DB_LoadXFileInternal()")
        end = source.index("bool __cdecl DB_IsMinimumFastFileLoaded()", start)
        body = source[start:end]

        cases = (
            (
                'if (!g_load.outstandingReads)',
                'DB_WaitXFileStage();',
                "Com_Error(",
            ),
            (
                'if (headerStatus == DBFastFileHeaderStatus::TruncatedMagic)',
                'if (headerStatus == DBFastFileHeaderStatus::InvalidMagic)',
                "MyAssertHandler(",
            ),
            (
                'if (headerStatus == DBFastFileHeaderStatus::InvalidMagic)',
                'if (headerStatus == DBFastFileHeaderStatus::TruncatedVersion)',
                "Com_Error(",
            ),
            (
                'if (headerStatus == DBFastFileHeaderStatus::TruncatedVersion)',
                'version = parsedHeader.version;',
                "MyAssertHandler(",
            ),
            (
                'if (headerStatus == DBFastFileHeaderStatus::UnsupportedVersion)',
                'if (headerStatus != DBFastFileHeaderStatus::Ok)',
                "Com_Error(",
            ),
            (
                'if (headerStatus != DBFastFileHeaderStatus::Ok)',
                'fileIsSecure = parsedHeader.secure;',
                "MyAssertHandler(",
            ),
            (
                'if (g_trackLoadProgress)',
                'fileSize = static_cast<int32_t>(fileStat.st_size);',
                "Com_Error(",
            ),
        )
        for start_marker, end_marker, dispatch in cases:
            with self.subTest(path=start_marker):
                block = body.split(start_marker, 1)[1].split(end_marker, 1)[0]
                self.assertIn("#if defined(__ANDROID__)", block)
                self.assertIn("DB_CancelLoadXFile();", block)
                self.assertLess(block.index("DB_CancelLoadXFile();"), block.index(dispatch))

    def test_windows_callback_declaration_is_guarded_only_for_android(self):
        header = (ROOT / "third_party/KisakCOD/src/database/database.h").read_text()
        source = (ROOT / "third_party/KisakCOD/src/database/db_file_load.cpp").read_text()
        self.assertIn("#if !defined(__ANDROID__)\nvoid __stdcall DB_FileReadCompletion", header)
        self.assertIn("#if !defined(__ANDROID__)\nvoid __stdcall DB_FileReadCompletion", source)


if __name__ == "__main__":
    unittest.main()
