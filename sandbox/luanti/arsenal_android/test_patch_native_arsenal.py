"""Test native Arsenal camera patch is scoped and preserves original AK path."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from patch_native_arsenal import patch


def fixture(root):
    cpp=root/"luanti/src/client/camera.cpp"
    header=root/"luanti/src/client/camera.h"
    cpp.parent.mkdir(parents=True,exist_ok=True)
    cpp.write_text("""
void Camera::updateAK47Viewmodel(f32 frametime)
{
    const f32 dt = std::max(0.0f, frametime);
    if (m_wield_item_next.name != "ak47dev:ak47" || m_camera_mode != CAMERA_MODE_FIRST) {
        m_wieldnode->setVisible(true);
    }
}
void Camera::wield(const ItemStack &item, bool animate)
{
    if (item.name == "ak47dev:ak47" &&
                m_wield_item_next.name == item.name) {
        m_wield_item_next = item;
    }
}
void Camera::drawWieldedTool()
{
  if (m_wield_item_next.name == "ak47dev:ak47" && m_ak47_viewmodel) {
  }
}
""")
    header.write_text("""
class Camera {
  void updateAK47Viewmodel(f32 frametime);
  u32 m_ak47_last_fired=0;
};
""".replace("  void",chr(9)+"void").replace("  u32",chr(9)+"u32"))
    app=root/"luanti/android/app"
    (app/"src/main/java/net/minetest/minetest").mkdir(parents=True)
    (app/"src/main/res/values").mkdir(parents=True)
    for p in (app/"build.gradle", app/"src/main/AndroidManifest.xml",
              app/"src/main/java/net/minetest/minetest/GameActivity.java"):
        p.write_text("com.xziel.voxelsandbox.ak47dryv8")
    (app/"src/main/res/values/strings.xml").write_text("AK47 COD4 Dry Fire V8")
    src=root/"source"
    (src/"models").mkdir(parents=True)
    (src/"textures").mkdir()
    for suff in ("gun","hands"):
        (src/"models"/f"arsenal_m4_{suff}.glb").write_bytes(b"a"*256)
    for texture in ("arsenal_flat_metal.png","arsenal_flat_hands.png"):
        (src/"textures"/texture).write_bytes(b"\x89PNG\r\n\x1a\n")
    (src/"init.lua").write_text("--source-verified private game registration")
    (src/"mod.conf").write_text("name = arsenal")
    manifest=root/"manifest.json"
    manifest.write_text(json.dumps({"native_model_ids":["m4"]}))
    return root/"luanti",src,manifest


class PatchTests(unittest.TestCase):
    def test_real_source_models_activate_native_gun_and_hands(self):
        with TemporaryDirectory() as d:
            root,src,manifest=fixture(Path(d))
            result=patch(root,src,manifest)
            self.assertEqual(result["native_model_count"],1)
            self.assertTrue(result["legacy_ak_preserved"])
            self.assertFalse(result["android_fps_verified"])
            cpp=(root/"src/client/camera.cpp").read_text()
            self.assertIn("void Camera::updateArsenalViewmodel(f32 frametime)",cpp)
            self.assertIn("updateArsenalViewmodel(frametime);",cpp)
            self.assertIn('m_client->getMesh("arsenal_" + id + "_gun.glb")',cpp)
            self.assertIn('m_client->getMesh("arsenal_" + id + "_hands.glb")',cpp)
            self.assertIn('updateAK47Viewmodel(f32 frametime)',cpp)
            self.assertIn("com.xziel.voxelsandbox.arsenaltest",
                          (root/"android/app/build.gradle").read_text())
            self.assertTrue((root/"games/voxelibre/mods/arsenal/models/arsenal_m4_gun.glb").is_file())

    def test_missing_source_binary_fails_closed(self):
        with TemporaryDirectory() as d:
            root,src,manifest=fixture(Path(d))
            (src/"models/arsenal_m4_hands.glb").unlink()
            with self.assertRaisesRegex(FileNotFoundError,"missing real native model"):
                patch(root,src,manifest)

    def test_illegal_filename_fails_closed(self):
        with TemporaryDirectory() as d:
            root,src,manifest=fixture(Path(d))
            manifest.write_text(json.dumps({"native_model_ids":["../../attack"]}))
            with self.assertRaisesRegex(ValueError,"unsafe native weapon ID"):
                patch(root,src,manifest)

    def test_no_existing_ak_patch_fails_closed(self):
        with TemporaryDirectory() as d:
            root,src,manifest=fixture(Path(d))
            (root/"src/client/camera.cpp").write_text("// untouched Luanti camera")
            with self.assertRaisesRegex(ValueError,"AK HD patch must run first"):
                patch(root,src,manifest)


if __name__=="__main__":
    unittest.main()
