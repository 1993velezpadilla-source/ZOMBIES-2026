"""Keep the authentic SP game-state headers independent of the D3D client."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD/src"


class PortableSinglePlayerGameHeaderTests(unittest.TestCase):
    def test_game_public_does_not_import_server_or_d3d_client_headers(self):
        header = (ENGINE / "game/game_public.h").read_text(encoding="utf-8")
        self.assertIn("#include <game/g_client.h>", header)
        self.assertIn("#include <qcommon/ent.h>", header)
        self.assertNotIn("#include <server/server.h>", header)

    def test_shared_gclient_record_is_defined_once_and_server_reuses_it(self):
        client_header = (ENGINE / "game/g_client.h").read_text(encoding="utf-8")
        server_header = (ENGINE / "server/server.h").read_text(encoding="utf-8")
        self.assertEqual(client_header.count("struct gclient_s"), 1)
        self.assertEqual(client_header.count("struct clientPersistent_t"), 1)
        self.assertIn("#include <game/g_client.h>", server_header)
        self.assertNotIn("struct gclient_s", server_header)
        self.assertNotIn("struct clientPersistent_t", server_header)
        self.assertNotIn("enum clientConnected_t", server_header)

    def test_shared_record_preserves_fields_used_by_original_trigger_update(self):
        header = (ENGINE / "game/g_client.h").read_text(encoding="utf-8")
        expected_fields = [
            "playerState_s ps;",
            "int noclip;",
            "int ufo;",
            "bool playerMoved;",
        ]
        positions = [header.index(field) for field in expected_fields]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("gentity_s *pHitHitEnt;", header)
        self.assertIn("EntHandle pLookatEnt;", header)
        self.assertIn("EntHandle useHoldEntity;", header)

    def test_shared_client_header_has_no_renderer_or_server_dependency(self):
        header = (ENGINE / "game/g_client.h").read_text(encoding="utf-8")
        for forbidden in ("server/server.h", "client/client.h", "gfx_d3d/"):
            self.assertNotIn(forbidden, header)

    def test_pointer_bearing_sp_registry_records_keep_32bit_and_lp64_layouts(self):
        header = (ENGINE / "game/game_public.h").read_text(encoding="utf-8")
        expected = {
            "client_fields_s": ("0x20", "0x14"),
            "VehicleLocalPhysics": ("0x38", "0x34"),
            "game_hudelem_field_t": ("0x28", "0x1C"),
        }
        guard = "#if defined(__LP64__) || defined(_LP64) || defined(_WIN64)"
        for name, (lp64_size, win32_size) in expected.items():
            with self.subTest(name=name):
                block = (
                    guard + "\n"
                    + f"static_assert(sizeof({name}) == {lp64_size});" + "\n"
                    + "#else\n"
                    + f"static_assert(sizeof({name}) == {win32_size});" + "\n"
                    + "#endif"
                )
                self.assertIn(block, header)

    def test_arm64_gate_still_compiles_original_trigger_body_not_a_stub(self):
        workflow = (ROOT / ".github/workflows/iw3-original-native-android.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_real_engine_g_update_player_triggers.py", workflow)
        self.assertIn("iw3_g_update_player_triggers.cpp", workflow)
        self.assertIn("G_UpdatePlayerTriggers(gentity_s*)", workflow)
        self.assertIn("IW3_GAMEPLAY_PROVEN=false", workflow)


if __name__ == "__main__":
    unittest.main()
