"""Guard the complete original IW3 command/filesystem/Dvar ARM64 link audit.

The output is an unresolved ELF object, never a playable Android engine.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/iw3-command-full-arm64.yml"
CMD = ROOT / "third_party/KisakCOD/src/qcommon/cmd.cpp"
FS = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"
DVAR = ROOT / "third_party/KisakCOD/src/universal/dvar.cpp"


class OriginalCommandFilesystemDvarLinkTests(unittest.TestCase):
    def test_three_authentic_source_units_and_cross_edges(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        cmd = CMD.read_text(encoding="utf-8")
        fs = FS.read_text(encoding="utf-8")
        dvar = DVAR.read_text(encoding="utf-8")

        self.assertIn('third_party/KisakCOD/src/qcommon/cmd.cpp', workflow)
        self.assertIn('"universal/com_files.cpp:$fs"', workflow)
        self.assertIn('"universal/dvar.cpp:$dvar"', workflow)
        self.assertIn('"$ndk/ld.lld" -m aarch64linux -r "$cmd" "$fs" "$dvar"', workflow)
        for symbol in (
            "Cmd_Init()", "Cmd_Argv(int)",
            "FS_FOpenFileRead(char const*, int*)", "Dvar_FindVar(char const*)",
        ):
            self.assertIn(symbol, workflow)
        self.assertIn('grep -F " U $symbol"', workflow)
        self.assertIn('test -s "$object_dir/iw3-original-cmd-files-dvar-undefined.txt"', workflow)
        self.assertIn("IW3_ORIGINAL_CMD_FS_DVAR_FULL_TU_RELOCATABLE_LINK_PASS", workflow)
        self.assertIn("IW3_ORIGINAL_ENGINE_RUNTIME_LINKED=false", workflow)
        self.assertIn("IW3_PLAYABLE_APK=false", workflow)
        self.assertIn("Cmd_Init()", cmd)
        self.assertIn("FS_FOpenFileRead(", cmd)
        self.assertIn("Dvar_FindVar(", cmd)
        self.assertIn("FS_FOpenFileRead(", fs)
        self.assertIn("Dvar_FindVar(", dvar)
        self.assertIn("Cmd_Argv(", dvar)

    def test_graph_objects_preserved_as_non_apk_evidence(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for name in (
            "iw3-original-com-files-full-aarch64.o",
            "iw3-original-dvar-full-aarch64.o",
            "iw3-original-cmd-files-dvar-aarch64.o",
            "iw3-original-cmd-files-dvar-elf.txt",
            "iw3-original-cmd-files-dvar-defined.txt",
            "iw3-original-cmd-files-dvar-undefined.txt",
        ):
            self.assertIn(name, workflow)
        self.assertIn("NOT APK", workflow)
        self.assertNotIn("IW3_PLAYABLE_APK=true", workflow)


if __name__ == "__main__":
    unittest.main()
