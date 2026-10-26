#include "iw3_android_unzip_compat.h"
#include "iw3_android_platform.h"
#include "iw3_android_iwd_mount_compat.h"
#include <array>
#include <string>
#include <vector>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <unistd.h>

#if defined(__GNUC__)
#define IW3_UNZIP_EXPORT __attribute__((visibility("default")))
#else
#define IW3_UNZIP_EXPORT
#endif

namespace {
using Bytes = std::vector<std::uint8_t>;
struct Entry {
    std::string name;
    std::string payload;
    std::uint16_t method;
    Bytes compressed;
    std::uint32_t crc;
    std::uint32_t localOffset;
};
void put16(Bytes &out, std::uint16_t v) {
    out.push_back(static_cast<std::uint8_t>(v));
    out.push_back(static_cast<std::uint8_t>(v >> 8));
}
void put32(Bytes &out, std::uint32_t v) {
    put16(out, static_cast<std::uint16_t>(v));
    put16(out, static_cast<std::uint16_t>(v >> 16));
}
bool raw_deflate(const std::string &input, Bytes &out) {
    z_stream stream{};
    if (deflateInit2(&stream, Z_DEFAULT_COMPRESSION, Z_DEFLATED, -MAX_WBITS,
                     8, Z_DEFAULT_STRATEGY) != Z_OK) return false;
    out.resize(input.size() + 128);
    stream.next_in = reinterpret_cast<Bytef *>(
        const_cast<char *>(input.data()));
    stream.avail_in = static_cast<uInt>(input.size());
    stream.next_out = reinterpret_cast<Bytef *>(out.data());
    stream.avail_out = static_cast<uInt>(out.size());
    const int rc = deflate(&stream, Z_FINISH);
    if (rc != Z_STREAM_END) {
        deflateEnd(&stream);
        return false;
    }
    out.resize(static_cast<std::size_t>(stream.total_out));
    return deflateEnd(&stream) == Z_OK;
}
bool make_zip(Bytes &out, std::array<Entry, 2> &entries) {
    for (auto &entry : entries) {
        const auto *data = reinterpret_cast<const Bytef *>(entry.payload.data());
        entry.crc = static_cast<std::uint32_t>(crc32(0, data,
            static_cast<uInt>(entry.payload.size())));
        if (entry.method == 0) {
            entry.compressed.assign(entry.payload.begin(), entry.payload.end());
        } else if (entry.method == 8) {
            if (!raw_deflate(entry.payload, entry.compressed)) return false;
        } else return false;
        if (out.size() > UINT32_MAX) return false;
        entry.localOffset = static_cast<std::uint32_t>(out.size());
        put32(out, 0x04034b50u); put16(out, 20); put16(out, 0);
        put16(out, entry.method); put16(out, 0); put16(out, 0);
        put32(out, entry.crc);
        put32(out, static_cast<std::uint32_t>(entry.compressed.size()));
        put32(out, static_cast<std::uint32_t>(entry.payload.size()));
        put16(out, static_cast<std::uint16_t>(entry.name.size())); put16(out, 0);
        out.insert(out.end(), entry.name.begin(), entry.name.end());
        out.insert(out.end(), entry.compressed.begin(), entry.compressed.end());
    }
    if (out.size() > UINT32_MAX) return false;
    const std::uint32_t centralOffset = static_cast<std::uint32_t>(out.size());
    for (const auto &entry : entries) {
        put32(out, 0x02014b50u); put16(out, 20); put16(out, 20);
        put16(out, 0); put16(out, entry.method); put16(out, 0); put16(out, 0);
        put32(out, entry.crc);
        put32(out, static_cast<std::uint32_t>(entry.compressed.size()));
        put32(out, static_cast<std::uint32_t>(entry.payload.size()));
        put16(out, static_cast<std::uint16_t>(entry.name.size()));
        put16(out, 0); put16(out, 0); put16(out, 0); put16(out, 0);
        put32(out, 0); put32(out, entry.localOffset);
        out.insert(out.end(), entry.name.begin(), entry.name.end());
    }
    const auto centralSize = static_cast<std::uint32_t>(out.size() - centralOffset);
    put32(out, 0x06054b50u); put16(out, 0); put16(out, 0);
    put16(out, static_cast<std::uint16_t>(entries.size()));
    put16(out, static_cast<std::uint16_t>(entries.size()));
    put32(out, centralSize); put32(out, centralOffset); put16(out, 0);
    return true;
}
bool read_current(unzFile archive, const Entry &expected) {
    unz_file_info info{};
    char name[256]{};
    if (unzGetCurrentFileInfo(archive, &info, name, sizeof(name),
                              nullptr, 0, nullptr, 0) != UNZ_OK) return false;
    if (expected.name != name || info.compression_method != expected.method ||
        info.uncompressed_size != expected.payload.size() ||
        info.compressed_size != expected.compressed.size()) return false;
    if (unzOpenCurrentFile(archive) != UNZ_OK) return false;
    std::vector<char> bytes(expected.payload.size() + 1, '\0');
    const int got = unzReadCurrentFile(archive, bytes.data(),
                                        static_cast<unsigned>(bytes.size()));
    const int closeRc = unzCloseCurrentFile(archive);
    return got == static_cast<int>(expected.payload.size()) &&
           std::string(bytes.data(), static_cast<std::size_t>(got)) == expected.payload &&
           closeRc == UNZ_OK;
}
bool index_original_iwd(const char *path, const std::array<Entry, 2> &expected) {
    const int old_count = fs_iwdFileCount;
    const int old_feed = fs_checksumFeed;
    fs_checksumFeed = 0;
    iwd_t *iwd = FS_LoadZipFile(const_cast<char *>(path), const_cast<char *>(path));
    bool ok = iwd != nullptr;
    if (iwd) {
        const std::size_t path_length = std::strlen(path);
        const std::size_t stored_length = std::strlen(iwd->iwdFilename);
        ok = ok && iwd->numfiles == static_cast<int>(expected.size()) &&
             iwd->buildBuffer != nullptr && iwd->hashTable != nullptr &&
             iwd->hashSize != 0 && (iwd->hashSize & (iwd->hashSize - 1)) == 0 &&
             iwd->checksum == iwd->pure_checksum &&
             fs_iwdFileCount == old_count + static_cast<int>(expected.size()) &&
             std::strcmp(iwd->iwdBasename, path) == 0 &&
             path_length >= 4 && stored_length + 4 == path_length &&
             std::memcmp(iwd->iwdFilename, path, stored_length) == 0 &&
             std::strcmp(path + path_length - 4, ".iwd") == 0;

        for (std::size_t i = 0; ok && i < expected.size(); ++i) {
            fileInIwd_s *indexed = &iwd->buildBuffer[i];
            if (!indexed->name || std::strcmp(indexed->name, expected[i].name.c_str()) != 0) {
                ok = false;
                break;
            }
            const int bucket = FS_HashFileName(indexed->name, static_cast<int>(iwd->hashSize));
            bool found = false;
            fileInIwd_s *cursor = iwd->hashTable[bucket];
            for (std::size_t step = 0; cursor && step < expected.size(); ++step, cursor = cursor->next) {
                if (cursor == indexed) {
                    found = true;
                    break;
                }
            }
            if (!found) ok = false;
        }

        const int close_rc = unzClose(reinterpret_cast<unzFile>(iwd->handle));
        fileInIwd_s *build_buffer = iwd->buildBuffer;
        Z_Free(build_buffer, 3);
        Z_Free(iwd, 3);
        if (close_rc != UNZ_OK) ok = false;
    }
    fs_iwdFileCount = old_count;
    fs_checksumFeed = old_feed;
    return ok;
}
} // namespace

