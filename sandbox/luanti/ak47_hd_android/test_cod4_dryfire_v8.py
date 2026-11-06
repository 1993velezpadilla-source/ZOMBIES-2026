"""Tests that dry fire really uses the original COD4 SMG click; no generic placeholder."""
import hashlib
import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
import make_cod4_dryfire_v8 as dry

class COD4DryFireTests(unittest.TestCase):
    def test_exact_ak47_player_field_and_pinned_sha(self):
        self.assertEqual(dry.PLAYER_ALIAS,"weap_dryfire_smg_plr")
        self.assertEqual(dry.ORIGINAL_WAV,"weap_dryfire_smg.wav")
        self.assertEqual(dry.ORIGINAL_SHA,"561963bfb073ee2b765ed2d3a1b0f8b6722124b87a8950a5170b05727c284c3f")
        self.assertLess(abs(dry.EXPECTED_SECONDS-.21626),.00001)

    def test_oggs_from_original_duration_without_stretch_or_wrong_player_alias(self):
        with tempfile.TemporaryDirectory() as root:
            folder=Path(root)
            original=folder/'loaded/common/sound/weapons/weap_dryfire_smg.wav'
            original.parent.mkdir(parents=True)
            sr=44100
            t=np.arange(round(dry.EXPECTED_SECONDS*sr))/sr
            source=(.32*np.sin(2*np.pi*967*t)+.17*np.sin(2*np.pi*2457*t)).astype('float32')
            sf.write(str(original),source,sr,subtype='PCM_16',format='WAV')
            sha=hashlib.sha256(original.read_bytes()).hexdigest()
            with patch.object(dry,'ORIGINAL_SHA',sha):
                report=dry.prepare(folder/'loaded',folder/'out')
            self.assertEqual(report['player_alias'],'weap_dryfire_smg_plr')
            self.assertTrue(report['original_pitch'])
            self.assertFalse(report['time_stretch_applied'])
            self.assertFalse(report['source_wav_bundled'])
            encoded,sr2=sf.read(str(folder/'out/ak47dev_dry.ogg'))
            self.assertEqual(sr,sr2)
            self.assertEqual(len(encoded),len(source))
            self.assertGreater(float(np.max(np.abs(encoded))),.10)
            audit=json.loads((folder/'out/ak47dev_dry_audit_v8.json').read_text())
            self.assertEqual(audit['output_sha256'],hashlib.sha256(
                (folder/'out/ak47dev_dry.ogg').read_bytes()).hexdigest())

    def test_missing_original_is_fatal_no_synthetic_backup(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                dry.prepare(Path(root),Path(root)/'out')


if __name__=='__main__':
    unittest.main()
