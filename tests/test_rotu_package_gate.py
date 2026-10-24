"""Synthetic source-only manifest tests; no game files are used."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'tools' / 'iw3_rotu' / 'package_gate.py'
spec = importlib.util.spec_from_file_location('package_gate', SOURCE)
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)


class PackageGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'mod.csv').write_text(
            '// include,mod_scripts\n'
            'rawfile,maps/mp/gametypes/surv.gsc\n'
            'xmodel,fictional_zombie\n'
            'fx,fictional_attack\n', encoding='utf-8')
        (self.root / 'mod_scripts.csv').write_text(
            'rawfile,scripts/bots/_bots.gsc\n'
            'rawfile,scripts/include/waypoints.gsc\n',
            encoding='utf-8')
        self.files = {
            'mod.csv', 'mod_scripts.csv',
            'maps/mp/gametypes/surv.gsc',
            'scripts/bots/_bots.gsc', 'scripts/include/waypoints.gsc',
        }

    def test_staging_enables_commented_script_include(self):
        stage = self.root / 'temporary-overlay'
        result = pkg.audit(self.root, self.files, stage)
        self.assertTrue(result['staging_source_ready'])
        self.assertFalse(result['mod_scripts_include_originally_active'])
        self.assertEqual(result['staging_overlay_status'], 'activated_in_overlay')
        self.assertIn('include,mod_scripts\n', (stage / 'mod.csv').read_text())
        self.assertNotIn('// include,mod_scripts', (stage / 'mod.csv').read_text())
        self.assertEqual((stage / 'mod_scripts.csv').read_text(),
                         (self.root / 'mod_scripts.csv').read_text())
        self.assertFalse(result['mod_fastfile_compiled'])
        self.assertFalse(result['asset_dependencies_verified'])
        self.assertFalse(result['live_zombie_verified'])

    def test_unresolved_gametype_stops_staging_pass(self):
        self.files.remove('maps/mp/gametypes/surv.gsc')
        report = pkg.audit(self.root, self.files)
        self.assertFalse(report['staging_source_ready'])
        self.assertEqual(report['unresolved_gametype_script_paths'],
                         ['maps/mp/gametypes/surv.gsc'])

    def test_missing_bot_script_stops_staging_pass(self):
        self.files.remove('scripts/bots/_bots.gsc')
        self.assertFalse(pkg.audit(self.root, self.files)['staging_source_ready'])

    def test_double_active_include_rejected(self):
        (self.root / 'mod.csv').write_text('include,mod_scripts\ninclude,mod_scripts\n', encoding='utf-8')
        report = pkg.audit(self.root, self.files, self.root / 'stage')
        self.assertIsNotNone(report['staging_error'])
        self.assertFalse(report['staging_source_ready'])
        self.assertFalse((self.root / 'stage' / 'mod.csv').exists())

    def test_already_active_is_idempotent(self):
        (self.root / 'mod.csv').write_text(
            'include,mod_scripts\nrawfile,maps/mp/gametypes/surv.gsc\n', encoding='utf-8')
        report = pkg.audit(self.root, self.files)
        self.assertTrue(report['staging_source_ready'])
        self.assertTrue(report['mod_scripts_include_originally_active'])
        self.assertEqual(report['staging_overlay_status'], 'already_active')

    def test_no_include_is_not_invented(self):
        (self.root / 'mod.csv').write_text(
            'rawfile,maps/mp/gametypes/surv.gsc\n', encoding='utf-8')
        report = pkg.audit(self.root, self.files)
        self.assertFalse(report['staging_source_ready'])
        self.assertIn('Expected exactly one', report['staging_error'])

    def test_script_and_asset_types_are_reported_separately(self):
        result = pkg.audit(self.root, self.files)
        self.assertEqual(result['asset_references_by_type']['xmodel'], 1)
        self.assertEqual(result['asset_references_by_type']['fx'], 1)
        self.assertEqual(result['unresolved_gametype_script_paths'], [])


if __name__ == '__main__':
    unittest.main()
