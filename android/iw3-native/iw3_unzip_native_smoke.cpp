#include "iw3_android_unzip_compat.h"
#include "iw3_android_platform.h"
#include "iw3_android_iwd_mount_compat.h"
#include "iw3_android_iwd_directory_compat.h"
#include "iw3_android_iwd_lookup_compat.h"
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
bool index_original_iwd(const char *path, const std::array<Entry, 2> &expected, bool *searchpath_ok) {
    if (searchpath_ok) *searchpath_ok = false;
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
             path_length >= 4 && stored_length == path_length &&
             std::strcmp(iwd->iwdFilename, path) == 0 &&
             std::strcmp(path + path_length - 4, ".iwd") == 0;

        // The real FS_FOpenFileReadForThread path clones an IWD archive by
        // reopening iwdFilename. Verify the stored path is directly usable,
        // then read the indexed member through the original ZIP implementation.
        bool cloned_handle_reopen_read_ok = false;
        unzFile reopened = unzReOpen(
            iwd->iwdFilename, reinterpret_cast<unzFile>(iwd->handle));
        if (reopened) {
            if (unzSetCurrentFileInfoPosition(reopened, iwd->buildBuffer[0].pos) == UNZ_OK &&
                unzOpenCurrentFile(reopened) == UNZ_OK) {
                std::vector<char> reopened_bytes(expected[0].payload.size() + 1, '\\0');
                const int got = unzReadCurrentFile(
                    reopened, reopened_bytes.data(),
                    static_cast<unsigned>(reopened_bytes.size()));
                const int close_current = unzCloseCurrentFile(reopened);
                cloned_handle_reopen_read_ok =
                    got == static_cast<int>(expected[0].payload.size()) &&
                    std::string(reopened_bytes.data(), static_cast<std::size_t>(got)) ==
                        expected[0].payload &&
                    close_current == UNZ_OK;
            }
            if (unzClose(reopened) != UNZ_OK)
                cloned_handle_reopen_read_ok = false;
        }
        ok = ok && cloned_handle_reopen_read_ok;

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

        // Exercise the original list insertion with the indexed fixture.
        if (ok && searchpath_ok) {
            searchpath_s *const previous = fs_searchpaths;
            auto *search = static_cast<searchpath_s *>(
                Z_Malloc(static_cast<int32_t>(sizeof(searchpath_s)),
                         "FS_AddIwdFilesForGameDirectory", 3));
            if (search) {
                search->next = nullptr;
                search->iwd = iwd;
                search->dir = nullptr;
                search->bLocalized = 0;
                search->ignore = 0;
                search->ignorePureCheck = 0;
                search->language = 0;
                FS_AddSearchPath(search);
                bool found = false;
                for (searchpath_s *cursor = fs_searchpaths; cursor; cursor = cursor->next) {
                    if (cursor == search && cursor->iwd == iwd) {
                        found = true;
                        break;
                    }
                }
                *searchpath_ok = found && fs_searchpaths == search &&
                                 search->next == previous;
                fs_searchpaths = previous;
                Z_Free(search, 3);
            }
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

bool scan_original_iwd_directory(const char *root,
                                 const std::array<Entry, 2> &expected,
                                 const Bytes &archiveBytes,
                                 bool *lookup_ok) {
    if (lookup_ok) *lookup_ok = false;
    if (!root || root[0] != '/' || std::strlen(root) > 700) return false;

    char subdir[48]{};
    char basename[64]{};
    char relative_archive[128]{};
    char root_copy[1024]{};
    char game_copy[48]{};
    char disk_dir[96]{};
    char disk_relative[128]{};
    const char disk_payload[] = "KISAKCOD_ORIGINAL_DIRECTORY_FALLBACK";
    bool disk_dir_created = false;
    bool disk_file_written = false;
    const long pid = static_cast<long>(::getpid());
    const int subdir_length = std::snprintf(subdir, sizeof(subdir), "iw3-scan-%ld", pid);
    const int basename_length = std::snprintf(
        basename, sizeof(basename), "iw3-directory-scan-%ld.iwd", pid);
    const int relative_length = std::snprintf(
        relative_archive, sizeof(relative_archive), "%s/%s", subdir, basename);
    const int root_length = std::snprintf(root_copy, sizeof(root_copy), "%s", root);
    const int game_length = std::snprintf(game_copy, sizeof(game_copy), "%s", subdir);
    if (subdir_length <= 0 || static_cast<std::size_t>(subdir_length) >= sizeof(subdir) ||
        basename_length <= 0 || static_cast<std::size_t>(basename_length) >= sizeof(basename) ||
        relative_length <= 0 || static_cast<std::size_t>(relative_length) >= sizeof(relative_archive) ||
        root_length <= 0 || static_cast<std::size_t>(root_length) >= sizeof(root_copy) ||
        game_length <= 0 || static_cast<std::size_t>(game_length) >= sizeof(game_copy) ||
        std::strlen(root) + 1 + std::strlen(subdir) + 1 + std::strlen(basename) >= 260) {
        return false;
    }
    if (z2026_platform_mkdir(subdir) != 0) return false;
    const bool wrote = z2026_platform_write_file(
        relative_archive, archiveBytes.data(), archiveBytes.size()) ==
        static_cast<int>(archiveBytes.size());
    bool ok = false;

    if (wrote) {
        const int disk_dir_length = std::snprintf(
            disk_dir, sizeof(disk_dir), "%s/maps", subdir);
        const int disk_relative_length = std::snprintf(
            disk_relative, sizeof(disk_relative),
            "%s/maps/iw3_android_disk_probe.txt", subdir);
        if (disk_dir_length > 0 &&
            static_cast<std::size_t>(disk_dir_length) < sizeof(disk_dir) &&
            disk_relative_length > 0 &&
            static_cast<std::size_t>(disk_relative_length) < sizeof(disk_relative)) {
            disk_dir_created = z2026_platform_mkdir(disk_dir) == 0;
            if (disk_dir_created) {
                disk_file_written = z2026_platform_write_file(
                    disk_relative, disk_payload, sizeof(disk_payload) - 1) ==
                    static_cast<int>(sizeof(disk_payload) - 1);
            }
        }
        const int old_count = fs_iwdFileCount;
        const int old_feed = fs_checksumFeed;
        searchpath_s *const previous = fs_searchpaths;
        char previous_gamedir[sizeof(fs_gamedir)]{};
        std::memcpy(previous_gamedir, fs_gamedir, sizeof(previous_gamedir));
        fs_checksumFeed = 0;

        // Execute the ORIGINAL game-directory registration path, not only its
        // child IWD scanner. The engine first registers directory_t, then scans
        // the same rooted folder and prepends the indexed IWD searchpath.
        FS_AddGameDirectory(root_copy, game_copy, 0, 0);

        searchpath_s *const inserted = fs_searchpaths;
        searchpath_s *const directory_node = inserted ? inserted->next : nullptr;
        if (inserted && inserted != previous && directory_node &&
            directory_node != previous && directory_node->next == previous &&
            inserted->iwd && !inserted->dir && directory_node->dir &&
            !directory_node->iwd &&
            std::strcmp(directory_node->dir->path, root_copy) == 0 &&
            std::strcmp(directory_node->dir->gamedir, game_copy) == 0 &&
            std::strcmp(fs_gamedir, game_copy) == 0 &&
            inserted->iwd->numfiles == static_cast<int>(expected.size()) &&
            inserted->bLocalized == 0 && inserted->language == 0 &&
            directory_node->bLocalized == 0 && directory_node->language == 0 &&
            inserted->iwd->checksum == inserted->iwd->pure_checksum &&
            fs_iwdFileCount == old_count + static_cast<int>(expected.size()) &&
            std::strcmp(inserted->iwd->iwdBasename, basename) == 0 &&
            std::strcmp(inserted->iwd->iwdGamename, game_copy) == 0) {
            ok = inserted->iwd->buildBuffer != nullptr &&
                 inserted->iwd->hashTable != nullptr &&
                 inserted->iwd->hashSize != 0 &&
                 (inserted->iwd->hashSize & (inserted->iwd->hashSize - 1)) == 0;
            for (std::size_t i = 0; ok && i < expected.size(); ++i) {
                fileInIwd_s *indexed = &inserted->iwd->buildBuffer[i];
                if (!indexed->name ||
                    std::strcmp(indexed->name, expected[i].name.c_str()) != 0) {
                    ok = false;
                    break;
                }
                const int bucket = FS_HashFileName(
                    indexed->name, static_cast<int>(inserted->iwd->hashSize));
                bool found = false;
                fileInIwd_s *entry = inserted->iwd->hashTable[bucket];
                for (std::size_t step = 0; entry && step < expected.size();
                     ++step, entry = entry->next) {
                    if (entry == indexed) {
                        found = true;
                        break;
                    }
                }
                if (!found) ok = false;
            }

            // Exercise the original FS_FOpenFileReadForThread lookup-only
            // branch against the live original searchpath list. This verifies
            // IWD hit, miss, and traversal rejection; it does not allocate a
            // handle or claim that the original FS_Read path is ported.
            const int lookup_hit = z2026_iw3_original_searchpath_lookup(
                expected[0].name.c_str(), nullptr, FS_THREAD_MAIN);
            const int lookup_miss = z2026_iw3_original_searchpath_lookup(
                "maps/iw3_android_missing.txt", nullptr, FS_THREAD_MAIN);
            const int lookup_disk_hit = z2026_iw3_original_searchpath_lookup(
                "maps/iw3_android_disk_probe.txt", nullptr, FS_THREAD_MAIN);
            const int lookup_traversal = z2026_iw3_original_searchpath_lookup(
                "../maps/iw3_android_probe.txt", nullptr, FS_THREAD_MAIN);
            const bool lookup_pass = lookup_hit == 1 &&
                                     disk_file_written &&
                                     lookup_disk_hit == 1 &&
                                     lookup_miss == -1 &&
                                     lookup_traversal == -1;
            if (lookup_ok) *lookup_ok = lookup_pass;
            ok = ok && lookup_pass;
        }

        // Restore global state before freeing the fixture-owned searchpaths.
        fs_searchpaths = previous;
        searchpath_s *cursor = inserted;
        std::size_t released = 0;
        while (cursor && cursor != previous && released < 8) {
            searchpath_s *next = cursor->next;
            if (cursor->iwd) {
                iwd_t *iwd = cursor->iwd;
                if (unzClose(reinterpret_cast<unzFile>(iwd->handle)) != UNZ_OK)
                    ok = false;
                if (iwd->buildBuffer) Z_Free(iwd->buildBuffer, 3);
                Z_Free(iwd, 3);
            }
            if (cursor->dir) Z_Free(cursor->dir, 3);
            Z_Free(cursor, 3);
            cursor = next;
            ++released;
        }
        if (cursor != previous) ok = false;
        std::memcpy(fs_gamedir, previous_gamedir, sizeof(previous_gamedir));
        fs_iwdFileCount = old_count;
        fs_checksumFeed = old_feed;
    }

    if (disk_dir_created) {
        const int disk_unlink = z2026_platform_unlink_file(disk_relative);
        if (disk_file_written && disk_unlink != 0) ok = false;
        if (z2026_platform_rmdir(disk_dir) != 0) ok = false;
    }
    if (wrote && z2026_platform_unlink_file(relative_archive) != 0) ok = false;
    if (z2026_platform_rmdir(subdir) != 0) ok = false;
    return ok;
}

} // namespace

extern "C" IW3_UNZIP_EXPORT int z2026_iw3_unzip_smoke(const char *directory, int *iwd_mount_ok, int *iwd_searchpath_ok, int *iwd_directory_scan_ok, int *iwd_lookup_ok) {
    if (iwd_mount_ok) *iwd_mount_ok = 0;
    if (iwd_searchpath_ok) *iwd_searchpath_ok = 0;
    if (iwd_directory_scan_ok) *iwd_directory_scan_ok = 0;
    if (iwd_lookup_ok) *iwd_lookup_ok = 0;
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
    bool searchpath_ok = false;
    const bool mount_ok = index_original_iwd(path, entries, &searchpath_ok);
    bool lookup_ok = false;
    const bool directory_scan_ok = scan_original_iwd_directory(directory, entries, archiveBytes, &lookup_ok);
    if (iwd_lookup_ok) *iwd_lookup_ok = lookup_ok ? 1 : 0;
    if (iwd_mount_ok) *iwd_mount_ok = mount_ok ? 1 : 0;
    if (iwd_searchpath_ok) *iwd_searchpath_ok = searchpath_ok ? 1 : 0;
    if (iwd_directory_scan_ok) *iwd_directory_scan_ok = directory_scan_ok ? 1 : 0;
    ok = ok && mount_ok && searchpath_ok && directory_scan_ok && lookup_ok;
    if (z2026_platform_unlink_file(path) != 0) ok = false;
    return ok ? 1 : 0;
}
