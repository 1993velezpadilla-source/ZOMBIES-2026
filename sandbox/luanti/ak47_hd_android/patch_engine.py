"""Apply HD runtime adapter to the existing V3.3 disposable source checkout."""
import argparse
from pathlib import Path
import shutil
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent

def checked(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise ValueError(str(path)+' expected one source anchor: '+old[:90])
    path.write_text(text.replace(old,new))

def patch(root,assets):
    mod=root/'games/voxelibre/mods/ak47dev'
    shutil.copy2(HERE/'init.lua',mod/'init.lua')
    for folder in ('models','textures'):
        for file in (assets/folder).iterdir():shutil.copy2(file,mod/folder/file.name)
    cpp=root/'src/client/camera.cpp';text=cpp.read_text()
    start=text.index('void Camera::updateAK47Viewmodel(f32 frametime)')
    end=text.index('void Camera::wield(',start)
    cpp.write_text(text[:start]+(HERE/'camera_hd.cpp.inc').read_text()+'\n'+text[end:])
    checked(cpp,'#include "client/texturesource.h"',
            '#include "client/texturesource.h"\n#include "client/shader.h"')
    header=root/'src/client/camera.h'
    checked(header,'\tstd::string m_ak47_last_event;',
        '\tstd::string m_ak47_last_event;\n'
        '\tbool m_ak47_hd_active = false;\n'
        '\tf32 m_ak47_hd_elapsed = 0.0f;\n'
        '\tf32 m_ak47_hd_duration = 0.0f;\n'
        '\tstd::string m_ak47_hd_action;\n'
        '\tstd::string m_ak47_hd_clip;')
    checked(cpp,'\tcam->setFOV(72.0*M_PI/180.0);\n\tcam->setNearValue(10);',
        '\tif (m_wield_item_next.name == "ak47dev:ak47" && m_ak47_viewmodel) {\n'
        '\t\tconst f32 horizontal = (75.0f - 25.0f * m_ak47_ads_alpha) * M_PI / 180.0f;\n'
        '\t\tcam->setFOV(2.0f * std::atan(std::tan(horizontal * 0.5f) / cam->getAspectRatio()));\n'
        '\t\tcam->setNearValue(0.25f);\n'
        '\t} else {\n\t\tcam->setFOV(72.0*M_PI/180.0);\n\t\tcam->setNearValue(10);\n\t}')
    app=root/'android/app'
    # MainActivity re-extracts bundled game assets when VERSION_CODE changes.
    checked(root/'android/build.gradle','project.ext.set("versionBuild", 0)',
            'project.ext.set("versionBuild", 2)')
    for path in [app/'build.gradle',app/'src/main/AndroidManifest.xml',
                 app/'src/main/java/net/minetest/minetest/GameActivity.java']:
        text=path.read_text();assert 'com.xziel.voxelsandbox.v33' in text
        path.write_text(text.replace('com.xziel.voxelsandbox.v33','com.xziel.voxelsandbox.ak47hd'))
    checked(app/'src/main/res/values/strings.xml','Voxel Sandbox AK V33','AK47 HD Playtest')
    checked(root/'src/defaultsettings.cpp','settings->setDefault("touch_interaction_style", "tap");',
            'settings->setDefault("touch_interaction_style", "buttons_crosshair");')
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',23)
    for name,label in [('dig_btn.png','FIRE'),('place_btn.png','ADS'),('aux1_btn.png','R')]:
        image=Image.new('RGBA',(128,128),(18,23,30,170));draw=ImageDraw.Draw(image)
        draw.rounded_rectangle((5,5,123,123),radius=24,outline=(225,230,238,225),width=4)
        box=draw.textbbox((0,0),label,font=font);width=box[2]-box[0]
        draw.text(((128-width)/2,48),label,font=font,fill=(245,245,245,255))
        image.save(root/'textures/base/pack'/name)
        image.save(mod/'textures'/name)
    print('HD adapter ready: .ak47hd package, eight named source clips, external 512px atlas, FIRE/ADS/R')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--assets',type=Path,required=True);a=p.parse_args();patch(a.root,a.assets)
