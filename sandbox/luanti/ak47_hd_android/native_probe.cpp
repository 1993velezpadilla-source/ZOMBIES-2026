// Actual pinned Luanti/Irrlicht GLB loader + CPU skinning against private goldens.
// No GPU, window, Android device, or engine-performance claim is made here.
#include "CGLTFMeshFileLoader.h"
#include "CReadFile.h"
#include "SkinnedMesh.h"
#include "IMeshBuffer.h"
#include "IVertexBuffer.h"
#include "os.h"
#include "network/networkprotocol.h"
#include "network/networkpacket.h"
#include "serialization.h"
#include "log.h"
#include <json/json.h>
#include <fstream>
#include <iostream>
#include <cmath>
#include <stdexcept>
#include <sstream>
#include <chrono>

// Test-harness log sink for the actual engine compression implementation.
class ProbeLogTarget : public LogTarget {
public:
    bool hasOutput() override { return true; }
    void log(std::string_view message) override { std::cerr<<message; }
};
ProbeLogTarget probe_log_target;
thread_local LogStream dstream(probe_log_target);
void StreamProxy::fix_stream_state(std::ostream &stream) { stream.clear(); }

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
    const auto media_bytes=file->getSize();
    if(media_bytes<=0 || media_bytes>MEDIAFILE_MAX_SIZE) {
        std::cerr<<"SERVER_MEDIA_REJECTED bytes="<<media_bytes
                 <<" limit="<<MEDIAFILE_MAX_SIZE<<std::endl;
        file->drop();return 4;
    }
    // Exercise the same compression, packet writer and decoder as a real join.
    std::ifstream raw_stream(argv[1],std::ios::binary);
    const std::string raw((std::istreambuf_iterator<char>(raw_stream)),{});
    std::ostringstream encoded(std::ios::binary);compressZstd(raw,encoded,1);
    NetworkPacket packet(TOCLIENT_MEDIA,4);
    packet<<u16(1)<<u16(0)<<u32(1)<<std::string_view("ak47hd.glb");
    packet.putLongString(encoded.str());
    if(packet.getSize()>MEDIAFILE_TRANSFER_MAX_SIZE) {
        std::cerr<<"SERVER_MEDIA_TRANSFER_REJECTED bytes="<<packet.getSize()<<std::endl;
        file->drop();return 5;
    }
    packet.seek(0);u16 bunches,index;u32 files;std::string filename;
    packet>>bunches>>index>>files>>filename;
    std::istringstream incoming(packet.readLongString(),std::ios::binary);
    std::ostringstream decoded(std::ios::binary);decompressZstd(incoming,decoded);
    if(bunches!=1 || index!=0 || files!=1 || filename!="ak47hd.glb" || decoded.str()!=raw)
        throw std::runtime_error("native compressed media round trip mismatch");
    scene::CGLTFMeshFileLoader loader;
    auto *mesh=loader.createMesh(file);file->drop();
    if(!mesh)throw std::runtime_error("native Luanti loader rejected GLB");
    auto *skin=dynamic_cast<scene::SkinnedMesh*>(mesh);
    if(!skin || mesh->getTrackCount()!=8 || mesh->getMeshBufferCount()!=8)
        throw std::runtime_error("native mesh layout mismatch");
    mesh->prepareForAnimation(0);
    skin->setSkinPoseCache(true);
    Json::Value cases;std::ifstream stream(argv[2]);stream>>cases;
    double worst=0;
    std::vector<core::matrix4> last_global;
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
        const auto passes=skin->getSkinPosePasses();
        skin->skinMesh(global);
        if(skin->getSkinPosePasses()!=passes)throw std::runtime_error("unchanged pose was reskinned");
        skin->resetAnimation();skin->skinMesh(global);
        if(skin->getSkinPosePasses()!=passes+1)throw std::runtime_error("static pose reset did not invalidate skin cache");
        last_global=global;
        for(const auto &p:test["points"]) {
            const auto xyz=mesh->getMeshBuffer(p["buffer"].asUInt())->getVertexBuffer()->getPosition(p["vertex"].asUInt());
            const double actual[3]={xyz.X,xyz.Y,xyz.Z};
            for(int i=0;i<3;i++)worst=std::max(worst,std::abs(actual[i]-p["xyz"][i].asDouble()));
        }
    }
    auto benchmark=[&](bool cache) {
        skin->setSkinPoseCache(cache);skin->skinMesh(last_global);
        const auto start=std::chrono::steady_clock::now();
        for(int i=0;i<30;++i)skin->skinMesh(last_global);
        return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    };
    const double uncached=benchmark(false),cached=benchmark(true);
    std::cout<<"NATIVE_LUANTI_SKIN_CHECK worst_vertex_error="<<worst
             <<" joints="<<skin->getJointCount()<<" buffers="<<mesh->getMeshBufferCount()
             <<" media_bytes="<<media_bytes<<" media_limit="<<MEDIAFILE_MAX_SIZE
             <<" transfer_bytes="<<packet.getSize()<<" transfer_limit="<<MEDIAFILE_TRANSFER_MAX_SIZE
             <<" media_round_trip=exact"<<std::endl;
    std::cout<<"NATIVE_IDLE_SW_SKIN_CACHE 30_frames_uncached_ms="<<uncached
             <<" cached_ms="<<cached<<" cache_hits="<<skin->getSkinPoseHits()<<std::endl;
    mesh->drop();
    return worst<.01 ? 0 : 3;
}
