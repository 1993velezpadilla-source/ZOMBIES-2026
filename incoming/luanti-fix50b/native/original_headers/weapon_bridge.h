#pragma once
#include "ak47_attachments.h"
#include "ak47_weapon_params.h"
#include "m9_weapon_params.h"
#include "arsenal_profiles.h"
namespace weapon_bridge {
inline bool supports(const std::string &name) { return name=="ak47dev:ak47" || name=="ak47dev:m9" || arsenal_native::supports(name); }
inline const ak47::Attachment &profile(const std::string &name,const std::string &id,const std::string &mode) {
 if (const auto *entry=arsenal_native::find(name,id,mode)) return entry->spec;
 if (name=="ak47dev:m9") {
  static const ak47::Attachment base={"m9:none","m9hd.glb","m9hd_rifle.png",65,.1f,.1f,false,false,false,false};
  static const ak47::Attachment silenced={"m9:silencer","m9hd_silencer.glb","m9hd_silencer_rifle.png",65,.1f,.1f,false,true,false,false};
  return id=="silencer" ? silenced : base;
 }
 return ak47::attachment(id,mode);
}
inline const ak47::RecoilDefinition &recoil(const std::string &name,const std::string &id,const std::string &mode) {
 if (const auto *entry=arsenal_native::find(name,id,mode)) return entry->recoil;
 return name=="ak47dev:m9" ? ak47::m9_recoil : ak47::source_recoil;
}
inline bool advanced(const std::string &name) { return name=="ak47dev:m9" || arsenal_native::supports(name); }
inline bool pistol(const std::string &name) {
 if (const auto *entry=arsenal_native::find(name,"none","rifle")) return entry->pistol;
 return name=="ak47dev:m9";
}
inline bool buffer_enabled(const std::string &name,const std::string &id,const std::string &mode,unsigned i) {
 if (const auto *entry=arsenal_native::find(name,id,mode)) return i>=entry->masks.size() || entry->masks[i]==0 || (entry->masks[i]&entry->enabled)!=0;
 return true;
}
inline const char *hands(const std::string &name) {
 if (const auto *entry=arsenal_native::find(name,"none","rifle")) return entry->hands;
 return name=="ak47dev:m9" ? "m9hd_hands.png" : "ak47hd_hands.png";
}
inline const char *scope_texture(const std::string &name,const std::string &id) {
 return arsenal_native::supports(name) && id.find("acog")==std::string::npos ? "arsenal_scope_sniper.png" : "ak47dev_acog_scope.png";
}
}
