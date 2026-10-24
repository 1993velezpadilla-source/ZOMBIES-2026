"""Verify source-specific diagnostic patching without building or running the game.

Only three GPL source files are copied into a disposable test directory;
the pinned KisakCOD source tree is never mutated.
"""
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.iw3_rotu.instrument_early_breakpoint import patch

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party" / "KisakCOD"
PATHS = (
    "src/win32/win_main.cpp",
    "src/database/db_registry.cpp",
    "src/client_mp/cl_main_pc_mp.cpp",
)


class TemporaryClientInstrumentationTest(unittest.TestCase):
    def test_injects_precise_checkpoints_without_auth_bypass(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            for relative in PATHS:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(UPSTREAM / relative, destination)

            patch(root)
            client = (root / PATHS[2]).read_text(encoding="utf-8")
            self.assertIn('Z2026_TraceStage("SV_FRAME_ENTER", 0);\n            SV_Frame(0);', client)
            self.assertIn('Z2026_TraceStage("NET_RESOLVE_ENTER", 0);\n            if (NET_StringToAdr(', client)
            self.assertIn('Z2026_TraceStage("AUTH_GATE_ENTER", (int)clc->serverAddress.type);', client)
            self.assertIn('Z2026_TraceStage("STEAM_TICKET_ENTER", 0);\n    const bool ticketOk', client)
            self.assertIn("const bool ticketOk = Steam_UpdateClientAuthTicket(addr);", client)
            self.assertIn("return ticketOk;", client)
            self.assertIn("Z2026_TraceProfile(Com_HasPlayerProfile())", client)
            self.assertEqual(
                client.count("Steam_UpdateClientAuthTicket(addr)"), 1,
                "Ticket validation call must remain in the same route",
            )
            self.assertNotIn("return true; // bypass", client)
            # Catch accidental literal backslash+n in an injected C++ statement.
            self.assertNotIn('SV_FRAME_ENTER", 0);\\n', client)
            with self.assertRaises(ValueError):
                patch(root)

    def test_never_changes_original_vendor(self):
        original = (UPSTREAM / PATHS[2]).read_text(encoding="utf-8")
        self.assertNotIn("Z2026_TraceStage", original)


if __name__ == "__main__":
    unittest.main()
