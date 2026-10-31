"""Execute the authentic IW3 weapon-file loader against adversarial short reads.

Only the extracted KisakCOD function is under test. All external services are
host fixtures; success is not evidence of a loaded game asset or Android APK.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"
SIGNATURE = "WeaponDef *__cdecl BG_LoadWeaponDefInternal("


class OriginalWeaponFileIOTests(unittest.TestCase):
    def test_authentic_weapon_loader_rejects_incomplete_files(self):
        original = function_source(SOURCE.read_text(encoding="utf-8"), SIGNATURE)
        self.assertIn("v11 < len || FS_Read((uint8_t *)buffer, len, f) != len", original)
        self.assertIn("FS_Read((uint8_t *)buffer, v11 - len, f) != v11 - len", original)
        self.assertIn("pathLength >= (int)sizeof(dest)", original)
        fixture = r"""
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#define __cdecl
constexpr int FS_READ = 0, CON_CHANNEL_PLAYERWEAP = 1;
constexpr int ERR_DROP = 2, WFT_NUM_FIELD_TYPES = 20, WEAPTYPE_PROJECTILE = 3;
struct snd_alias_list_t { int id; };
struct cspField_t { const char* name; int offset; int type; };
cspField_t weaponDefFields[502]{};
struct WeaponDef {
    const char* szInternalName = "test";
    char* szAmmoName = nullptr;
    char* szClipName = nullptr;
    void *viewLastShotEjectEffect = nullptr, *viewShellEjectEffect = nullptr;
    void *worldLastShotEjectEffect = nullptr, *worldShellEjectEffect = nullptr;
    snd_alias_list_t *raiseSound = nullptr, *putawaySound = nullptr;
    snd_alias_list_t *pickupSound = nullptr, *ammoPickupSound = nullptr;
    snd_alias_list_t *emptyFireSound = nullptr;
    double enemyCrosshairRange = 0;
    int weapType = 0;
};
static std::string fileBytes, lastPath;
static int reportedLength = -1, shortReadCall = 0;
static int opens = 0, closes = 0, reads = 0, parses = 0, warnings = 0;
static size_t cursor = 0;
static bool validInfo = true, acceptParse = true;
static std::vector<void*> allocations;
static char ammo[16] = "AMMO", clip[16] = "CLIP";
void* Hunk_AllocLow(size_t n, const char*, int) {
    void* p = std::calloc(1, n);
    assert(p);
    allocations.push_back(p);
    return p;
}
void InitWeaponDef(WeaponDef* w) { w->szAmmoName = ammo; w->szClipName = clip; }
int Com_sprintf(char* dst, unsigned cap, const char* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    const int result = std::vsnprintf(dst, cap, fmt, ap);
    va_end(ap);
    return result;
}
int FS_FOpenFileByMode(const char* path, int* handle, int) {
    ++opens;
    lastPath = path;
    cursor = 0;
    *handle = 31;
    return reportedLength >= 0 ? reportedLength : static_cast<int>(fileBytes.size());
}
int FS_Read(uint8_t* out, int count, int handle) {
    assert(handle == 31 && count >= 0 && count <= 10244);
    assert(cursor <= fileBytes.size());
    ++reads;
    size_t n = std::min(static_cast<size_t>(count), fileBytes.size() - cursor);
    if (reads == shortReadCall && n) --n;
    std::memcpy(out, fileBytes.data() + cursor, n);
    cursor += n;
    return static_cast<int>(n);
}
void FS_FCloseFile(int handle) { assert(handle == 31); ++closes; }
void Com_PrintWarning(int, const char*, ...) { ++warnings; }
int Info_Validate(const char*) { return validInfo; }
void SetConfigString(char**, const char*) {}
void SetConfigString2(char**, const char*) {}
int BG_ParseWeaponDefSpecificFieldType(uint8_t*, const char*, int) { return 1; }
int ParseConfigStringToStructCustomSize(...) { ++parses; return acceptParse; }
int I_stricmp(const char* a, const char* b) { return std::strcmp(a, b); }
snd_alias_list_t* Com_FindSoundAlias(const char*) {
    static snd_alias_list_t alias{1};
    return &alias;
}
void BG_SetupTransitionTimes(WeaponDef*) {}
void BG_CheckWeaponDamageRanges(WeaponDef*) {}
void BG_CheckProjectileValues(WeaponDef*) {}
int G_ParseWeaponAccurayGraphs(WeaponDef*) { return 1; }
void Com_Error(int, const char*, ...) { std::abort(); }
char* I_strlwr(char* s) { for (char* p=s; *p; ++p) if (*p>='A' && *p<='Z') *p += 32; return s; }
/* ORIGINAL_WEAPON_LOADER */
static void reset(const std::string& bytes) {
    for (void* p : allocations) std::free(p);
    allocations.clear();
    fileBytes = bytes;
    lastPath.clear();
    reportedLength = -1;
    shortReadCall = 0;
    opens = closes = reads = parses = warnings = 0;
    cursor = 0;
    validInfo = acceptParse = true;
}
static WeaponDef* invoke(const char* name = "mp40") {
    return BG_LoadWeaponDefInternal("sp", name);
}
int main() {
    const std::string magic = "WEAPONFILE";
    reset(magic + "\\damage\\42");
    assert(invoke() != nullptr && opens == 1 && closes == 1 && reads == 2 && parses == 1);
    assert(lastPath == "weapons/sp/mp40");
    reset(magic + "abc");
    reportedLength = static_cast<int>(magic.size()) - 1;
    assert(invoke() == nullptr && reads == 0 && closes == 1 && parses == 0);
    reset(magic + "abc");
    shortReadCall = 1;
    assert(invoke() == nullptr && reads == 1 && closes == 1 && parses == 0);
    reset(magic + "abc");
    shortReadCall = 2;
    assert(invoke() == nullptr && reads == 2 && closes == 1 && parses == 0);
    reset(std::string(magic.size(), 'X') + "abc");
    assert(invoke() == nullptr && closes == 1 && parses == 0);
    reset(magic + "abc");
    reportedLength = static_cast<int>(magic.size()) + 0x2800;
    assert(invoke() == nullptr && closes == 1 && parses == 0);
    reset(magic + "abc");
    std::string tooLong(1024, 'x');
    assert(invoke(tooLong.c_str()) == nullptr);
    assert(opens == 0 && closes == 0 && parses == 0 && warnings > 0);
    reset(magic + "abc");
    validInfo = false;
    assert(invoke() == nullptr && closes == 1 && parses == 0);
    reset(magic + "abc");
    acceptParse = false;
    assert(invoke() == nullptr && closes == 1 && parses == 1);
    reset(magic + "abc");
    assert(invoke() != nullptr && closes == 1 && parses == 1);
    reset("");
    std::puts("IW3_ORIGINAL_WEAPON_FILE_IO_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_WEAPON_LOADER */", original)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_weapon_file_io.cpp"
            exe = Path(tmp) / "original_weapon_file_io"
            cpp.write_text(fixture, encoding="utf-8")
            build = subprocess.run(
                [os.environ.get("CXX", "g++"), "-std=c++17", "-O1", "-g",
                 "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
                 str(cpp), "-o", str(exe)],
                capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            env = os.environ.copy()
            env["ASAN_OPTIONS"] = "detect_leaks=1"
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30, env=env)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_WEAPON_FILE_IO_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