extern "C" IW3_UNZIP_EXPORT int z2026_iw3_unzip_smoke(const char *directory, int *iwd_mount_ok) {
    if (iwd_mount_ok) *iwd_mount_ok = 0;
    static_assert(sizeof(unz_global_info) == 8, "IW3 ZIP32 global-info layout drift");
    static_assert(sizeof(unz_file_info) == 80, "IW3 ZIP32 file-info layout drift");
    static_assert(sizeof(unz_file_info_internal) == 4, "IW3 ZIP32 file offset layout drift");
    if (!directory || directory[0] != '/' || std::strlen(directory) > 700 ||
        z2026_platform_set_data_root(directory) != 0) return 0;

    std::array<Entry, 2> entries{{
        {"maps/iw3_android_probe.txt", "KISAKCOD_IWD_STORED_64BIT", 0, {}, 0, 0},
        {"images/iw3_android_probe.txt", "KISAKCOD_IWD_DEFLATED_64BIT_SAFE", 8, {}, 0, 0}
    }};
    Bytes archiveBytes;
    if (!make_zip(archiveBytes, entries)) return 0;
    char path[96]{};
    const int pathLength = std::snprintf(path, sizeof(path),
        "iw3-unzip-smoke-%ld.iwd", static_cast<long>(::getpid()));
    if (pathLength <= 0 || static_cast<std::size_t>(pathLength) >= sizeof(path)) return 0;

    // The archive fixture uses the real IWD extension. Verify that the rooted
    // discovery API sees it and that original unzOpen accepts both the
    // relative probe path and an absolute FS_BuildOSPath-style path beneath
    // the canonical app-data root.
    if (z2026_platform_write_file(path, archiveBytes.data(), archiveBytes.size()) !=
        static_cast<int>(archiveBytes.size())) return 0;
    std::vector<char> names(65536);
    std::size_t name_count = 0;
    const int names_bytes = z2026_platform_list_iwd_files(
        "", names.data(), names.size(), &name_count);
    bool discovered = false;
    if (names_bytes >= 0) {
        std::size_t offset = 0;
        while (offset < static_cast<std::size_t>(names_bytes)) {
            const char *name = names.data() + offset;
            if (std::strcmp(name, path) == 0) discovered = true;
            offset += std::strlen(name) + 1;
        }
    }
    char absolute_path[1024]{};
    const int absolute_length = std::snprintf(
        absolute_path, sizeof(absolute_path), "%s/%s", directory, path);
    if (absolute_length <= 0 ||
        static_cast<std::size_t>(absolute_length) >= sizeof(absolute_path)) {
        z2026_platform_unlink_file(path);
        return 0;
    }

    auto parse_original_iwd = [&](const char *archive_path) {
        bool ok = false;
        unzFile parsed = unzOpen(archive_path);
        if (parsed) {
            unz_global_info global{};
            ok = unzGetGlobalInfo(parsed, &global) == UNZ_OK &&
                 global.number_entry == entries.size() &&
                 unzGoToFirstFile(parsed) == UNZ_OK &&
                 read_current(parsed, entries[0]) &&
                 unzGoToNextFile(parsed) == UNZ_OK &&
                 read_current(parsed, entries[1]) &&
                 unzGoToNextFile(parsed) == UNZ_END_OF_LIST_OF_FILE;
            if (unzClose(parsed) != UNZ_OK) ok = false;
        }
        return ok;
    };
    const bool relative_parse_ok = parse_original_iwd(path);
    const bool absolute_parse_ok = parse_original_iwd(absolute_path);
    bool ok = discovered && name_count >= 1 &&
              relative_parse_ok && absolute_parse_ok;
    const bool mount_ok = index_original_iwd(path, entries);
    if (iwd_mount_ok) *iwd_mount_ok = mount_ok ? 1 : 0;
    if (z2026_platform_unlink_file(path) != 0) ok = false;
    return ok ? 1 : 0;
}
