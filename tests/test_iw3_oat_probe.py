"""Small static contracts for an original, license-safe IW3 fastfile probe."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'tools' / 'iw3_rotu' / 'oat_probe'


class Iw3OatProbeTest(unittest.TestCase):
    def test_zone_is_explicit_iw3_and_only_one_rawfile(self):
        zone = (ROOT / 'zone_source/zombies_iw3_probe.zone').read_text('utf-8')
        parts = [line.strip() for line in zone.splitlines() if line.strip() and not line.startswith('//')]
        self.assertEqual(parts, ['>game,IW3', '>name,zombies_iw3_probe', 'rawfile,zombies2026/probe.txt'])

    def test_rawfile_is_self_authored_and_non_binary(self):
        raw = ROOT / 'zone_raw/zombies_iw3_probe/zombies2026/probe.txt'
        self.assertTrue(raw.is_file())
        data = raw.read_bytes()
        self.assertLess(len(data), 1024)
        self.assertTrue(data.startswith(b'ZOMBIES-2026 IW3 original fastfile smoke test.'))
        self.assertNotIn(b'\\x00', data)

    def test_no_asset_models_or_other_game_data_in_probe(self):
        forbidden = {'.ff', '.iwd', '.dll', '.exe', '.apk', '.iwi', '.xmodel_export', '.wav', '.ogg'}
        files = [p for p in ROOT.rglob('*') if p.is_file()]
        self.assertEqual(len(files), 2)
        self.assertFalse([p for p in files if p.suffix.lower() in forbidden])


if __name__ == '__main__':
    unittest.main()
