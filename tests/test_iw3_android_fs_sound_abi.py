import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPAT = ROOT / "android/iw3-native/iw3_android_filesystem_compat.h"
SOUND_PUBLIC = ROOT / "third_party/KisakCOD/src/sound/snd_public.h"
STOP_SOUNDS = ROOT / "third_party/KisakCOD/src/sound/snd_stopsounds.h"
COM_FILES = ROOT / "third_party/KisakCOD/src/universal/com_files.cpp"


class AndroidFilesystemSoundAbiTests(unittest.TestCase):
    def test_android_boundary_declares_the_original_shutdown_abi(self):
        compat = COMPAT.read_text(encoding="utf-8")
        public = SOUND_PUBLIC.read_text(encoding="utf-8")
        enum_header = STOP_SOUNDS.read_text(encoding="utf-8")
        source = COM_FILES.read_text(encoding="utf-8")

        signature = r"void\s+__cdecl\s+SND_StopSounds\s*\(\s*snd_stopsounds_arg_t\s+which\s*\)\s*;"
        self.assertRegex(compat, signature)
        self.assertRegex(public, signature)
        self.assertIn('#include <sound/snd_stopsounds.h>', compat)
        self.assertIn("SND_STOP_STREAMED", enum_header)
        self.assertIn('#include <sound/snd_stopsounds.h>', source)
        self.assertIn("SND_StopSounds(SND_STOP_STREAMED);", source)

    def test_android_boundary_does_not_fake_the_sound_implementation(self):
        compat = COMPAT.read_text(encoding="utf-8")
        self.assertNotRegex(
            compat,
            r"\bSND_StopSounds\s*\([^;]*\)\s*\{",
            "Android compatibility header must declare the original sound service, not stub it",
        )


if __name__ == "__main__":
    unittest.main()
