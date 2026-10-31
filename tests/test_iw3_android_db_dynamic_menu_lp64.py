"""Run the original DB_DynamicCloneMenu body with 64-bit menu/item pointers.

This is an isolated host regression of genuine KisakCOD code, NOT a game,
renderer, loaded map, or Android APK proof.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/database/db_registry.cpp"
SIGNATURE = "void __cdecl DB_DynamicCloneMenu(XAssetHeader from, XAssetHeader to, int32_t swag)"


class OriginalDatabaseMenuLP64Tests(unittest.TestCase):
    def test_original_dynamic_clone_uses_typed_menu_and_item_pointers(self):
        original = SOURCE.read_text(encoding="utf-8")
        body = function_source(original, SIGNATURE)
        self.assertIn("toMenu->window.staticFlags", body)
        self.assertIn("fromMenu->items[fromIndex]", body)
        self.assertIn("toMenu->items[toIndex]", body)
        self.assertIn("DB_RemoveWindowFocus(toWindow)", body)
        self.assertNotIn("xmodelPieces[", body)
        self.assertNotIn("4 * toIndex", body)
        self.assertNotIn("4 * fromIndex", body)

        fixture = r"""
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#define __cdecl
struct windowDef_t {
    const char *name = nullptr;
    int staticFlags = 0;
    int dynamicFlags[1]{};
};
struct itemDef_s { windowDef_t window; };
struct menuDef_t {
    windowDef_t window;
    int itemCount = 0;
    itemDef_s **items = nullptr;
};
union XAssetHeader {
    menuDef_t *menu;
    void *data;
};
void DB_RemoveWindowFocus(windowDef_t *window) {
    assert(window);
    window->dynamicFlags[0] &= ~2;
}
/* ORIGINAL_FUNCTION */
int main() {
    itemDef_s sourceA{{"alpha", 0, {6}}};
    itemDef_s sourceB{{"beta", 0, {13}}};
    itemDef_s *sourceItems[]{&sourceA, &sourceB};
    menuDef_t from{};
    from.window.staticFlags = 0x345;
    from.itemCount = 2;
    from.items = sourceItems;

    itemDef_s targetB{{"beta", 0, {2}}};
    itemDef_s targetUnmatched{{"gamma", 0, {7}}};
    itemDef_s targetA{{"alpha", 0, {3}}};
    itemDef_s targetUnnamed{{nullptr, 0, {2}}};
    itemDef_s *targetItems[]{&targetB, nullptr, &targetUnmatched, &targetA, &targetUnnamed};
    menuDef_t to{};
    to.window.staticFlags = 0;
    to.itemCount = 5;
    to.items = targetItems;

    DB_DynamicCloneMenu({&from}, {&to}, 0);
    assert(to.window.staticFlags == 0x345);
    assert(targetB.window.dynamicFlags[0] == (13 & ~2));
    assert(targetA.window.dynamicFlags[0] == (6 & ~2));
    assert(targetUnmatched.window.dynamicFlags[0] == (7 & ~2));
    assert(targetUnnamed.window.dynamicFlags[0] == 0);
    assert(sourceA.window.dynamicFlags[0] == 6);
    assert(sourceB.window.dynamicFlags[0] == 13);

    // Bad menu/list pointers and negative counts must not dereference memory.
    menuDef_t invalid{};
    invalid.itemCount = 1;
    invalid.items = nullptr;
    DB_DynamicCloneMenu({&invalid}, {&to}, 0);
    DB_DynamicCloneMenu({&from}, {&invalid}, 0);
    DB_DynamicCloneMenu({nullptr}, {&to}, 0);
    DB_DynamicCloneMenu({&from}, {nullptr}, 0);
    invalid.itemCount = -1;
    DB_DynamicCloneMenu({&invalid}, {&to}, 0);
    assert(to.window.staticFlags == 0x345);

    std::puts("IW3_ORIGINAL_DB_DYNAMIC_MENU_LP64_PASS");
}
"""
        fixture = fixture.replace("/* ORIGINAL_FUNCTION */", body)
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / "original_db_menu_lp64.cpp"
            exe = Path(temp) / "original_db_menu_lp64"
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
                [str(exe)], capture_output=True, text=True, timeout=30, env=env
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn("IW3_ORIGINAL_DB_DYNAMIC_MENU_LP64_PASS", run.stdout)


if __name__ == "__main__":
    unittest.main()
