#include "iw3_android_iwd_names_compat.h"
#include <cassert>
#include <cstdio>
#include <cstring>

int FS_HashFileName(const char*, int);
int FS_FilenameCompare(const char*, const char*);
void FS_ConvertPath(char*);
extern "C" int z2026_iw3_iwd_names_smoke();

int main() {
    // Original IW3 hashing ignores the extension and normalizes
    // backslash + ASCII case; fixed values from original algorithm.
    assert(FS_HashFileName("maps/mp/mp_crash.d3dbsp", 1024) == 785);
    assert(FS_HashFileName("MAPS\\MP\\MP_CRASH.D3DBSP", 1024) == 785);
    assert(FS_HashFileName("scripts/zombies.gsc", 1024) == 917);
    assert(FS_HashFileName("SCRIPTS\\ZOMBIES.GSC", 1024) == 917);
    assert(FS_HashFileName("weapons/mp40", 1024) == 230);
    assert(FS_HashFileName("weapons/MP40", 1024) == 230);
    // A high-bit byte must be passed to tolower as unsigned char; with
    // signed char this value becomes negative and changes the original hash.
    const char highBitName[] = {static_cast<char>(0xFE), 'A', '.', 't', 'x', 't', '\0'};
    assert(FS_HashFileName(highBitName, 1024) == 930);
    assert(FS_FilenameCompare("maps/mp/mp_crash.d3dbsp",
                              "MAPS\\MP\\MP_CRASH.D3DBSP") == 0);
    assert(FS_FilenameCompare("weapons:mp40", "WEAPONS/mp40") == 0);
    assert(FS_FilenameCompare("weapons/mp40", "weapons/mp41") == -1);
    char path[] = "maps\\mp:mp_crash.d3dbsp";
    FS_ConvertPath(path);
    assert(std::strcmp(path, "maps/mp/mp_crash.d3dbsp") == 0);
    assert(z2026_iw3_iwd_names_smoke() == 1);
    std::puts("IW3_ORIGINAL_IWD_FILENAME_HASH_COMPARE_NORMALIZE_HOST_GREEN");
}
