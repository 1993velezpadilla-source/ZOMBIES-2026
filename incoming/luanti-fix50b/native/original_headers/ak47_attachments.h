#pragma once
#include <string>
namespace ak47 {
struct Attachment { const char *id,*model,*texture; float fov,ads_in,ads_out; bool grenade,silenced,scope,reflex; };
inline const Attachment &attachment(const std::string &id,const std::string &mode) {
static const Attachment rows[]={
{"none","ak47hd.glb","ak47hd_rifle.png",50,0.25f,0.25f,false,false,false,false},
{"gp25","ak47hd_gp25.glb","ak47hd_gp25_rifle.png",50,0.25f,0.25f,false,false,false,false},
{"gp25:grenade","ak47hd_grenade.glb","ak47hd_grenade_rifle.png",55,0.5f,0.5f,true,false,false,false},
{"silencer","ak47hd_silencer.glb","ak47hd_silencer_rifle.png",50,0.25f,0.25f,false,true,false,false},
{"silencer+gp25","ak47hd_silencer_gp25.glb","ak47hd_silencer_gp25_rifle.png",50,0.25f,0.25f,false,true,false,false},
{"silencer+gp25:grenade","ak47hd_silencer_gp25_grenade.glb","ak47hd_silencer_gp25_grenade_rifle.png",55,0.5f,0.5f,true,true,false,false},
{"reflex","ak47hd_reflex.glb","ak47hd_reflex_rifle.png",50,0.25f,0.25f,false,false,false,true},
{"reflex+gp25","ak47hd_reflex_gp25.glb","ak47hd_reflex_gp25_rifle.png",50,0.25f,0.25f,false,false,false,true},
{"reflex+gp25:grenade","ak47hd_reflex_gp25_grenade.glb","ak47hd_reflex_gp25_grenade_rifle.png",55,0.5f,0.5f,true,false,false,false},
{"reflex+silencer","ak47hd_reflex_silencer.glb","ak47hd_reflex_silencer_rifle.png",50,0.25f,0.25f,false,true,false,true},
{"reflex+silencer+gp25","ak47hd_reflex_silencer_gp25.glb","ak47hd_reflex_silencer_gp25_rifle.png",50,0.25f,0.25f,false,true,false,true},
{"reflex+silencer+gp25:grenade","ak47hd_reflex_silencer_gp25_grenade.glb","ak47hd_reflex_silencer_gp25_grenade_rifle.png",55,0.5f,0.5f,true,true,false,false},
{"acog","ak47hd_acog.glb","ak47hd_acog_rifle.png",30,0.3f,0.6f,false,false,true,false},
{"acog+gp25","ak47hd_acog_gp25.glb","ak47hd_acog_gp25_rifle.png",30,0.3f,0.6f,false,false,true,false},
{"acog+gp25:grenade","ak47hd_acog_gp25_grenade.glb","ak47hd_acog_gp25_grenade_rifle.png",55,0.5f,0.5f,true,false,false,false},
{"acog+silencer","ak47hd_acog_silencer.glb","ak47hd_acog_silencer_rifle.png",30,0.3f,0.6f,false,true,true,false},
{"acog+silencer+gp25","ak47hd_acog_silencer_gp25.glb","ak47hd_acog_silencer_gp25_rifle.png",30,0.3f,0.6f,false,true,true,false},
{"acog+silencer+gp25:grenade","ak47hd_acog_silencer_gp25_grenade.glb","ak47hd_acog_silencer_gp25_grenade_rifle.png",55,0.5f,0.5f,true,true,false,false},
}; const auto key=id+(mode=="grenade" ? ":grenade" : ""); for(const auto &row:rows)if(key==row.id)return row; return rows[0];
}
}
