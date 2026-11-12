#pragma once
#include <cmath>
#include <cstdlib>
#include <string>

namespace weapon_bridge {
// Extra profiles are supplied by the server's source-verified weapon catalogue.
// Restrict their assets to this firearm's namespace, even on a remote server.
inline bool extra_asset(const std::string &item,const std::string &asset,const std::string &extension) {
    if(item.rfind("cod4:",0)!=0 || asset.size()<extension.size())return false;
    const std::string prefix="a_"+item.substr(5)+"_";
    if(asset.rfind(prefix,0)!=0 || asset.compare(asset.size()-extension.size(),extension.size(),extension)!=0)return false;
    for(size_t i=0;i<asset.size()-extension.size();++i) {
        const char c=asset[i];if(!(c>='a' && c<='z') && !(c>='0' && c<='9') && c!='_')return false;
    }
    return true;
}
inline float extra_number(const std::string &text,float fallback,float minimum,float maximum) {
    if(text.empty())return fallback;
    char *end=nullptr;const float value=std::strtof(text.c_str(),&end);
    return end && *end==0 && std::isfinite(value) && value>=minimum && value<=maximum ? value : fallback;
}
}
