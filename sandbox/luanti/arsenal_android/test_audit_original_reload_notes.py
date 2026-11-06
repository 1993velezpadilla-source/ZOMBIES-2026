"""Regression tests for original reload timing/audio note comparisons."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audit_original_reload_notes import analyze


class FakeXanim:
    def __init__(self, name):
        self.name=name
        self.fps=30
        self.frame_count=106 if "_empty" in name else 83
        self.notes=[("lift",0),("magazine_out",19),("magazine_in",57)]
        if "_empty" in name:
            self.notes.append(("chamber",77))


def decoder(path):
    return FakeXanim(path.stem)


def manifest():
    return {"weapons":[{"id":"ak47","model_aliases":["viewmodel_ak47"]}]+[
        {"id":f"gun{i}","model_aliases":[f"viewmodel_gun{i}"]}
        for i in range(27)]}


class OriginalReloadNoteTests(unittest.TestCase):
    def test_original_empty_chamber_not_in_tactical_reload(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            xanim=root/"common_mp/xanim"
            xanim.mkdir(parents=True)
            for name in ("viewmodel_ak47_reload.xanim_bin",
                         "viewmodel_ak47_reload_empty.xanim_bin"):
                (xanim/name).write_bytes(b"real-dump-placeholder-mocked-reader")
            report=analyze(root,manifest(),decoder)
            self.assertEqual(report["both_original_reload_xanims_found"],1)
            self.assertEqual(report["native_sound_event_difference_confirmed"],1)
            r=report["original_source_notetracks"]["ak47"]
            self.assertEqual(r["empty_only_notes"],[("chamber",77)])
            self.assertFalse(r["sound_ogg_baked"])
            self.assertFalse(report["actual_audio_rendered"])

    def test_only_normal_reload_must_not_claim_empty_audio(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            xanim=root/"common_mp/xanim"
            xanim.mkdir(parents=True)
            (xanim/"viewmodel_ak47_reload.xanim_bin").write_bytes(b"mock")
            report=analyze(root,manifest(),decoder)
            self.assertEqual(report["both_original_reload_xanims_found"],0)
            self.assertEqual(report["native_sound_event_difference_confirmed"],0)

    def test_no_source_cannot_claim_distinct_audio(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            (root/"common_mp/xanim").mkdir(parents=True)
            report=analyze(root,manifest(),decoder)
            self.assertEqual(report["native_sound_event_difference_confirmed"],0)

    def test_wrong_catalog_count_fails(self):
        with TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"28 source weapon"):
                analyze(Path(d),{"weapons":[]},decoder)


if __name__=="__main__":
    unittest.main()
