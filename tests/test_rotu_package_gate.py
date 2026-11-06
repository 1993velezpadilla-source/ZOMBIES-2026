"""Verify canonical RotU script IWD packager with only synthetic sources."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / 'tools' / 'iw3_rotu' / 'package_gate.py'
spec = importlib.util.spec_from_file_location('package_gate', SOURCE)
pkg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pkg)


class PackageGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.put('mod.csv',
                 '// include,mod_scripts\n'
                 'rawfile,maps/mp/gametypes/surv.gsc\n'
                 'xmodel,fictional_zombie\n'
                 'fx,fictional_attack\n')
        self.put('mod_scripts.csv',
                 'rawfile,scripts/bots/_bots.gsc\n'
                 'rawfile,scripts/include/waypoints.gsc\n'
                 'rawfile,scripts/gamemodes/_waves.gsc\n')
        self.put('compile_mod.bat',
                 r'7z a -r -tzip z_svr_scripts.iwd maps\mp\*.*' + '\n' +
                 r'7z a -r -tzip z_svr_scripts.iwd scripts\*.*' + '\n' +
                 r'7z a -r -tzip z_svr_scripts.iwd common_scripts\*.*')
        self.put('maps/mp/gametypes/surv.gsc', 'main() {}')
        self.put('scripts/bots/_bots.gsc', 'init() {}')
        self.put('scripts/include/waypoints.gsc', 'loadWaypoints() {}')
        self.put('scripts/gamemodes/_waves.gsc', 'startRegularWave() {}')
        self.files = {
            'compile_mod.bat', 'mod.csv', 'mod_scripts.csv',
            'maps/mp/gametypes/surv.gsc', 'scripts/bots/_bots.gsc',
            'scripts/include/waypoints.gsc', 'scripts/gamemodes/_waves.gsc',
        }

    def put(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')

    def test_canonical_builder_not_include_mod_scripts(self):
        report = pkg.audit(self.root, self.files)
        self.assertTrue(report['script_iwd_source_gate'])
        self.assertTrue(report['canonical_builder_uses_script_iwd'])
        self.assertFalse(report['mod_csv_script_include_enabled'])
        self.assertFalse(report['mod_ff_built'])
        self.assertFalse(report['live_zombie_verified'])

    def test_iwd_archive_is_valid_zip_with_real_script_paths(self):
        path = self.root / 'temp-output' / 'z_svr_scripts.iwd'
        report = pkg.audit(self.root, self.files, path)
        self.assertTrue(report['iwd_archive']['crc_verified'])
        self.assertEqual(report['iwd_archive']['member_count'], 4)
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(set(archive.namelist()), set(pkg.REQUIRED))
            self.assertEqual(archive.read('scripts/bots/_bots.gsc'), b'init() {}')
        self.assertFalse(report['mod_ff_built'])

    def test_missing_critical_gametype_reports_blocker(self):
        self.files.remove('maps/mp/gametypes/surv.gsc')
        report = pkg.audit(self.root, self.files)
        self.assertFalse(report['script_iwd_source_gate'])
        self.assertEqual(report['missing_critical_script_paths'],
                         ['maps/mp/gametypes/surv.gsc'])

    def test_missing_manifest_script_reports_blocker(self):
        self.files.remove('scripts/bots/_bots.gsc')
        report = pkg.audit(self.root, self.files)
        self.assertFalse(report['script_iwd_source_gate'])
        self.assertEqual(report['missing_mod_scripts_manifest_paths'], ['scripts/bots/_bots.gsc'])

    def test_wrong_builder_is_detected(self):
        self.put('compile_mod.bat', 'REM no build instructions')
        report = pkg.audit(self.root, self.files)
        self.assertFalse(report['script_iwd_source_gate'])
        self.assertFalse(report['canonical_builder_uses_script_iwd'])

    def test_zip_rejects_non_checked_out_source(self):
        (self.root / 'scripts/bots/_bots.gsc').unlink()
        with self.assertRaises(ValueError):
            pkg.make_iwd(self.root, self.root / 'temp-output' / 'z_svr_scripts.iwd', self.files)

    def test_assets_are_not_packaged_or_claimed_verified(self):
        report = pkg.audit(self.root, self.files, self.root / 'z_svr_scripts.iwd')
        self.assertEqual(report['referenced_asset_types']['xmodel'], 1)
        self.assertEqual(report['referenced_asset_types']['fx'], 1)
        self.assertFalse(report['mod_ff_asset_dependencies_verified'])
        with zipfile.ZipFile(self.root / 'z_svr_scripts.iwd') as archive:
            self.assertNotIn('xmodel/fictional_zombie', archive.namelist())


if __name__ == '__main__':
    unittest.main()
