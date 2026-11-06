#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace ak47 {
struct GunParameters {
    float pitch_min,pitch_max,yaw_min,yaw_max;
    float acceleration,speed_max,speed_decay,static_decay;
};
struct RecoilDefinition { GunParameters hip,ads;float max_pitch,max_yaw; };

// Port of BG_CalculateWeaponPosition_GunRecoil_SingleAngle in KisakCOD.
inline bool step_angle(float &offset,float &speed,float dt,float cap,
        float acceleration,float speed_max,float speed_decay,float static_decay)
{
    if (std::fabs(offset)<.25f && std::fabs(speed)<1.f) {
        offset=0;speed=0;return true;
    }
    offset+=speed*dt;
    if(offset>cap) {offset=cap;if(speed>0)speed=0;}
    else if(offset<-cap) {offset=-cap;if(speed<0)speed=0;}
    if(offset>0)speed-=acceleration*dt;
    else if(offset<0)speed+=acceleration*dt;
    speed-=speed*speed_decay*dt;
    if(speed>0)speed=std::max(0.f,speed-static_decay*dt);
    else speed=std::min(0.f,speed+static_decay*dt);
    speed=std::clamp(speed,-speed_max,speed_max);
    return false;
}

struct GunRecoil {
    float pitch=0,yaw=0,pitch_speed=0,yaw_speed=0;
    std::uint32_t seed=0x47a51u;
    float random() {seed=1664525u*seed+1013904223u;return float(seed>>8)/16777216.f;}
    void reset() {pitch=yaw=pitch_speed=yaw_speed=0;}
    void fire(const RecoilDefinition &def,float ads,unsigned count=1) {
        const auto &p=ads>0 ? def.ads : def.hip;
        for(unsigned i=0;i<std::min(count,8u);++i) {
            // BG_WeaponFireRecoil adds the weapon-defined angular impulses.
            pitch_speed+=p.pitch_min+random()*(p.pitch_max-p.pitch_min);
            yaw_speed+=p.yaw_min+random()*(p.yaw_max-p.yaw_min);
        }
    }
    void advance(const RecoilDefinition &def,float ads,float elapsed) {
        const float a=std::clamp(ads,0.f,1.f);
        auto mix=[a](float h,float v){return h+(v-h)*a;};
        const float accel=mix(def.hip.acceleration,def.ads.acceleration);
        const float limit=mix(def.hip.speed_max,def.ads.speed_max);
        const float decay=mix(def.hip.speed_decay,def.ads.speed_decay);
        const float friction=mix(def.hip.static_decay,def.ads.static_decay);
        for(float left=std::clamp(elapsed,0.f,.5f);left>0;) {
            const float dt=std::min(.005f,left);left-=dt;
            const bool p=step_angle(pitch,pitch_speed,dt,def.max_pitch,accel,limit,decay,friction);
            const bool y=step_angle(yaw,yaw_speed,dt,def.max_yaw,accel,limit,decay,friction);
            if(p&&y)break;
        }
    }
};

inline float first_fire_sample(float dt,float duration) {
    // A newly received shot must not repeatedly display source frame zero.
    return std::clamp(dt,0.f,duration*.25f);
}
} // namespace ak47
