"""Add a private native-local sidecar to the pinned OAT IW3 model converter.

OAT glTF derives locals from global bind matrices. IW3 model.trans/model.quats
are independent source fields; never assume they equal those derived locals.
Only the user's selected AK family/viewhands are written, to an explicit
private output directory. No model values are embedded in this patch.
"""
from pathlib import Path
import sys

def patch(root):
    # Keep the pinned source build portable on GCC 13/14. These headers and
    # the overloaded std::sqrt are explicit, standard equivalents.
    for cpp in (Path(root)/'src').rglob('*.cpp'):
        original=cpp.read_text()
        if 'std::format(' in original and '#include <format>' not in original:
            cpp.write_text('#include <format>\n'+original)
    volume=Path(root)/'src/ObjLoading/Game/T5/XModel/XModelHighMipVolumeT5.cpp'
    volume.write_text(volume.read_text().replace('std::sqrtf(', 'std::sqrt('))
    path=Path(root)/'src/ObjWriting/XModel/XModelToCommonConverter.cpp.template'
    text=path.read_text()
    if 'IW3_NATIVE_LOCALS_DIR' in text:return
    text='#include <cstdlib>\n#include <fstream>\n#include <iomanip>\n'+text
    anchor='''    void AddXModelBones(XModelCommon& out, const ZoneScriptStrings& scriptStrings, const XModel& model)
    {
'''
    header='''        std::ofstream nativeLocals;
        const auto* nativeDirectory = std::getenv("IW3_NATIVE_LOCALS_DIR");
        const std::string_view nativeName(model.name);
        if (nativeDirectory && (nativeName.starts_with("viewmodel_ak47") || nativeName == "viewmodel_base_viewhands"))
        {
            nativeLocals.open(std::string(nativeDirectory) + "/" + model.name + ".json");
            nativeLocals << "{\\\"native_model_locals\\\":true,\\\"bones\\\":[";
            nativeLocals << std::setprecision(10);
        }
'''
    if text.count(anchor)!=1:raise ValueError('pinned OAT AddXModelBones anchor changed')
    text=text.replace(anchor,anchor+header)
    anchor='''            out.m_bones.emplace_back(std::move(bone));'''
    body='''            if (nativeLocals.is_open())
            {
                if (boneNum) nativeLocals << ",";
                nativeLocals << "{\\\"name\\\":" << std::quoted(bone.name)
                    << ",\\\"translation\\\":[" << bone.localOffset[0] << "," << bone.localOffset[1] << "," << bone.localOffset[2]
                    << "],\\\"rotation\\\":[" << bone.localRotation.x << "," << bone.localRotation.y << "," << bone.localRotation.z << "," << bone.localRotation.w << "]}";
            }
'''
    if text.count(anchor)!=1:raise ValueError('pinned OAT bone emission anchor changed')
    text=text.replace(anchor,body+anchor)
    anchor='''        }
    }

    const char* AssetName'''
    if text.count(anchor)!=1:raise ValueError('pinned OAT function ending changed')
    text=text.replace(anchor,'''        }
        if (nativeLocals.is_open()) nativeLocals << "]}\\n";
    }

    const char* AssetName''')
    path.write_text(text)

if __name__=='__main__':patch(sys.argv[1])
