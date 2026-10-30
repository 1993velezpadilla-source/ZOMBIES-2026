"""Regression tests for 64-bit string dvar pointers in original KisakCOD FS."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
BG_WEAPONS_SOURCE = ROOT / "third_party/KisakCOD/src/bgame/bg_weapons.cpp"
STRING_DVARS = (
    "fs_homepath",
    "fs_basepath",
    "fs_cdpath",
    "fs_basegame",
    "fs_gameDirVar",
)


class OriginalFilesystemStringDvarABITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_string_values_never_travel_through_32_bit_integer_member(self):
        for name in STRING_DVARS:
            with self.subTest(dvar=name):
                self.assertNotRegex(
                    self.source, rf"\b{name}->(?:current|reset)\.integer\b"
                )
                self.assertIn(f"{name}->current.string", self.source)

    def test_startup_uses_native_width_string_pointers(self):
        startup_start = self.source.index("void __cdecl FS_Startup(char *gameName)")
        startup_end = self.source.index("void __cdecl FS_InitFilesystem()", startup_start)
        startup = self.source[startup_start:startup_end]
        self.assertIn("fs_basepath->current.string[0] != '\\0'", startup)
        self.assertIn("fs_homepath->current.string[0] != '\\0'", startup)
        self.assertIn("FS_AddLocalizedGameDirectory((char *)fs_basepath->current.string", startup)
        self.assertNotIn("current.integer", startup)

    def test_open_and_init_paths_keep_string_pointer_width(self):
        open_start = self.source.index(
            "uint32_t __cdecl FS_FOpenFileReadForThread("
        )
        open_end = self.source.index("\n}\n", open_start) + 3
        open_body = self.source[open_start:open_end]
        self.assertIn("FS_BuildOSPathForThread((char*)fs_basepath->current.string", open_body)
        self.assertNotIn("fs_basepath->current.integer", open_body)

        init_start = self.source.index("void __cdecl FS_InitFilesystem()")
        init_end = self.source.index("uint32_t __cdecl FS_FOpenFileByMode", init_start)
        init_body = self.source[init_start:init_end]
        self.assertIn("lastValidBase, (char *)fs_basepath->current.string", init_body)
        self.assertIn("lastValidGame, (char *)fs_gameDirVar->current.string", init_body)

    def test_homepath_default_uses_native_width_reset_string_pointer(self):
        self.assertIn("homePath = (char *)fs_basepath->reset.string;", self.source)
        self.assertNotIn("fs_basepath->reset.integer", self.source)

    def test_game_directory_validator_never_truncates_string_pointers(self):
        start = self.source.index(
            "bool __cdecl FS_GameDirDomainFunc(dvar_s *dvar, DvarValue newValue)"
        )
        end = self.source.index("\nvoid FS_RegisterDvars()", start)
        body = self.source[start:end]
        self.assertIn("if (!newValue.string[0])", body)
        self.assertIn("newValue.string[4] != '/'", body)
        self.assertIn('strstr(newValue.string, "..")', body)
        self.assertIn('strstr(newValue.string, "::")', body)
        self.assertNotIn("newValue.integer", body)
        self.assertNotIn("(int)strstr", body)

    def test_numeric_debug_dvar_stays_numeric(self):
        self.assertIn("fs_debug->current.integer", self.source)


    def test_bgame_weapon_paths_use_native_width_game_directory_string(self):
        source = BG_WEAPONS_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("fs_gameDirVar->current.integer", source)

        shutdown_start = source.index("void __cdecl BG_ShutdownWeaponDefFiles()")
        shutdown_end = source.index("\nvoid __cdecl BG_ClearWeaponDef()", shutdown_start)
        shutdown = source[shutdown_start:shutdown_end]
        self.assertIn(r"fs_gameDirVar->current.string[0] != '\0'", shutdown)
        self.assertNotIn("current.integer", shutdown)

        load_start = source.index("WeaponDef *__cdecl BG_LoadWeaponDef(const char *name)")
        load_end = source.index("\nWeaponDef *__cdecl BG_LoadWeaponDef_FastFile", load_start)
        load = source[load_start:load_end]
        self.assertIn(r"fs_gameDirVar->current.string[0] != '\0' || !IsFastFileLoad()", load)
        self.assertNotIn("fs_gameDirVar->current.integer", load)

        # This neighboring dvar is numeric and must continue using integer.
        self.assertIn("player_adsExitDelay->current.integer", source)

    def test_bgame_weapon_source_has_an_arm64_compile_gate(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("Compile original BGame weapon loader for Android ARM64 (NOT RUNTIME)", workflow)
        self.assertIn("IW3_ORIGINAL_BGAME_WEAPONS_AARCH64_OBJECT_PASS", workflow)
        self.assertIn("IW3_BG_WEAPONS_RUNTIME_LINKED=false", workflow)

    def test_original_melee_dvar_registration_resolves_against_original_dvar_object(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("IW3_ORIGINAL_BGAME_MELEE_DVARS_DVAR_REGISTER_FLOAT_EDGE_RESOLVED_AARCH64_GREEN", workflow)
        self.assertIn("libiw3_sp_dvar_android.a", workflow)


if __name__ == "__main__":
    unittest.main()
