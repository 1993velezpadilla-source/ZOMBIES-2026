// EXPERIMENTAL: original IW3 gun+viewhands GLBs imported into Luanti's
// separate first-person wield scene. This is a real renderer/animation adapter,
// NOT an assertion that every weapon's ADS/handgrip is calibrated.
// Keep Source AK47 HD fully intact and only enable this for arsenal:* tools.
void Camera::updateArsenalViewmodel(f32 frametime)
{
    const f32 dt = std::max(0.0f, frametime);
    const std::string item_name = m_wield_item_next.name;
    const bool selected = item_name.compare(0, 8, "arsenal:") == 0 &&
            m_camera_mode == CAMERA_MODE_FIRST;
    if (!selected) {
        if (m_arsenal_gun) m_arsenal_gun->setVisible(false);
        if (m_arsenal_hands) m_arsenal_hands->setVisible(false);
        return;
    }

    const std::string id = item_name.substr(8);
    const auto valid_id = [&] {
        if (id.empty() || id.size() > 24) return false;
        for (const char c : id)
            if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') ||
                    c == '_')) return false;
        return true;
    };
    if (!valid_id()) {
        warningstream << "[arsenal] invalid weapon ID in item name" << std::endl;
        m_wieldnode->setVisible(true);
        return;
    }
    // Source-certified attachment mesh: never substitute a guessed model.
    std::string variant;
    m_wield_item_next.metadata.getStringToRef("xz_ar_variant", variant);
    if (variant.size() > 42 || std::any_of(variant.begin(), variant.end(),
          [](char c) { return !((c >= 'a' && c <= 'z') ||
                            (c >= '0' && c <= '9') || c == '_'); })) {
        variant.clear();
    }
    const std::string model_key = id + (variant.empty() ? "" : "_" + variant);
    if (m_ak47_viewmodel) m_ak47_viewmodel->setVisible(false);

    if (m_arsenal_id != model_key) {
        if (m_arsenal_gun) { m_arsenal_gun->remove(); m_arsenal_gun = nullptr; }
        if (m_arsenal_hands) { m_arsenal_hands->remove(); m_arsenal_hands = nullptr; }
        m_arsenal_id = model_key;
        m_arsenal_last_event.clear();
        m_arsenal_clip.clear();
        m_arsenal_ads_alpha = 0.0f;
        m_arsenal_clock = 0.0f;
        m_arsenal_retry = 0.0f;
        m_arsenal_action_remaining = 0.0f;
        m_arsenal_action_duration = 0.0f;
    }

    // Loader retries at most once every 2 s, not every render frame.
    // No generic AK or static placeholder silently substitutes a missing gun.
    if (!m_arsenal_gun || !m_arsenal_hands) {
        m_arsenal_retry -= dt;
        if (m_arsenal_retry <= 0.0f) {
            m_arsenal_retry = 2.0f;
            auto *gun = m_client->getMesh("arsenal_" + model_key + "_gun.glb");
            auto *hands = m_client->getMesh("arsenal_" + id + "_hands.glb");
            const bool clips_ok = gun && hands &&
                gun->getTrackNumber("idle") && gun->getTrackNumber("fire") &&
                gun->getTrackNumber("reload") && gun->getTrackNumber("ads") &&
                hands->getTrackNumber("idle") && hands->getTrackNumber("fire") &&
                hands->getTrackNumber("reload") && hands->getTrackNumber("ads");
            if (clips_ok) {
                if (auto *skin=dynamic_cast<scene::SkinnedMesh*>(gun))
                    skin->setSkinPoseCache(true);
                if (auto *skin=dynamic_cast<scene::SkinnedMesh*>(hands))
                    skin->setSkinPoseCache(true);
                m_arsenal_gun = m_wieldmgr->addAnimatedMeshSceneNode(gun);
                m_arsenal_hands = m_wieldmgr->addAnimatedMeshSceneNode(hands);
                if (m_arsenal_gun && m_arsenal_hands) {
                    auto *ts = m_client->getTextureSource();
                    auto *ss = m_client->getShaderSource();
                    auto style = [&](scene::AnimatedMeshSceneNode *node,
                            const char *texture, const char *shader_name) {
                        ShaderFeatures features;
                        features.skinning = node->getMesh()->needsHwSkinning();
                        const u32 sid = ss->getShaderRaw(shader_name, false, features);
                        for (u32 k = 0; k < node->getMaterialCount(); ++k) {
                            auto &mat = node->getMaterial(k);
                            mat.MaterialType = ss->getShaderInfo(sid).material;
                            mat.BackfaceCulling = false;
                            mat.setTexture(0, ts->getTextureForMesh(texture));
                        }
                        node->setVisible(false);
                    };
                    style(m_arsenal_gun, "arsenal_flat_metal.png",
                          "ak47_lit_model_shader");
                    style(m_arsenal_hands, "arsenal_flat_hands.png",
                          "ak47_lit_skin_shader");
                    infostream << "[arsenal] actual GLBs for " << id <<
                        " loaded, gun tracks " << gun->getTrackCount() <<
                        ", hands tracks " << hands->getTrackCount() << std::endl;
                } else {
                    if (m_arsenal_gun) { m_arsenal_gun->remove(); m_arsenal_gun=nullptr; }
                    if (m_arsenal_hands) { m_arsenal_hands->remove(); m_arsenal_hands=nullptr; }
                }
            } else {
                warningstream << "[arsenal] missing complete source mesh/rig/4 clips for "
                        << id << "; fallback to native wield item" << std::endl;
            }
            if (gun) gun->drop();
            if (hands) hands->drop();
        }
    }

    const bool ready = m_arsenal_gun && m_arsenal_hands;
    if (!ready) {
        m_wieldnode->setVisible(true);
        return;
    }
    m_wieldnode->setVisible(false);
    m_arsenal_gun->setVisible(true);
    m_arsenal_hands->setVisible(true);

    std::string ads, event, empty;
    m_wield_item_next.metadata.getStringToRef("xz_ar_ads", ads);
    m_wield_item_next.metadata.getStringToRef("xz_ar_anim", event);
    m_wield_item_next.metadata.getStringToRef("xz_ar_empty", empty);
    const f32 target = ads == "1" ? 1.0f : 0.0f;
    m_arsenal_ads_alpha += (target - m_arsenal_ads_alpha) *
                         std::min(1.0f, dt * 10.0f);
    m_arsenal_clock += dt;

    m_arsenal_action_remaining = std::max(0.0f, m_arsenal_action_remaining - dt);
    if (!event.empty() && event != m_arsenal_last_event) {
        m_arsenal_last_event = event;
        if (event[0] == 'R' || event[0] == 'F') {
            const bool reload = event[0] == 'R';
            const bool has_empty =
                m_arsenal_gun->getMesh()->getTrackNumber("reload_empty") &&
                m_arsenal_hands->getMesh()->getTrackNumber("reload_empty");
            m_arsenal_action = reload
                ? (empty == "1" && has_empty ? "reload_empty" : "reload")
                : "fire";
            auto index = m_arsenal_gun->getMesh()->getTrackNumber(m_arsenal_action);
            m_arsenal_action_duration = index
                ? std::max(0.05f, m_arsenal_gun->getMesh()->getMaxFrameNumber(*index))
                : 0.1f;
            m_arsenal_action_remaining = m_arsenal_action_duration;
        }
    }

    std::string clip = "idle";
    f32 phase = std::fmod(m_arsenal_clock * 0.2f, 1.0f);
    if (m_arsenal_action_remaining > 0.0f) {
        clip = m_arsenal_action;
        phase = 1.0f - m_arsenal_action_remaining /
                          std::max(0.001f, m_arsenal_action_duration);
    } else if (m_arsenal_ads_alpha > 0.001f) {
        clip = "ads";
        phase = std::min(1.0f, m_arsenal_ads_alpha);
    }

    const auto pose = [&](scene::AnimatedMeshSceneNode *node) {
        auto *mesh = node->getMesh();
        const auto index = mesh->getTrackNumber(clip);
        if (!index) return;
        auto &trackset = node->getAnimation();
        if (m_arsenal_clip != clip ||
                trackset.tracks.find(*index) == trackset.tracks.end()) {
            trackset.tracks.clear();
            auto &tr = trackset.tracks[*index];
            tr.setFrameRange(0.0f, mesh->getMaxFrameNumber(*index));
            tr.fps = 0.0f;
            tr.loop = false;
            tr.blend_duration = 0.04f;
        }
        trackset.tracks[*index].cur_frame =
            std::max(0.0f, std::min(1.0f, phase)) * mesh->getMaxFrameNumber(*index);
    };
    pose(m_arsenal_gun);
    pose(m_arsenal_hands);
    m_arsenal_clip = clip;

    // Provisional source-oriented pose. This is NOT ADS sight calibration.
    // Actual camera/pivot corrections must be validated for every gun model.
    const v3f hip(8.0f, -6.0f, 31.0f);
    const v3f aim(0.0f, -2.5f, 31.0f);
    const v3f pos = hip * (1.0f - m_arsenal_ads_alpha) +
                    aim * m_arsenal_ads_alpha;
    for (auto *node : {m_arsenal_gun, m_arsenal_hands}) {
        node->setPosition(pos);
        node->setRotation(v3f(0,0,0));
        node->setScale(v3f(1,1,1));
    }
}
