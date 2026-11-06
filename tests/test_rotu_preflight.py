import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'iw3_rotu' / 'preflight.py'
spec = importlib.util.spec_from_file_location('preflight', SCRIPT)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class RotuPreflightTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.kisak = self.root / 'kisak'
        self.rotu = self.root / 'rotu'
        self.kisak.mkdir()
        self.rotu.mkdir()
        for p in preflight.ENGINE:
            self.put(self.kisak, p, 'set(KISAK_PLATFORM win32)')
        (self.kisak / 'src').mkdir()
        self.put(self.kisak, 'src/game_mp/g_scr_main_mp.cpp',
                 '{"addtestclient", &GScr_AddTestClient}; {"tablelookup", &Scr_TableLookup};')
        self.put(self.kisak, 'src/server_mp/sv_client_mp.cpp',
                 'SV_AddTestClient() { SV_DirectConnect(x); SV_ClientEnterWorld(x); return SV_GentityNum(0); }')
        for p in preflight.CORE:
            self.put(self.rotu, p, '')
        self.put(self.rotu, 'scripts/bots/_bots.gsc', 'loadWaypoints(); addTestClient(); scripts\\bots\\_types::initZomTypes();')
        self.put(self.rotu, 'scripts/gamemodes/_waves.gsc', 'startRegularWave() {}')
        self.put(self.rotu, 'scripts/include/waypoints.gsc', 'loadWaypoints() { tableLookup(0, 0, 0, 0); }')
        self.put(self.rotu, 'mod_scripts.csv', '\n'.join(['rawfile,scripts/bots/_bots.gsc', 'rawfile,scripts/bots/_types.gsc', 'rawfile,scripts/gamemodes/_gamemodes.gsc', 'rawfile,scripts/gamemodes/_survival.gsc', 'rawfile,scripts/gamemodes/_waves.gsc', 'rawfile,scripts/players/_players.gsc']) + '\n')

    def tearDown(self):
        self.t.cleanup()

    @staticmethod
    def put(base, path, value):
        file = base / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding='utf-8')

    def test_source_gate_green_but_runtime_red(self):
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertTrue(result['source_preflight_pass'])
        self.assertFalse(result['runtime']['zombie_running'])
        self.assertFalse(result['runtime']['apk_built'])
        self.assertTrue(result['engine']['windows_platform_selected'])

    def test_missing_zombie_script_is_failing_gate(self):
        (self.rotu / 'scripts/bots/_bots.gsc').unlink()
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertFalse(result['source_preflight_pass'])
        self.assertIn('scripts/bots/_bots.gsc', result['rotu']['missing_core'])

    def test_manifest_missing_file_fails(self):
        self.put(self.rotu, 'mod_scripts.csv', 'rawfile,scripts/bots/not_here.gsc\n')
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertFalse(result['source_preflight_pass'])
        self.assertEqual(result['rotu']['missing_rawfiles'], ['scripts/bots/not_here.gsc'])

    def test_manifest_traversal_is_rejected(self):
        self.put(self.rotu, 'mod_scripts.csv', 'rawfile,scripts/../../evil.gsc\n')
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertFalse(result['source_preflight_pass'])
        self.assertEqual(len(result['rotu']['invalid_manifest_entries']), 1)

    def test_missing_engine_source_fails(self):
        shutil.rmtree(self.kisak / 'src')
        self.assertFalse(preflight.preflight(self.kisak, self.rotu)['source_preflight_pass'])

    def test_native_bot_registration_missing_fails(self):
        self.put(self.kisak, 'src/game_mp/g_scr_main_mp.cpp',
                 '{"tablelookup", &Scr_TableLookup};')
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertFalse(result['source_preflight_pass'])
        self.assertFalse(result['engine']['mp_addtestclient_registered'])

    def test_native_bot_stub_fails(self):
        self.put(self.kisak, 'src/server_mp/sv_client_mp.cpp',
                 'SV_AddTestClient() { return 0; }')
        result = preflight.preflight(self.kisak, self.rotu)
        self.assertFalse(result['source_preflight_pass'])
        self.assertFalse(result['engine']['mp_addtestclient_engine_implementation'])

    def test_game_data_only_checks_local_presence(self):
        data = self.root / 'owned-install'
        self.put(data, 'main/iw_00.iwd', 'fixture')
        self.put(data, 'zone/spanish/mp_crash.ff', 'fixture')
        result = preflight.preflight(self.kisak, self.rotu, data)
        self.assertTrue(result['game_data']['multiplayer_iwd_present'])
        self.assertEqual(result['game_data']['mp_map_fastfiles'], ['zone/spanish/mp_crash.ff'])
        self.assertFalse(result['runtime']['iw3_rotu_compiled'])


if __name__ == '__main__':
    unittest.main()
