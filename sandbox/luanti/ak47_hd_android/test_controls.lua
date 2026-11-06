-- Exercise the registered game controls through a small deterministic engine mock.
local clock=0
local callbacks={}
local sounds={}
local hud=""
local current="ak47dev:ak47"
local controls={dig=false,sneak=false,aux1=false}
local values={}
local meta={set_string=function(self,k,v) values[k]=v end}
local stack={get_name=function() return current end,get_meta=function() return meta end}
local inventory={contains_item=function() return true end,get_size=function() return 1 end,
    get_stack=function() return stack end}
local player={is_player=function() return true end,get_player_name=function() return "test" end,
    get_wielded_item=function() return stack end,set_wielded_item=function() end,
    get_inventory=function() return inventory end,get_wield_index=function() return 1 end,
    get_player_control=function() return controls end,set_fov=function() end,
    hud_add=function() return 1 end,hud_change=function(self,id,k,v) hud=v end,
    get_pos=function() return {x=0,y=0,z=0} end,
    get_properties=function() return {eye_height=1.47} end,
    get_look_dir=function() return {x=1,y=0,z=0} end}
vector={add=function(a,b) return {x=a.x+b.x,y=a.y+b.y,z=a.z+b.z} end,
    multiply=function(a,b) return {x=a.x*b,y=a.y*b,z=a.z*b} end}
minetest={
    get_us_time=function() return clock*1000000 end,
    sound_play=function(n) sounds[n]=(sounds[n] or 0)+1 end,
    raycast=function() return function() return nil end end,
    register_tool=function(n,def) callbacks.node=def end,
    register_on_joinplayer=function(f) callbacks.join=f end,
    register_on_leaveplayer=function() end,
    register_globalstep=function(f) callbacks.step=f end,
    register_chatcommand=function() end,
    get_connected_players=function() return {player} end,
    get_player_by_name=function() return player end,
    after=function(t,f) callbacks.after=f end,
    chat_send_player=function() end,log=function() end}
dofile("sandbox/luanti/ak47_hd_android/init.lua")
callbacks.join(player);clock=1;callbacks.after()
for i=1,30 do callbacks.node.on_use(stack,player);clock=clock+.101 end
assert(sounds.ak47dev_fire==30,"30 rounds must fire")
assert(values.xz_ak_fired=="30","only successful shots increment the recoil counter")
assert(hud:find("00 / 210",1,true),hud)
callbacks.node.on_use(stack,player)
assert(values.xz_ak_empty=="1" and values.xz_ak_anim:sub(1,1)=="R","empty reload event")
clock=clock+3.52;callbacks.step(.05);assert(hud:find("00 / 210",1,true),"empty reload completed early")
clock=clock+.02;callbacks.step(.05);assert(hud:find("30 / 180",1,true),hud)
callbacks.node.on_use(stack,player);clock=clock+.101
callbacks.node.on_place(stack,player);assert(values.xz_ak_ads=="1","ADS toggle")
local event=values.xz_ak_anim
controls.aux1=true;callbacks.step(.05)
assert(values.xz_ak_ads=="0" and values.xz_ak_anim==event,"ADS must exit before reload")
clock=clock+.24;callbacks.step(.05);assert(values.xz_ak_anim==event,"reload started before exit")
clock=clock+.02;callbacks.step(.05);assert(values.xz_ak_anim~=event and values.xz_ak_empty=="0","normal reload event")
controls.aux1=false;clock=clock+2.77;callbacks.step(.05)
assert(hud:find("30 / 179",1,true),hud)
callbacks.node.on_use(stack,player);clock=clock+.101
callbacks.node.on_place(stack,player);assert(values.xz_ak_ads=="1")
current="air";callbacks.step(.05);current="ak47dev:ak47"
clock=clock+.2;callbacks.node.on_place(stack,player);assert(values.xz_ak_ads=="1","unequip resets ADS state")
print("CONTROL_TESTS_PASS: ammunition, dry fire, both reload clocks, ADS exit ordering, aux reload and unequip reset")
