"""Exercise the authentic IW3 surface-sound allocator on LP64 under ASan/UBSan.

The function body is extracted verbatim from KisakCOD. Test providers replace
engine services; this is not an Android runtime or gameplay demonstration.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons_load_obj.cpp"
SIGNATURE = "snd_alias_list_t **__cdecl BG_RegisterSurfaceTypeSounds("


class OriginalWeaponNativeAllocationsTests(unittest.TestCase):
    def test_native_surface_pointer_array_has_29_full_width_slots(self):
        source = SOURCE.read_text(encoding="utf-8")
        original = function_source(source, SIGNATURE)
        self.assertIn("sizeof(*result) * 29", original)
        self.assertNotIn("Hunk_AllocLow(0x74u", original)
        self.assertIn(
            'Hunk_AllocLow(sizeof(WeaponDef), "BG_LoadWeaponDefInternal", 9)',
            source,
        )
        fixture = r"""
#include <cassert>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <vector>
#define __cdecl
#define iassert(x) assert(x)
constexpr int ERR_DROP = 1;
struct snd_alias_list_t { int id; };
struct SurfaceEntry {
    char *surfaceSoundBase;
    snd_alias_list_t **soundAliasList;
};
static SurfaceEntry surfaceTypeSoundLists[16]{};
static int surfaceTypeSoundListCount = 0;
static snd_alias_list_t defaultAlias{42}, regularAlias{43};
static char surfaceNames[29][16]{};
static std::vector<void*> allocations;
static std::vector<size_t> sizes;
void* Hunk_AllocLow(size_t bytes, const char*, int) {
    void* p = std::calloc(1, bytes);
    assert(p);
    allocations.push_back(p);
    sizes.push_back(bytes);
    return p;
}
int I_strcmp(const char* a, const char* b) { return std::strcmp(a, b); }
void Com_Error(int, const char*, ...) { throw std::runtime_error("limit"); }
int Com_sprintf(char* dst, int capacity, const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    const int n = std::vsnprintf(dst, static_cast<size_t>(capacity), fmt, args);
    va_end(args);
    return n;
}
const char* Com_SurfaceTypeToName(int i) {
    assert(i >= 0 && i < 29);
    return surfaceNames[i];
}
snd_alias_list_t* Com_FindSoundAlias(const char* name) {
    if (std::strcmp(name, "metal_5") == 0) return nullptr;
    const size_t n = std::strlen(name);
    if (n >= 8 && std::strcmp(name + n - 8, "_default") == 0)
        return &defaultAlias;
    return &regularAlias;
}
/* ORIGINAL_FUNCTION */
int main() {
    static_assert(sizeof(void*) == 8, "LP64 pointer-width test");
    for (int i = 0; i < 29; ++i)
        std::snprintf(surfaceNames[i], sizeof(surfaceNames[i]), "%d", i);
    assert(BG_RegisterSurfaceTypeSounds("") == nullptr);
    assert(surfaceTypeSoundListCount == 0);
    auto** metal = BG_RegisterSurfaceTypeSounds("metal");
    assert(metal && surfaceTypeSoundListCount == 1);
    assert(sizes[0] == 29 * sizeof(snd_alias_list_t*));
    for (int i = 0; i < 29; ++i)
        assert(metal[i] == (i == 5 ? &defaultAlias : &regularAlias));
    const size_t prior = allocations.size();
    assert(BG_RegisterSurfaceTypeSounds("metal") == metal);
    assert(allocations.size() == prior && surfaceTypeSoundListCount == 1);
    assert(BG_RegisterSurfaceTypeSounds("stone") != metal);
    assert(surfaceTypeSoundListCount == 2);
    for (int i = 2; i < 16; ++i) {
        char name[24];
        std::snprintf(name, sizeof(name), "surface_%d", i);
        assert(BG_RegisterSurfaceTypeSounds(name) != nullptr);
    }
    assert(surfaceTypeSoundListCount == 16);
    bool limitCaught = false;
    try { (void)BG_RegisterSurfaceTypeSounds("seventeenth"); }
    catch (const std::runtime_error&) { limitCaught = true; }
    assert(limitCaught);
    assert(surfaceTypeSoundListCount == 16);
    for (void* p : allocations) std::free(p);
    std::puts("IW3_ORIGINAL_SURFACE_SOUND_LP64_ALLOC_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_FUNCTION */", original)
        with tempfile.TemporaryDirectory() as tmp:
            cpp = Path(tmp) / "original_surface_sound_lp64.cpp"
            exe = Path(tmp) / "original_surface_sound_lp64"
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
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=30, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_SURFACE_SOUND_LP64_ALLOC_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
