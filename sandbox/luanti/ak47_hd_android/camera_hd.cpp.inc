void Camera::updateAK47Viewmodel(f32 frametime)
{
    const f32 dt = std::max(0.0f, frametime);
    if (m_wield_item_next.name != "ak47dev:ak47" || m_camera_mode != CAMERA_MODE_FIRST) {
        if (m_ak47_viewmodel) m_ak47_viewmodel->setVisible(false);
        m_wieldnode->setVisible(true);
        m_ak47_action_left = 0.0f;
        m_ak47_ads_alpha = 0.0f;
        m_ak47_hd_active = false;
        m_ak47_source_recoil.reset();
        return;
    }
    m_ak47_clock += dt;
    if (!m_ak47_viewmodel && (!m_ak47_mesh_attempted || m_ak47_clock > 1.0f)) {
        m_ak47_mesh_attempted = true;
        m_ak47_clock = 0.0f;
        scene::IAnimatedMesh *mesh = m_client->getMesh("ak47hd.glb");
        if (mesh) {
            if (auto *skin=dynamic_cast<scene::SkinnedMesh*>(mesh))
                skin->setSkinPoseCache(true);
            if (mesh->getTrackNumber("ak47_ads_hold") && mesh->getTrackNumber("viewmodel_ak47_reload")) {
                m_ak47_viewmodel = m_wieldmgr->addAnimatedMeshSceneNode(mesh);
                auto *textures = m_client->getTextureSource();
                auto *shaders = m_client->getShaderSource();
                ShaderFeatures features;
                features.skinning = mesh->needsHwSkinning();
                const u32 shader_id = shaders->getShaderRaw("fs_model_shader", false, features);
                for (u32 i = 0; m_ak47_viewmodel && i < m_ak47_viewmodel->getMaterialCount(); ++i) {
                    auto &material = m_ak47_viewmodel->getMaterial(i);
                    material.MaterialType = shaders->getShaderInfo(shader_id).material;
                    material.BackfaceCulling = false;
                    const u32 slot = mesh->getTextureSlot(i);
                    material.setTexture(0, textures->getTextureForMesh(
                        slot == 1 ? "ak47hd_hands.png" : "ak47hd_512.png"));
                }
                infostream << "[ak47hd] loaded combined rifle+hands: "
                           << mesh->getMeshBufferCount() << " buffers, "
                           << mesh->getTrackCount() << " source-derived clips" << std::endl;
            } else {
                errorstream << "[ak47hd] required animation tracks missing" << std::endl;
            }
            mesh->drop();
        }
    }
    // A missing HD mesh must never silently display the old placeholder rifle.
    m_wieldnode->setVisible(false);
    if (!m_ak47_viewmodel) return;
    m_ak47_viewmodel->setVisible(true);
    m_ak47_viewmodel->setPosition(v3f(0, 0, 0));
    m_ak47_viewmodel->setScale(v3f(1, 1, 1));

    std::string flag, event, empty, fired_text;
    m_wield_item_next.metadata.getStringToRef("xz_ak_ads", flag);
    m_wield_item_next.metadata.getStringToRef("xz_ak_anim", event);
    m_wield_item_next.metadata.getStringToRef("xz_ak_empty", empty);
    m_wield_item_next.metadata.getStringToRef("xz_ak_fired", fired_text);
    const u32 fired=static_cast<u32>(std::strtoul(fired_text.c_str(),nullptr,10));
    if (!m_ak47_hd_active) {
        m_ak47_last_event = event;
        m_ak47_hd_active = true;
        m_ak47_last_fired=fired;
    }
    const f32 target = flag == "1" ? 1.0f : 0.0f;
    const f32 step = dt / 0.25f;
    m_ak47_ads_alpha = target > m_ak47_ads_alpha ?
        std::min(target, m_ak47_ads_alpha + step) : std::max(target, m_ak47_ads_alpha - step);
    m_ak47_source_recoil.advance(ak47::source_recoil,m_ak47_ads_alpha,dt);

    m_ak47_hd_elapsed += dt;
    m_ak47_action_left = std::max(0.0f, m_ak47_action_left - dt);
    auto *mesh = m_ak47_viewmodel->getMesh();
    if (!event.empty() && event != m_ak47_last_event) {
        m_ak47_last_event = event;
        if (event[0] == 'R') {
            m_ak47_source_recoil.reset();
            m_ak47_action_reload = true;
            m_ak47_hd_action = empty == "1" ? "viewmodel_ak47_reload_empty" : "viewmodel_ak47_reload";
            const auto id = mesh->getTrackNumber(m_ak47_hd_action);
            m_ak47_hd_duration = id ? mesh->getMaxFrameNumber(*id) : 2.7666667f;
            m_ak47_action_left = m_ak47_hd_duration;
            m_ak47_hd_elapsed = 0.0f;
        } else if (event[0] == 'F') {
            m_ak47_action_reload = false;
            m_ak47_hd_action = target > 0.5f ? "ak47_ads_fire" : "viewmodel_ak47_fire";
            m_ak47_hd_duration = 0.10f; // full source curve at the 600 RPM weapon clock
            m_ak47_action_left = m_ak47_hd_duration;
            m_ak47_hd_elapsed = ak47::first_fire_sample(dt,m_ak47_hd_duration);
            const u32 shots=fired>m_ak47_last_fired ? fired-m_ak47_last_fired : 1u;
            m_ak47_source_recoil.fire(ak47::source_recoil,m_ak47_ads_alpha,shots);
            m_ak47_source_recoil.advance(ak47::source_recoil,m_ak47_ads_alpha,.005f);
        }
    }
    m_ak47_last_fired=fired;
    m_ak47_viewmodel->setRotation(v3f(m_ak47_source_recoil.pitch,-m_ak47_source_recoil.yaw,0));
    std::string clip;
    f32 fraction = 0.0f;
    if (m_ak47_action_left > 0.0f) {
        clip = m_ak47_hd_action;
        fraction = std::min(1.0f, m_ak47_hd_elapsed / std::max(0.001f, m_ak47_hd_duration));
    } else if (m_ak47_ads_alpha > 0.0001f && m_ak47_ads_alpha < 0.9999f) {
        clip = target > 0.5f ? "ak47_ads_enter" : "ak47_ads_exit";
        fraction = target > 0.5f ? m_ak47_ads_alpha : 1.0f - m_ak47_ads_alpha;
    } else {
        clip = m_ak47_ads_alpha > 0.5f ? "ak47_ads_hold" : "ak47_hip_idle";
    }
    const auto id = mesh->getTrackNumber(clip);
    if (!id) return;
    auto &animation = m_ak47_viewmodel->getAnimation();
    if (m_ak47_hd_clip != clip) {
        animation.tracks.clear();
        m_ak47_hd_clip = clip;
        auto &track = animation.tracks[*id];
        track.setFrameRange(0.0f, mesh->getMaxFrameNumber(*id));
        track.fps = 0.0f; // sample by the client clock, including interrupted ADS
        track.loop = false;
        track.blend_duration = 0.04f;
    }
    animation.tracks[*id].cur_frame = fraction * mesh->getMaxFrameNumber(*id);
}

