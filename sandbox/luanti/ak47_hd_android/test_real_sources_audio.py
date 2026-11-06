"""End-to-end mono/stereo and 44.1k/48k input test BEFORE downloading COD4."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from make_reload_audio import prepare


class SourceAudioFormatTest(unittest.TestCase):
    def test_realistic_mismatched_samplerate_and_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod=Path(tmp); folder=mod/'sounds';folder.mkdir(parents=True)
            rng=np.random.default_rng(20261106)
            # AK full reload is about 2.318 seconds, actual source stereo.
            source=rng.normal(0,.06,(round(2.318481*44100),2)).astype('float32')
            # Independent mechanical click recording is higher sample rate
            # and mono; don't change its duration or tone.
            bolt=rng.normal(0,.15,(round(.893*48000),1)).astype('float32')
            sf.write(folder/'ak47dev_reload.ogg',source,44100,format='OGG',subtype='VORBIS')
            sf.write(folder/'ak47dev_bolt.ogg',bolt,48000,format='OGG',subtype='VORBIS')
            report=prepare(mod)
            self.assertEqual(set(report['variants']),{'normal','empty'})
            normal=report['variants']['normal'];empty=report['variants']['empty']
            self.assertTrue(normal['pitch_unchanged'] and empty['pitch_unchanged'])
            self.assertFalse(normal['time_stretch_applied'] or empty['time_stretch_applied'])
            self.assertEqual(normal['extra_bolt_samples'],0)
            self.assertGreater(empty['extra_bolt_samples'],0)
            self.assertAlmostEqual(sf.info(folder/'ak47dev_reload_normal.ogg').duration,83/30,places=2)
            self.assertAlmostEqual(sf.info(folder/'ak47dev_reload_empty.ogg').duration,106/30,places=2)


if __name__=='__main__':
    unittest.main()
