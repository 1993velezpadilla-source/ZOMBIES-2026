#pragma once
#include <algorithm>

namespace weapon_hud {
inline constexpr const char *managed_crosshair_name = "mcl_playerplus:crosshair";

// Finish fading before the irons settle; reuse the viewmodel's ADS blend.
inline float crosshair_opacity(float ads_fraction, bool weapon, bool first_person)
{
    if (!weapon || !first_person)
        return 1.0f;
    const float fade = std::clamp(ads_fraction / 0.7f, 0.0f, 1.0f);
    return 1.0f - fade * fade * (3.0f - 2.0f * fade);
}
}
