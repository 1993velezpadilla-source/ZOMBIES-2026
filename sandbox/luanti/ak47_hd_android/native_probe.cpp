// Actual pinned Luanti/Irrlicht GLB loader + CPU skinning against private goldens.
// No GPU, window, Android device, or engine-performance claim is made here.
#include "CGLTFMeshFileLoader.h"
#include "CReadFile.h"
#include "SkinnedMesh.h"
#include "IMeshBuffer.h"
#include "IVertexBuffer.h"
#include "os.h"
#include <json/json.h>
#include <fstream>
#include <iostream>
#include <cmath>
#include <stdexcept>

namespace os {
ILogger *Printer::Logger = nullptr;
void Printer::print(const c8 *m,ELOG_LEVEL){std::cerr<<m<<std::endl;}
void Printer::log(const c8 *m,ELOG_LEVEL l){print(m,l);}
void Printer::log(const c8 *m,const c8 *h,ELOG_LEVEL l){print((std::string(m)+": "+h).c_str(),l);}
void Printer::log(const c8 *m,const io::path &h,ELOG_LEVEL l){log(m,h.c_str(),l);}
}

int main(int argc,char **argv) {
    if(argc!=3)return 2;
    auto *file=io::CReadFile::createReadFile(argv[1]);
    if(!file)throw std::runtime_error("missing private GLB");
    scene::CGLTFMeshFileLoader loader;
    auto *mesh=loader.createMesh(file);file->drop();
    if(!mesh)throw std::runtime_error("native Luanti loader rejected GLB");
    auto *skin=dynamic_cast<scene::SkinnedMesh*>(mesh);
    if(!skin || mesh->getTrackCount()!=8 || mesh->getMeshBufferCount()!=8)
        throw std::runtime_error("native mesh layout mismatch");
    mesh->prepareForAnimation(0);
    Json::Value cases;std::ifstream stream(argv[2]);stream>>cases;
    double worst=0;
    for(const auto &test:cases) {
        auto id=mesh->getTrackNumber(test["clip"].asString());
        if(!id)throw std::runtime_error("native animation name missing");
        std::vector<std::optional<core::Transform>> old(skin->getJointCount());
        auto local=skin->animateMesh({{*id,test["time"].asFloat(),1.f}},old);
        std::vector<core::matrix4> global;
        for(const auto &transform:local) {
            if(const auto *matrix=std::get_if<core::matrix4>(&transform))global.push_back(*matrix);
            else global.push_back(std::get<core::Transform>(transform).buildMatrix());
        }
        skin->calculateGlobalMatrices(global);skin->skinMesh(global);
        for(const auto &p:test["points"]) {
            const auto xyz=mesh->getMeshBuffer(p["buffer"].asUInt())->getVertexBuffer()->getPosition(p["vertex"].asUInt());
            const double actual[3]={xyz.X,xyz.Y,xyz.Z};
            for(int i=0;i<3;i++)worst=std::max(worst,std::abs(actual[i]-p["xyz"][i].asDouble()));
        }
    }
    std::cout<<"NATIVE_LUANTI_SKIN_CHECK worst_vertex_error="<<worst
             <<" joints="<<skin->getJointCount()<<" buffers="<<mesh->getMeshBufferCount()<<std::endl;
    mesh->drop();
    return worst<.01 ? 0 : 3;
}
