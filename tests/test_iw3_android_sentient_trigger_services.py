"""Regression tests for authentic sentient/path-node services on the ARM64 frame edge."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tools.iw3_android.prepare_real_engine_sentient_trigger_services import (
    DECLARATIONS,
    HEADER,
    REQUIRED,
    SIGNATURES,
    SOURCE,
    prepare,
)
from tools.iw3_android.prepare_g_runframe_prereqs import function_source

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "third_party/KisakCOD"


class OriginalSentientTriggerServiceTests(unittest.TestCase):
    def test_original_bodies_are_extracted_verbatim_and_hashed(self):
        source_path = ENGINE / SOURCE
        original = source_path.read_bytes()
        source = original.decode("utf-8")
        bodies = [function_source(source, signature) for signature in SIGNATURES]

        with TemporaryDirectory() as temp:
            output = Path(temp) / "sentient_trigger_services.cpp"
            report_path = Path(temp) / "sentient_services.json"
            report = prepare(ENGINE, output, report_path)
            generated = output.read_text(encoding="utf-8")
            saved_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(source_path.read_bytes(), original)
        for signature, body in zip(SIGNATURES, bodies):
            self.assertEqual(generated.count(signature), 1)
            self.assertIn(body, generated)
            self.assertEqual(
                report["function_body_sha256"][signature],
                hashlib.sha256(body.encode("utf-8")).hexdigest(),
            )
        self.assertEqual(saved_report, report)
        self.assertTrue(report["original_function_bodies_preserved_verbatim"])
        self.assertTrue(report["pathlocal_alignment_128_preserved"])
        self.assertFalse(report["actor_header_included"])
        self.assertTrue(report["no_stub_service_added"])
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["map_loaded"])
        self.assertFalse(report["gameplay_proven"])
        self.assertFalse(report["playable_apk"])

    def test_declarations_are_verified_against_original_headers(self):
        for relative_path, declaration in DECLARATIONS:
            with self.subTest(header=str(relative_path), declaration=declaration):
                self.assertIn(declaration, (ENGINE / relative_path).read_text(encoding="utf-8"))

    def test_pathnode_alignment_uses_portable_cxx_without_changing_alignment(self):
        header = (ENGINE / "src/game/pathnode.h").read_text(encoding="utf-8")
        self.assertIn("struct alignas(128) pathlocal_t", header)
        self.assertNotIn("struct __declspec(align(128)) pathlocal_t", header)
        self.assertIn("static_assert(alignof(pathlocal_t) == 128", HEADER)

    def test_generated_services_do_not_include_the_32bit_actor_layout_header(self):
        self.assertNotIn("#include <game/actor.h>", HEADER)
        self.assertIn("#define IW3_ANDROID_PORTABLE_PATHNODE_SERVICES 1", HEADER)
        self.assertIn("int __cdecl Path_IsValidClaimNode(const pathnode_t *node);", HEADER)
        pathnode_header = (ENGINE / "src/game/pathnode.h").read_text(encoding="utf-8")
        self.assertIn("#ifndef IW3_ANDROID_PORTABLE_PATHNODE_SERVICES", pathnode_header)
        self.assertIn("struct badplace_arc_t;", pathnode_header)
        self.assertIn('#include <client/client.h>', pathnode_header)
        self.assertIn("Path_IsValidClaimNode(node)", REQUIRED)

    def test_lp64_pathnode_tree_and_portable_actor_alignment_headers(self):
        pathnode = (ENGINE / "src/game/pathnode.h").read_text(encoding="utf-8")
        anim = (ENGINE / "src/game/actor_animapi.h").read_text(encoding="utf-8")
        game_local = (ENGINE / "src/game/g_local.h").read_text(encoding="utf-8")

        self.assertIn(
            "static_assert(sizeof(pathnode_tree_nodes_t) == (sizeof(void *) == 8 ? 16 : 8));",
            pathnode,
        )
        self.assertIn("static_assert(sizeof(pathnode_tree_info_t) == 2 * sizeof(void *));", pathnode)
        self.assertIn(
            "static_assert(sizeof(pathnode_tree_t) == (sizeof(void *) == 8 ? 24 : 16));",
            pathnode,
        )
        self.assertIn("struct alignas(4) scr_animscript_t", anim)
        self.assertNotIn("struct __declspec(align(4)) scr_animscript_t", anim)
        self.assertIn("static_assert(sizeof(scr_animscript_t) == 8);", anim)
        self.assertIn("static_assert(alignof(scr_animscript_t) == 4);", anim)
        self.assertIn("#include <server/server_frame.h>", game_local)
        self.assertIn("int __cdecl G_RunFrame(ServerFrameExtent extent, int timeCap);", game_local)

    def test_generator_refuses_to_overwrite_original_engine_source(self):
        with self.assertRaises(ValueError):
            prepare(ENGINE, ENGINE / SOURCE)

    def test_generator_rejects_missing_source(self):
        with TemporaryDirectory() as temp:
            with self.assertRaises((FileNotFoundError, OSError)):
                prepare(Path(temp), Path(temp) / "missing.cpp")


if __name__ == "__main__":
    unittest.main()
