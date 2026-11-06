"""Ensure V12-style 2-weapon APK cannot be mistaken for a 28-weapon Arsenal."""
from io import BytesIO
import json
from pathlib import Path
import struct
import tempfile
import unittest
from zipfile import ZipFile

from scan_installed_apk import registrations, scan


def model(names=("idle", "reload")):
    document = {
        "asset": {"version": "2.0"},
        "meshes": [{"primitives": []}],
        "animations": [{"name": x} for x in names],
    }
    buf = json.dumps(document).encode()
    buf += b" " * (-len(buf) % 4)
    return b"glTF" + struct.pack("<II", 2, len(buf)+20) + struct.pack("<I4s", len(buf), b"JSON") + buf


def make_apk(dest, lua, glbs=1):
    nested = BytesIO()
    root = "games/voxelibre/mods/ak47dev/"
    with ZipFile(nested, "w") as pack:
        pack.writestr(root+"init.lua", lua)
        for n in range(glbs):
            pack.writestr(root+f"models/variant_{n}.glb", model())
    with ZipFile(dest, "w") as apk:
        apk.writestr("AndroidManifest.xml", b"manifest")
        apk.writestr("lib/arm64-v8a/libmain.so", b"elf")
        apk.writestr("assets/assets.zip", nested.getvalue())


EXPLICIT = '''
local AK="ak47dev:ak47"
local M9="ak47dev:m9"
local definitions={
 [AK]={capacity=30},
 [M9]={capacity=15},
}
for item_name,definition in pairs(definitions) do
 minetest.register_tool(item_name,{description=definition.label})
end
'''


class ScanTests(unittest.TestCase):
    def test_two_registered_tools_despite_many_variants(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder)/"bridge.apk"
            make_apk(apk, EXPLICIT, 22)
            result = scan(apk)
            self.assertEqual(result["registered_tool_ids_found"],
                             ["ak47dev:ak47", "ak47dev:m9"])
            self.assertEqual(result["registered_tool_count"], 2)
            self.assertEqual(result["glb_count"], 22)
            self.assertFalse(result["device_fps_verified"])

    def test_literal_register_tool(self):
        ids, missed = registrations({"mod.lua":
            'minetest.register_tool("my:gun",{description="Gun"})'})
        self.assertEqual(ids, ["my:gun"])
        self.assertFalse(missed)

    def test_unknown_dynamic_registration_must_be_unresolved(self):
        ids, missed = registrations({"mod.lua":
            'minetest.register_tool(random_name(), {})'})
        self.assertEqual(ids, [])
        self.assertEqual(len(missed), 1)

    def test_invalid_glb_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder)/"bad.apk"
            make_apk(apk, EXPLICIT)
            # A non-GLB with .glb extension must not be counted.
            from scan_installed_apk import glb_clips
            with self.assertRaisesRegex(ValueError, "invalid GLB"):
                glb_clips(b"bogus", "fake.glb")

    def test_registration_does_not_infer_models_are_weapons(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder)/"variants.apk"
            make_apk(apk, 'minetest.register_tool("ak47dev:ak47", {})', 95)
            result = scan(apk)
            self.assertEqual(result["glb_count"], 95)
            self.assertEqual(result["registered_tool_count"], 1)


if __name__ == "__main__":
    unittest.main()
