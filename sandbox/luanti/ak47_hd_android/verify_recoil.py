"""Compare the port against the original IW3 function and exercise low-FPS shots."""
import argparse
from pathlib import Path
import subprocess
import tempfile

def verify(source,params):
    text=source.read_text();name='BG_CalculateWeaponPosition_GunRecoil_SingleAngle'
    start=text.index('int __cdecl '+name+'(');brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    reference=text[start:end].replace('__cdecl','').replace(name,'reference_angle').replace('I_fabs','std::fabs')
    test=r'''
#include "ak47_motion.h"
#include "ak47_weapon_params.h"
#include <cassert>
#include <iostream>
#include <random>
REFERENCE
int main() {
    std::mt19937 rng(47);
    std::uniform_real_distribution<float> ofs(-30,30),speed(-100,100),time(.0001f,.005f);
    for(int i=0;i<10000;++i) {
        float a=ofs(rng),b=a,c=speed(rng),d=c,dt=time(rng);
        const auto &p=i%2 ? ak47::source_recoil.ads : ak47::source_recoil.hip;
        bool x=reference_angle(&a,&c,dt,8,p.acceleration,p.speed_max,p.speed_decay,p.static_decay);
        bool y=ak47::step_angle(b,d,dt,8,p.acceleration,p.speed_max,p.speed_decay,p.static_decay);
        assert(x==y && std::fabs(a-b)<.00001f && std::fabs(c-d)<.00001f);
    }
    for(float fps : {6.f,7.f,30.f,60.f}) {
        const float dt=1/fps;
        ak47::GunRecoil r;
        assert(ak47::first_fire_sample(dt,.1f)>0);
        for(int i=0;i<int(fps*2);++i) {
            r.advance(ak47::source_recoil,.5f,dt);
            r.fire(ak47::source_recoil,.5f,i%3 ? 1 : 2);
            r.advance(ak47::source_recoil,.5f,.005f);
            assert(std::isfinite(r.pitch) && std::isfinite(r.yaw));
            assert(std::fabs(r.pitch)<=ak47::source_recoil.max_pitch);
            assert(std::fabs(r.yaw)<=ak47::source_recoil.max_yaw);
        }
        for(int i=0;i<int(fps*3);++i)r.advance(ak47::source_recoil,.5f,dt);
        assert(r.pitch==0 && r.yaw==0 && r.pitch_speed==0 && r.yaw_speed==0);
        r.fire(ak47::source_recoil,0);r.reset();assert(r.pitch_speed==0 && r.yaw_speed==0);
    }
    std::cout<<"NATIVE_RECOIL_PASS: 10000 original-IW3 reference steps; 6/7/30/60 FPS shots, recovery and reset"<<std::endl;
}
'''.replace('REFERENCE',reference)
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder);(p/'verify.cpp').write_text(test)
        subprocess.run(['g++','-std=c++17','-O2','-I',str(Path(__file__).resolve().parent),
                        '-I',str(params.resolve().parent),str(p/'verify.cpp'),'-o',str(p/'verify')],check=True)
        subprocess.run([str(p/'verify')],check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--params',type=Path,required=True)
    a=p.parse_args();verify(a.source,a.params)
