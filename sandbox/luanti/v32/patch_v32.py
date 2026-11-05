#!/usr/bin/env python3
"""Integrate an AK-only camera FPS viewmodel into Luanti C++ (no TaCZ art).

V3.1's node remains the fallback if the original GLB cannot load. The old
generic item placement and right-hand swing are bypassed for AK only.
"""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
AK="ak47dev:ak47"

def checked(path, old, new):
    original=path.read_text(encoding="utf8")
    found=original.count(old)
    if found!=1:
        raise RuntimeError(f"{path}: expected 1 anchor, found {found}: {old[:100]!r}")
    path.write_text(original.replace(old,new), encoding="utf8")

CXX= r'''
void Camera::updateAK47Viewmodel(f32 frametime)
{
    // No Minecraft Forge dependency. Only activate this renderer for the
    // original Voxel Sandbox AK in first person; other tools stay untouched.
    if (m_wield_item_next.name != "ak47dev:ak47" ||
            m_camera_mode != CAMERA_MODE_FIRST) {
        if (m_ak47_viewmodel)
            m_ak47_viewmodel->setVisible(false);
        m_wieldnode->setVisible(true);
        m_ak47_action_left = 0.0f;
        m_ak47_recoil = 0.0f;
        m_ak47_ads_alpha = 0.0f;
        m_ak47_last_event.clear();
        return;
    }

    // Load just once after all mod assets are available on the client.
    if (!m_ak47_mesh_attempted) {
        m_ak47_mesh_attempted = true;
        scene::IAnimatedMesh *mesh = m_client->getMesh("ak47dev_animated.glb");
        if (mesh) {
            const u16 tracks = mesh->getTrackCount();
            m_ak47_viewmodel = m_wieldmgr->addAnimatedMeshSceneNode(mesh);
            mesh->drop();
            if (m_ak47_viewmodel) {
                const char *const textures[4] = {
                    "ak47dev_metal.png", "ak47dev_black.png",
                    "ak47dev_wood.png", "ak47dev_skin.png"
                };
                auto *tsrc = m_client->getTextureSource();
                const u32 count = m_ak47_viewmodel->getMaterialCount();
                for (u32 i = 0; i < count; ++i) {
                    auto &mat = m_ak47_viewmodel->getMaterial(i);
                    mat.BackfaceCulling = false;
                    if (i < 4 && tsrc)
                        mat.setTexture(0, tsrc->getTextureForMesh(textures[i]));
                }
                m_ak47_animated = tracks > 0;
                m_ak47_viewmodel->setVisible(false);
                infostream << "[ak47 FPS] client GLB loaded: " << count
                    << " materials, " << tracks << " animation tracks"
                    << std::endl;
            }
        } else {
            warningstream << "[ak47 FPS] GLB missing/invalid; falling back "
                    "to native 3D wield OBJ" << std::endl;
        }
    }

    std::string mode, flag, event;
    m_wield_item_next.metadata.getStringToRef("xz_ak_view", mode);
    m_wield_item_next.metadata.getStringToRef("xz_ak_ads", flag);
    m_wield_item_next.metadata.getStringToRef("xz_ak_anim", event);
    const bool use_rig = mode != "native" && m_ak47_viewmodel;

    // ADS interpolates in the client render loop (not 5 Hz Lua globalstep).
    const f32 target = flag == "1" ? 1.0f : 0.0f;
    const f32 interp = std::min(1.0f, std::max(0.0f, frametime * 11.0f));
    m_ak47_ads_alpha += (target - m_ak47_ads_alpha) * interp;
    m_ak47_clock += std::max(0.0f, frametime);

    if (!event.empty() && event != m_ak47_last_event) {
        m_ak47_last_event = event;
        if (event[0] == 'R') {
            m_ak47_action_left = 2.75f;
            m_ak47_action_reload = true;
        } else if (event[0] == 'F') {
            m_ak47_action_left = 0.105f;
            m_ak47_action_reload = false;
            m_ak47_recoil = 1.0f;
        }
        if (use_rig && m_ak47_animated &&
                m_ak47_action_left > 0.0f) {
            auto &track = m_ak47_viewmodel->getAnimation().tracks[0];
            if (m_ak47_action_reload) {
                // Original rig keyframes: remove mag, insert mag, rack bolt
                // at timeline 1.0 .. 3.75 seconds.
                track.setFrameRange(1.0f, 3.75f);
                track.fps = 1.0f;
            } else {
                // The shoot segment is compressed to 0.10 seconds / 600 RPM.
                track.setFrameRange(0.40f, 0.82f);
                track.fps = 4.0f;
            }
            track.loop = false;
            track.cur_frame = track.min_frame;
        }
    }
    const f32 before = m_ak47_action_left;
    m_ak47_action_left = std::max(0.0f,
            m_ak47_action_left - std::max(0.0f, frametime));
    m_ak47_recoil = std::max(0.0f,
            m_ak47_recoil - std::max(0.0f, frametime) * 10.0f);
    if (before > 0.0f && m_ak47_action_left == 0.0f &&
            use_rig && m_ak47_animated) {
        auto &track = m_ak47_viewmodel->getAnimation().tracks[0];
        track.setFrameRange(0.0f, 0.18f);
        track.fps = 1.0f;
        track.loop = true;
        track.cur_frame = track.min_frame;
    }

    // Camera +Z is forward in the independent wield scene. A gun modeled
    // along +Z must NOT inherit generic tool rotation (-100,120,-100).
    // Hipfire is below-right and converges toward the reticle. In ADS,
    // the AK's rear notch and front post sit near the camera centerline.
    const v3f hip_pos(10.5f, -11.7f, 28.0f);
    const v3f ads_pos(0.0f, -1.9f, 29.0f);
    const v3f hip_rot(-2.0f, -14.0f, -1.0f);
    const v3f ads_rot(0.0f, 0.0f, 0.0f);

    const f32 a = m_ak47_ads_alpha;
    v3f pose = hip_pos * (1.0f - a) + ads_pos * a;
    v3f rot = hip_rot * (1.0f - a) + ads_rot * a;
    const f32 sway = 1.0f - a;
    pose.X += std::sin(m_ak47_clock * 1.9f) * 0.22f * sway;
    pose.Y += std::sin(m_ak47_clock * 2.5f) * 0.13f * sway;
    pose.Z -= m_ak47_recoil * 1.4f;
    rot.X -= m_ak47_recoil * 2.5f;
    if (m_ak47_action_reload && m_ak47_action_left > 0.0f)
        pose.Y -= std::sin((2.75f-m_ak47_action_left)/2.75f *
                M_PI) * 2.0f * (1.0f-a);

    if (use_rig) {
        // The animated GLB uses authoring dimensions: 10 units = a voxel.
        m_wieldnode->setVisible(false);
        m_ak47_viewmodel->setVisible(true);
        m_ak47_viewmodel->setScale(v3f(2.7f, 2.7f, 2.7f));
        m_ak47_viewmodel->setPosition(pose);
        m_ak47_viewmodel->setRotation(rot);
    } else {
        // Fallback: same correct FPS pose, using the *static* native OBJ.
        // The Lua node's wield_scale is set to 7.0; C++ wield scale maps
        // the OBJ into roughly the same camera-space dimensions.
        if (m_ak47_viewmodel)
            m_ak47_viewmodel->setVisible(false);
        m_wieldnode->setVisible(true);
        m_wieldnode->setPosition(pose);
        m_wieldnode->setRotation(rot);
    }
}

'''
def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python patch_v32.py /path/to/luanti")
    luanti=Path(sys.argv[1]).resolve()
    header=luanti/"src/client/camera.h"
    cpp=luanti/"src/client/camera.cpp"
    android=luanti/"android/app"
    if not (luanti/"games/voxelibre/mods/ak47dev/init.lua").exists():
        raise RuntimeError("Run prepare, V2/V3/V3.1 patches first")
    checked(header, "class WieldMeshSceneNode;", "class WieldMeshSceneNode;\n"
            "namespace scene { class AnimatedMeshSceneNode; }")
    checked(header,
            "\tvoid updateWieldedTool();",
            "\tvoid updateWieldedTool();\n\tvoid updateAK47Viewmodel(f32 frametime);")
    checked(header,
            "\tWieldMeshSceneNode *m_wieldnode = nullptr;",
            "\tWieldMeshSceneNode *m_wieldnode = nullptr;\n"
            "\t// APK V3.2 experimental AK first-person camera-owned renderer.\n"
            "\tscene::AnimatedMeshSceneNode *m_ak47_viewmodel = nullptr;\n"
            "\tbool m_ak47_mesh_attempted = false;\n"
            "\tbool m_ak47_animated = false;\n"
            "\tbool m_ak47_action_reload = false;\n"
            "\tf32 m_ak47_ads_alpha = 0.0f;\n"
            "\tf32 m_ak47_action_left = 0.0f;\n"
            "\tf32 m_ak47_clock = 0.0f;\n"
            "\tf32 m_ak47_recoil = 0.0f;\n"
            "\tstd::string m_ak47_last_event;")

    checked(cpp,
            '#include "wieldmesh.h"',
            '#include "wieldmesh.h"\n'
            '#include "AnimatedMeshSceneNode.h"\n'
            '#include "client/texturesource.h"')
    checked(cpp,
            'void Camera::wield(const ItemStack &item, bool animate)\n{',
            CXX + 'void Camera::wield(const ItemStack &item, bool animate)\n{')
    checked(cpp,
            'if (item.name != m_wield_item_next.name ||\n'
            '\t\t\titem.metadata != m_wield_item_next.metadata) {\n'
            '\t\tm_wield_item_next = item;',
            'if (item.name != m_wield_item_next.name ||\n'
            '\t\t\titem.metadata != m_wield_item_next.metadata) {\n'
            '\t\t// AK visual packets arrive every shot/reload. Keep 3D meshes\n'
            '\t\t// loaded without rebuilding or playing generic equip animation.\n'
            '\t\tif (item.name == "ak47dev:ak47" &&\n'
            '\t\t\t\tm_wield_item_next.name == item.name) {\n'
            '\t\t\tm_wield_item_next = item;\n'
            '\t\t\treturn;\n'
            '\t\t}\n'
            '\t\tm_wield_item_next = item;')
    checked(cpp,
            '\tm_wieldnode->setPosition(wield_position);\n'
            '\tm_wieldnode->setRotation(wield_rotation);',
            '\tif (m_wield_item_next.name == "ak47dev:ak47" &&\n'
            '\t\t\tm_camera_mode == CAMERA_MODE_FIRST) {\n'
            '\t\tupdateAK47Viewmodel(frametime);\n'
            '\t} else {\n'
            '\t\tupdateAK47Viewmodel(frametime); // restore normal tools\n'
            '\t\tm_wieldnode->setPosition(wield_position);\n'
            '\t\tm_wieldnode->setRotation(wield_rotation);\n'
            '\t}')
    # The old V3 node has private app id, APK V3.2 adds a different one.
    checked(android/"build.gradle",
            "applicationId 'com.xziel.voxelsandbox.v31'",
            "applicationId 'com.xziel.voxelsandbox.v32'")
    checked(android/"src/main/AndroidManifest.xml",
            "com.xziel.voxelsandbox.v31.fileprovider",
            "com.xziel.voxelsandbox.v32.fileprovider")
    checked(android/"src/main/AndroidManifest.xml",
            "com.xziel.voxelsandbox.v31.documents",
            "com.xziel.voxelsandbox.v32.documents")
    checked(android/"src/main/java/net/minetest/minetest/GameActivity.java",
            '"com.xziel.voxelsandbox.v31.fileprovider"',
            '"com.xziel.voxelsandbox.v32.fileprovider"')
    checked(android/"src/main/res/values/strings.xml",
            '<string name="label">Voxel Sandbox AK Visible</string>',
            '<string name="label">Voxel Sandbox AK FPS</string>')
    print("V3.2 patched: AK-only C++ glTF camera rig + hipfire/ADS + reload "
          "animation, native 3D fallback, non-conflicting APK package")
if __name__=="__main__":
    main()
