"""Generate private runtime recoil constants from the real AK47 weapon definition."""
import math
from pathlib import Path

def write_recoil_header(weapon,out):
    fields=weapon.read_text(encoding='latin-1').split('\\')
    fields=dict(zip(fields[1::2],fields[2::2]))
    suffixes=['PitchMin','PitchMax','YawMin','YawMax','Accel','SpeedMax','SpeedDecay','StaticDecay']
    def number(key):
        v=float(fields[key])
        if not math.isfinite(v):raise ValueError('non-finite recoil parameter: '+key)
        return format(v,'.9g')+('f' if '.' in format(v,'.9g') or 'e' in format(v,'.9g') else '.0f')
    rows=[','.join(number(prefix+'GunKick'+s) for s in suffixes) for prefix in ('hip','ads')]
    text='#pragma once\n#include "ak47_motion.h"\nnamespace ak47 {\n'
    text+='inline constexpr RecoilDefinition source_recoil={\n{'+rows[0]+'},\n{'+rows[1]+'},\n'
    text+=number('gunMaxPitch')+','+number('gunMaxYaw')+'};\n}\n'
    out.write_text(text)

