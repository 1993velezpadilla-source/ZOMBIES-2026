-- Exercise real upstream VoxeLibre mcl_damage/init.lua with the repaired
-- attack reason, before allowing a new Android APK to be published.
-- argv[1] is the official file pinned to a verified upstream commit.
local original=assert(arg[1],"VoxeLibre original source path required")
local hp_handlers={}
minetest={
 settings={get_bool=function() return true end},
 register_on_player_hpchange=function(f) hp_handlers[#hp_handlers+1]=f end,
 register_on_dieplayer=function() end,
 register_on_mods_loaded=function(f) f() end,
}
core={
 is_creative_enabled=function() return false end,
}
vl_tuning={setting=function() end}
dofile(original)
assert(type(mcl_damage)=="table" and type(mcl_damage.from_mt)=="function",
 "Actual VoxeLibre damage engine was not loaded")
local attacker={
 get_luaentity=function() return {is_mob=true,name="mobs_mc:zombie"} end,
}
local good={
 type="set_hp",
 _mcl_type="mob",
 _mcl_direct=attacker,
 _mcl_source=attacker,
}
local mapped=mcl_damage.from_mt(good)
assert(mapped.type=="mob","Zombie must classify as a Minecraft mob attack")
assert(mapped.direct==attacker and mapped.source==attacker,
 "Mob damage source ObjectRef must survive VoxeLibre translation")
assert(mapped.flags==mcl_damage.types.mob,"Correct mob damage modifiers required")
local player={get_hp=function() return 20 end,get_player_name=function() return "survivor" end}
assert(#hp_handlers>=2,"VoxeLibre player HP handlers were not installed")
local result=hp_handlers[1](player,-10,good)
assert(result==-10,"Minecraft player HP delta must pass without nil direct crash")

-- Same invalid reason from the actual reported crash must fail in the
-- upstream adapter, proving the test reaches the missing-direct problem.
local old={type="punch",from="v26_zombie"}
local success,err=pcall(mcl_damage.from_mt,old)
assert(not success and tostring(err):find("nil value",1,true),
 "Regression guard no longer reproduced original broken attack reason")
print("PASS real VoxeLibre mcl_damage: valid source, classified mob, no runtime HP crash")
