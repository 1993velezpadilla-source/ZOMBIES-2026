"""Guard the genuine IW3 Com_Init ARM64 dependency-link audit.

The audit links real upstream objects only; it must never report a playable APK.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/iw3-command-full-arm64.yml"


class BootstrapGraphAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.step = cls.workflow.split(
            "- name: Link authentic Com_Init with original command, dvar and filesystem units (NOT GAME)",
            1,
        )[1].split("- name: Preserve command-system portability evidence (NOT APK)", 1)[0]

    def test_compiles_real_common_source_not_generated_bootstrap(self):
        self.assertIn('-c "$root/qcommon/common.cpp" -o "$common"', self.step)
        self.assertIn('IW3_ANDROID_DISABLE_SCRIPT_DEBUGGER=1', self.step)
        self.assertIn('IW3_ANDROID_COMMON_HEADER_ONLY_OPENAL=1', self.step)

    def test_links_all_four_complete_original_objects(self):
        self.assertIn(
            '-r "$common" "$cmd" "$fs" "$dvar" -o "$combined"', self.step
        )
        for symbol in ("Com_Init(char*)", "Com_Frame()", "Cmd_Init()", "Dvar_Init()"):
            self.assertIn(symbol, self.step)
        self.assertIn("IW3_ORIGINAL_COMMON_CMD_FILES_DVAR_RELOCATABLE_LINK_PASS", self.step)

    def test_resolves_original_fs_bootstrap_provider_without_claiming_game(self):
        self.assertIn("FS_InitFilesystem()", self.step)
        self.assertIn("FS_Startup(char*)", self.step)
        self.assertIn("IW3_ORIGINAL_FS_INITFILESYSTEM_PROVIDER_RESOLVED", self.step)
        self.assertIn("IW3_ORIGINAL_SYS_GETVALUE_RUNTIME_PROVIDER_MISSING", self.step)
        self.assertIn("IW3_ORIGINAL_CL_INITRENDERER_RUNTIME_PROVIDER_MISSING", self.step)
        self.assertIn("IW3_COMMON_BOOTSTRAP_RUNTIME_LINKED=false", self.step)
        self.assertIn("IW3_PLAYABLE_APK=false", self.step)
        self.assertNotIn("IW3_PLAYABLE_APK=true", self.step)

    def test_retains_link_artifacts(self):
        for artifact in (
            "iw3-original-common-full-aarch64.o",
            "iw3-original-common-cmd-files-dvar-aarch64.o",
            "iw3-original-bootstrap-graph-defined.txt",
            "iw3-original-bootstrap-graph-undefined.txt",
        ):
            self.assertIn(artifact, self.workflow)


if __name__ == "__main__":
    unittest.main()
