"""Cache unchanged CPU skin poses and build the Android playtest with Release code."""
import argparse
from pathlib import Path
from patch_engine import checked

def patch(root):
    header=root/'irr/include/SkinnedMesh.h';cpp=root/'irr/src/SkinnedMesh.cpp'
    checked(header,'\tbool useSoftwareSkinning() const { return UseSwSkinning; }',
        '\tbool useSoftwareSkinning() const { return UseSwSkinning; }\n'
        '\tvoid setSkinPoseCache(bool enabled) { CacheSkinPose=enabled;LastSkinPose.clear(); }\n'
        '\tu64 getSkinPosePasses() const { return SkinPosePasses; }\n'
        '\tu64 getSkinPoseHits() const { return SkinPoseHits; }')
    checked(header,'\tbool UseSwSkinning = false;',
        '\tbool UseSwSkinning = false;\n\tbool CacheSkinPose = false;\n'
        '\tstd::vector<core::matrix4> LastSkinPose;\n\tu64 SkinPosePasses=0,SkinPoseHits=0;')
    checked(cpp,'\tif (!IsAnimatable)\n\t\treturn;\n\n\t// Premultiply',
        '\tif (!IsAnimatable)\n\t\treturn;\n'
        '\tif (CacheSkinPose && LastSkinPose.size()==global_matrices.size() &&\n'
        '\t\tstd::equal(global_matrices.begin(),global_matrices.end(),LastSkinPose.begin(),\n'
        '\t\t\t[](const auto &a,const auto &b) { return std::equal(a.pointer(),a.pointer()+16,b.pointer()); })) {\n'
        '\t\t++SkinPoseHits;return;\n\t}\n'
        '\tif (CacheSkinPose) LastSkinPose=global_matrices;\n\t++SkinPosePasses;\n\n\t// Premultiply')
    for signature in ('void SkinnedMesh::updateStaticPose()','void SkinnedMesh::resetAnimation()',
                      'void SkinnedMesh::setDirty(E_BUFFER_TYPE buffer)'):
        checked(cpp,signature+'\n{',signature+'\n{\n\tLastSkinPose.clear();')
    # Release signing uses the same test-signing mechanism as earlier playtests.
    app=root/'android/app/build.gradle'
    with app.open('a') as f:f.write('\nandroid { buildTypes { release { signingConfig signingConfigs.debug } } }\n')
    checked(root/'android/native/build.gradle','\t\trelease {\n\t\t\tndk {',
        '\t\trelease {\n\t\t\texternalNativeBuild { cmake { arguments "-DCMAKE_BUILD_TYPE=Release" } }\n\t\t\tndk {')
    # This is part of the existing developer FPS overlay, not the normal HUD.
    checked(root/'src/client/gameui.cpp',
        '\t\t\t<< " | RTT: " << (client->getRTT() * 1000.0f) << "ms";',
        '\t\t\t<< " | RTT: " << (client->getRTT() * 1000.0f) << "ms";\n'
        '\t\tconst auto &skin_stats=RenderingEngine::get_video_driver()->getFrameStats();\n'
        '\t\tos << "\\nSkin GPU: " << skin_stats.HWSkinnedMeshes << " | CPU: "\n'
        '\t\t\t<< skin_stats.SWSkinnedMeshes << " | triangles: " << skin_stats.PrimitivesDrawn;')
    print('Release native build, opt-in unchanged-pose cache and skinning-path diagnostics patched')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);patch(p.parse_args().root)
