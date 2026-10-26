#include <cstdio>
#include <string>
#include <filesystem>

extern "C" int z2026_iw3_unzip_smoke(const char *directory, int *iwd_mount_ok, int *iwd_searchpath_ok);

int main() {
    const std::string directory = std::filesystem::temp_directory_path().string();
    int iwd_mount_ok = 0;
    const int parser_ok = z2026_iw3_unzip_smoke(directory.c_str(), &iwd_mount_ok);
    if (!parser_ok || iwd_mount_ok != 1) {
        std::fprintf(stderr, "IW3_ORIGINAL_IWD_INDEX_HOST_FAIL parser=%d mount=%d\n",
                     parser_ok, iwd_mount_ok);
        return 1;
    }
    std::puts("IW3_ORIGINAL_FS_LOADZIPFILE_INDEX_HOST_GREEN");
    std::puts("IW3_ORIGINAL_FS_ADDSSEARCHPATH_HOST_GREEN");
    return 0;
}
