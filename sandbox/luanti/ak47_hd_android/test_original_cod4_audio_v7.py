"""Catch the exact user complaint: chamber/empty sound must NEVER play in tactical."""
import unittest
from pathlib import Path
import numpy as np
from types import SimpleNamespace

from make_original_cod4_reload_v7 import (
    EXPECTED,SOUNDS,RATE,_render
)

class OriginalCOD4ReloadUnit(unittest.TestCase):
    def setUp(self):
        # Fake foley is test data, NOT game audio. Each cue gets unique frequency.
        duration={'lift':.33,'clipout':1.08,'clipin':.696,'chamber':.726}
        frequencies={'lift':201,'clipout':387,'clipin':611,'chamber':959}
        self.signals={}
        for alias in SOUNDS:
            kind=next(k for k in duration if k in alias)
            t=np.arange(round(duration[kind]*RATE))/RATE
            self.signals[alias]=(.20*np.sin(2*np.pi*frequencies[kind]*t)).astype(np.float32)

    def test_exact_native_original_frames(self):
        self.assertEqual(EXPECTED['normal'][2],[('weap_ak47_lift_plr',0),
            ('weap_ak47_clipout_plr',19),('weap_ak47_clipin_plr',57)])
        self.assertEqual(EXPECTED['empty'][2],EXPECTED['normal'][2]+[
            ('weap_ak47_chamber_plr',77)])
        for kind,(name,frames,notes) in EXPECTED.items():
            anim=SimpleNamespace(fps=30,frame_count=frames)
            pcm,events=_render(self.signals,anim,notes,frames)
            self.assertEqual(len(pcm),round(frames/30*RATE))
            self.assertEqual([e['frame'] for e in events],
                             [n[1] for n in notes])
            self.assertEqual('chamber' in ''.join(e['alias'] for e in events),
                             kind=='empty')
            self.assertEqual(len(events),3 if kind=='normal' else 4)

    def test_normal_is_silent_at_empty_only_chamber(self):
        anim=SimpleNamespace(fps=30)
        normal,_=_render(self.signals,anim,EXPECTED['normal'][2],83)
        empty,_=_render(self.signals,anim,EXPECTED['empty'][2],106)
        a,b=round(2.67*RATE),round(2.87*RATE)
        self.assertLess(float(np.max(np.abs(normal[a:b]))),.00001)
        self.assertGreater(float(np.max(np.abs(empty[a:b]))),.10)

    def test_no_external_or_same_full_reload_generator_in_patch(self):
        code=Path(__file__).with_name('patch_engine.py').read_text()
        self.assertNotIn('make_reload_audio(mod)',code)
        self.assertNotIn('make_reload_distinct_v6 import prepare',code)
        self.assertIn("shutil.copy2(assets/'sounds'/original",code)


if __name__=='__main__':
    unittest.main()
