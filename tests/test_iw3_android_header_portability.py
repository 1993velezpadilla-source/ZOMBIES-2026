"""Regression guards for original KisakCOD cross-translation-unit header dependencies."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalHeaderPortabilityTests(unittest.TestCase):
    def test_sp_server_public_pointer_api_forward_declares_client_t(self):
        header = (ENGINE / "src/server/sv_public.h").read_text(encoding="utf-8")
        forward = "struct client_t;"
        prototype = "void __cdecl SV_InitReliableCommandsForClient(client_t *cl);"
        self.assertEqual(header.count(forward), 1)
        self.assertLess(header.index(forward), header.index(prototype))
        self.assertIn("void __cdecl SV_AddReliableCommand(client_t *cl, int index, const char *cmd);", header)

    def test_g_local_declares_frame_extent_through_the_real_shared_header(self):
        header = (ENGINE / "src/game/g_local.h").read_text(encoding="utf-8")
        self.assertIn("#include <server/server_frame.h>", header)
        self.assertIn("int __cdecl G_RunFrame(ServerFrameExtent extent, int timeCap);", header)


if __name__ == "__main__":
    unittest.main()
