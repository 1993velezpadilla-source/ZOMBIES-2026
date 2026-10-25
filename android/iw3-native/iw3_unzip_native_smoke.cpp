#include "iw3_android_unzip_compat.h"
#include "iw3_android_platform.h"
#include "unzip.h"
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
} // namespace

extern "C" IW3_UNZIP_EXPORT int z2026_iw3_unzip_smoke(const char *directory) {
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
        "iw3-unzip-smoke-%ld.zip", static_cast<long>(::getpid()));
    if (pathLength <= 0 || static_cast<std::size_t>(pathLength) >= sizeof(path)) return 0;

    // The original ZIP parser must resolve its archive through the same
    // root-confined file-open boundary used for future real IWD packages.
    if (z2026_platform_write_file(path, archiveBytes.data(), archiveBytes.size()) !=
        static_cast<int>(archiveBytes.size())) return 0;

    bool ok = false;
    unzFile parsed = unzOpen(path);
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
    if (z2026_platform_unlink_file(path) != 0) ok = false;
    return ok ? 1 : 0;
}
