#include <cstdio>
#include <string>
#include <filesystem>

extern "C" int z2026_iw3_unzip_smoke(const char *directory);

int main() {
    const std::string directory = std::filesystem::temp_directory_path().string();
    if (!z2026_iw3_unzip_smoke(directory.c_str())) {
        std::fputs("IW3_ORIGINAL_ZIP32_PARSER_HOST_FAIL\n", stderr);
        return 1;
    }
    std::puts("IW3_ORIGINAL_ZIP32_PARSER_HOST_GREEN");
    return 0;
}
