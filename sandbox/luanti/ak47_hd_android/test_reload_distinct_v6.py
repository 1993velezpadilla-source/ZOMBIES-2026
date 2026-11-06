"""Regression for the user-observed V5 bug: both reload OGGs shared audio."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from make_reload_distinct_v6 import (
    prepare,independent_normal, NORMAL_SOURCE_PAGE,
    NORMAL_SOURCE_URL,EMPTY_SOURCE_URL,DURATIONS
)


def as_wav(samples,rate):
    data=io.BytesIO()
    sf.write(data,samples,rate,format='WAV',subtype='PCM_16')
    return data.getvalue()


class DistinctSourceReloadTest(unittest.TestCase):
    def _different_sound_sources(self,base):
        rate=44100
        t=np.arange(round(2.318481*rate))/rate
        # Two DIFFERENT natural recordings with realistic broadband noise.
        # A pure synthesized sine wave compresses under 10KB in Vorbis,
        # unlike actual reload Foley and triggers the valid-size guard.
        rng=np.random.default_rng(7612)
        empty=rng.normal(0,.06,(len(t),2)).astype(np.float32)
        empty[:,0]+=.21*np.sin(2*np.pi*410*t)
        empty[:,1]+=.20*np.sin(2*np.pi*550*t)
        bolt_rate=48000
        bt=np.arange(round(.892*bolt_rate))/bolt_rate
        bolt=np.sin(2*np.pi*1460*bt)[:,None].astype('float32')*.18
        normal_time=np.arange(round(2.0*rate))/rate
        # NORMAL: independently recorded waveform, unlike GunLib empty.
        normal=(np.sin(2*np.pi*1700*normal_time)[:,None]*.22+
                rng.normal(0,.055,(len(normal_time),1))).astype(np.float32)
        normal=np.pad(normal,((int(.07*rate),0),(0,0)))
        sounds=base/'sounds'
        sounds.mkdir(parents=True)
        sf.write(sounds/'ak47dev_reload.ogg',empty,rate,format='OGG',subtype='VORBIS')
        sf.write(sounds/'ak47dev_bolt.ogg',bolt,bolt_rate,format='OGG',subtype='VORBIS')
        return as_wav(normal,rate)

    def test_normal_and_empty_have_independent_recordings_and_correct_clocks(self):
        with tempfile.TemporaryDirectory() as d:
            mod=Path(d)
            src=self._different_sound_sources(mod)
            with patch('make_reload_distinct_v6.normal_source_bytes',return_value=src):
                report=prepare(mod)
            self.assertNotEqual(report['source_normal']['sha256'],report['source_empty']['sha256'])
            self.assertEqual(report['normal']['source_provenance'],NORMAL_SOURCE_PAGE)
            self.assertEqual(report['normal']['source_name'],'assaultriflereload1_0.wav')
            self.assertEqual(report['empty']['source_provenance'],'CC0 GunLib ak47_reload.ogg + ak47_click.ogg')
            self.assertFalse(report['normal']['shared_source_with_empty'])
            self.assertEqual(report['normal']['time_stretch_applied'],False)
            self.assertEqual(report['normal']['pitch_unchanged'],True)
            self.assertEqual(report['empty']['extra_bolt_samples']>0,True)
            for name,seconds in DURATIONS.items():
                path=mod/'sounds'/f'ak47dev_reload_{name}.ogg'
                self.assertTrue(path.exists())
                self.assertAlmostEqual(sf.info(path).duration,seconds,places=2)
            report_on_disk=json.loads((mod/'sounds'/'ak47dev_reload_audit_v6.json').read_text())
            self.assertNotEqual(report_on_disk['normal']['source_provenance'],
                                report_on_disk['empty']['source_provenance'])
            n,_=sf.read(mod/'sounds'/'ak47dev_reload_normal.ogg',always_2d=True)
            e,_=sf.read(mod/'sounds'/'ak47dev_reload_empty.ogg',always_2d=True)
            self.assertGreater(float(np.std(n)),.035)
            self.assertGreater(float(np.std(e)),.035)
            self.assertFalse(np.allclose(n[:1000,0],e[:1000,0],atol=.01),
                             'user reported identical source in both reloads')

    def test_v5_generator_still_uses_same_base_source_and_must_not_be_called(self):
        # Documentation for the repeated bug, guard the newly installed
        # runtime against accidentally regressing back to the old generator.
        src=(Path(__file__).parent/'patch_engine.py').read_text()
        self.assertIn('from make_reload_distinct_v6 import prepare',src)
        self.assertNotIn('from make_reload_audio import prepare as make_reload_audio',src)
        self.assertIn('assaultriflereload1_0.wav',Path(__file__).with_name('make_reload_distinct_v6.py').read_text())

    def test_normal_is_not_allowed_to_stretch_or_pull_empty_source(self):
        rate=44100
        normal=np.cos(np.arange(round(2.*rate))/rate*1000)[:,None].astype('float32')*.2
        pcm,meta=independent_normal(normal,rate)
        self.assertEqual(len(pcm),round(DURATIONS['normal']*rate))
        self.assertFalse(meta['time_stretch_applied'])
        self.assertEqual(meta['played_source_frames'],len(normal))
        self.assertEqual(meta['source_name'],'assaultriflereload1_0.wav')


if __name__=="__main__":unittest.main()
