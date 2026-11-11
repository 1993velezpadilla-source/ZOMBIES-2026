-- Standalone Luanti API mock focused on responsive formspec, stable registry,
-- no world mutation, day/night and developer pages.
local files = {}
local forms = {}
local callbacks = {}
local tools = {}
local nodes = {}
local settings_data = {time_speed='72'}
local storage_data = {}
local logs = {}
local onmods={}
local tick=0
local worldnode='xz_zombies:wall_ak47'
local placed_at={x=4,y=5,z=6}
local handled={}

local M
M = {
 registered_nodes=nodes,registered_entities={['mobs_mc:zombie']={}},registered_items={},
 settings={get=function(_,k) return settings_data[k] end,set=function(_,k,v) settings_data[k]=v end},
 get_current_modname=function() return 'xz_zombies_classic' end,
 get_modpath=function(name) return '/fake/'..name end,
 get_mod_storage=function() return {get_string=function(_,k) return storage_data[k] or '' end,
  set_string=function(_,k,v) storage_data[k]=v end,set_int=function(_,k,v) storage_data[k]=v end} end,
 deserialize=function() return nil end,serialize=function() return '{}' end,
 formspec_escape=function(x) return tostring(x):gsub(']', '\\]'):gsub(';','\\;') end,
 register_node=function(n,d) assert(n:sub(1,1)==':');nodes[n:sub(2)]=d end,
 register_tool=function(n,d) tools[n:sub(2)]=d end,
 register_lbm=function() end,
 register_on_joinplayer=function(fn) callbacks.join=fn end,
 register_on_leaveplayer=function(fn) callbacks.leave=fn end,
 register_on_player_receive_fields=function(fn) callbacks.fields=fn end,
 register_chatcommand=function(n,d) callbacks[n]=d.func end,
 register_on_mods_loaded=function(fn)onmods[#onmods+1]=fn end,
 override_item=function(item,fields)
  assert(M.registered_items[item],'item '..item)
  for k,v in pairs(fields) do M.registered_items[item][k]=v end
 end,
 get_us_time=function()tick=tick+300000;return tick end,
 get_node_or_nil=function(pos) return {name=worldnode,param2=0} end,
 get_node=function(pos) return {name=worldnode,param2=0} end,
 swap_node=function(pos,node) handled.swap={pos=pos,node=node} end,
 dir_to_facedir=function(d)assert(d.z==1);return 0 end,
 get_meta=function(pos) return {get_int=function(_,k)return 1200 end,
  set_int=function(_,k,v) handled.price=v end,set_string=function(_,k,v)end}end,
 raycast=function(o,t,obj,liq)
  local called=false
  return function() if not called then called=true;return {type='node',under=placed_at,above={x=4,y=5,z=7}} end end
 end,

 register_globalstep=function(fn) callbacks.step=fn end,
 show_formspec=function(n,f,s) forms[n]={id=f,src=s} end,
 get_player_window_information=function(n)
  if n=='compact' then return {max_formspec_size={x=5.35,y=4.80},touch_controls=true} end
  if n=='wide' then return {max_formspec_size={x=16.3,y=7.6},touch_controls=true} end
  if n=='portrait' then return {max_formspec_size={x=6.2,y=9.8},touch_controls=true} end
  if n=='tablet' then return {max_formspec_size={x=22,y=13},touch_controls=true} end
  return nil
 end,
 set_timeofday=function(v) _G.test_timeofday=v end,
 get_gametime=function() return 20 end,
 is_singleplayer=function() return true end,
 get_connected_players=function() return {} end,
 chat_send_player=function() end,chat_send_all=function() end,
 log=function(l,s) logs[#logs+1]=s end,
}
_G.minetest=M
_G.vector={new=function(p) return {x=p.x,y=p.y,z=p.z} end}
_G.ItemStack=function(item) return item end
local original_loadfile=loadfile
_G.loadfile=function(path)
 if path:find('arsenal_catalog%.lua') then
  return function()
   local out={}
   for i=1,26 do out['ak47dev:w'..i]={id='w'..i,label='WEAPON '..i,icon='gun.png'} end
   return out
  end
 end
 return original_loadfile(path)
end
assert(loadfile('incoming/luanti-fix50a/games/voxelibre/mods/xz_zombies_classic/init.lua'))()
assert(#tools==0) -- map does not have numeric indices
assert(tools['xz_zombies:editor_tool'])
local c=0;for k in pairs(nodes) do c=c+1 end
assert(c==37,'expected exactly 37 registered gameplay nodes, got '..c)
local meta={}
local function player(n)
 local inv={contains_item=function() return false end,room_for_item=function() return true end,
  add_item=function(_,item) meta.last_item=item;return {is_empty=function() return true end} end}
 local p={}
 function p:get_player_name()return n end
 function p:is_player()return true end
 function p:get_inventory()return inv end
 function p:get_meta() return {get_int=function(_,k)return meta[n..k] or 0 end,set_int=function(_,k,v)meta[n..k]=v end} end
 function p:hud_add()return 1 end
 function p:hud_change()end
 function p:get_armor_groups()return {} end
 function p:set_armor_groups()end
 function p:set_properties()end
 function p:get_hp()return 20 end
 function p:set_hp()end
 return p
end
local players={'compact','wide','portrait','tablet','legacy'}
for _,name in ipairs(players) do
 local p=player(name)
 tools['xz_zombies:editor_tool'].on_use({},p)
 local panel=forms[name]
 assert(panel.id=='xz_zombies:editor')
 local s=panel.src
 assert(s:find('scroll_container%['))
 assert(s:find('scroll_container_end%[%]'))
 local w,h=s:match('size%[([%d%.]+),([%d%.]+)%]')
 w,h=tonumber(w),tonumber(h)
 local mx,my=5.10,4.55
 if name=='wide' then mx,my=9.2,6.5 end
 if name=='portrait' then mx,my=5.95,6.5 end
 if name=='tablet' then mx,my=9.2,6.5 end
 if name=='legacy' then mx,my=8.15,5.95 end
 assert(w<=mx+0.01 and h<=my+0.01,('Unexpected screen size %s %.2f %.2f'):format(name,w,h))
 local footer=s:match('button_exit%[0%.25,([%d%.]+)')
 assert(footer and tonumber(footer)>=3.1)
 -- switch through five pages, preserving the state per-player
 for i=2,5 do
  callbacks.fields(p,'xz_zombies:editor',{page_next=true})
  s=forms[name].src
  assert(s:find('('..i..'/5)',1,true),name..' expected page '..i)
 end
 assert(forms[name].src:find('time_night'))
 callbacks.fields(p,'xz_zombies:editor',{time_night=true})
 assert(settings_data.time_speed=='0' and _G.test_timeofday==0)
 callbacks.fields(p,'xz_zombies:editor',{time_day=true})
 assert(settings_data.time_speed=='0' and _G.test_timeofday==0.5)
 callbacks.fields(p,'xz_zombies:editor',{time_normal=true})
 assert(settings_data.time_speed=='72')
 callbacks.fields(p,'xz_zombies:editor',{page_next=true})
 assert(forms[name].src:find('PLAY'))
 callbacks.fields(p,'xz_zombies:editor',{page_next=true})
 callbacks.fields(p,'xz_zombies:editor',{weapon='6',givewall=true})
 assert(meta.last_item=='xz_zombies:wall_w12' or meta.last_item=='xz_zombies:wall_w13' or meta.last_item, 'selected weapon item missing')
 callbacks.fields(p,'xz_zombies:editor',{page_prev=true})
 -- Developer GUI reachable during active PLAY, with buttons not checkboxes
 callbacks.fields(p,'xz_zombies:editor',{play=true})
 callbacks.fields(p,'xz_zombies:editor',{developer=true})
 assert(forms[name].id=='xz_zombies:developer')
 assert(forms[name].src:find('dev_cheats'))
 callbacks.fields(p,'xz_zombies:developer',{dev_cheats=true})
 assert(forms[name].src:find('god_toggle'))
 callbacks.fields(p,'xz_zombies:developer',{god_toggle=true})
 assert(forms[name].src:find('%[ON'))
 callbacks.fields(p,'xz_zombies:developer',{god_toggle=true})
 assert(forms[name].src:find('%[OFF'))
 print(name..': responsive UI + tabs + day/night + developer PASS')
end
print('PASS: 37 nodes preserved, all five device profile tests passed')

-- FIX49C: actual independent USE and ADS actions.
local originals={}
for name in pairs(nodes) do if name:find('^xz_zombies:wall_') then
 assert(nodes[name].on_place,'missing solid-wall placement enforcement '..name)
end end
for i=1,26 do originals['ak47dev:w'..i]=true end
originals['ak47dev:m9']=true; originals['ak47dev:ak47']=true
for item in pairs(originals) do
 local d={}
 d.on_place=function(stack,p,pointed)
  handled.original_place=(handled.original_place or 0)+1
  return 'original_place'
 end
 d.on_secondary_use=function(stack,p)
  handled.ads=(handled.ads or 0)+1
  return 'original_secondary'
 end
 M.registered_items[item]=d
end
for _,f in ipairs(onmods) do f() end
for item in pairs(originals) do
 assert(M.registered_items[item]._xz_zombies_use_bridge,'bridge missing on '..item)
end
local p=player('portrait')
function p:get_pos()return {x=4,y=3.53,z=4.0} end
function p:get_look_dir()return {x=0,y=0,z=1} end
function p:get_properties()return {eye_height=1.47} end
local zoom=false
function p:get_player_control()return {zoom=zoom} end
local held_item='ak47dev:ak47'
function p:get_wielded_item()return {get_name=function()return held_item end} end
M.get_connected_players=function()return {p} end
callbacks.fields(p,'xz_zombies:editor',{stop=true})
local before=handled.ads or 0
local wallpt={type='node',under=placed_at,above={x=4,y=5,z=7}}
local place_result=M.registered_items['ak47dev:ak47'].on_place('STACK',p,wallpt)
assert(place_result=='STACK','USE did not override ADS on wall')
assert(forms.portrait.id=='xz_zombies:configure','Wall buy did not open price')
assert((handled.ads or 0)==before,'USE incorrectly triggered ADS')
-- Secondary USE with no pointed args raycasts at the first node.
local second=M.registered_items['ak47dev:m9'].on_secondary_use('STACK',p)
assert(second=='STACK')
-- On-target and off-target USE must NEVER trigger ADS.
worldnode='mcl_core:stone'
assert(M.registered_items['ak47dev:ak47'].on_secondary_use('STACK',p)=='STACK')
assert(M.registered_items['ak47dev:ak47'].on_place('STACK',p,wallpt)=='STACK')
assert((handled.ads or 0)==before,'off-target USE accidentally zoomed')
-- Ammo crate must still function with original weapon's ammo code.
worldnode='ak47dev:ammo_crate'
assert(M.registered_items['ak47dev:ak47'].on_place('STACK',p,wallpt)=='original_place')
-- Zoom is the single source for ADS and toggles ON PRESS only.
worldnode='mcl_core:stone'
zoom=true;callbacks.step(0.02)
assert((handled.ads or 0)==before+1,'Zoom did not activate ADS')
callbacks.step(0.02);callbacks.step(0.02)
assert((handled.ads or 0)==before+1,'Zoom held retriggered ADS')
zoom=false;callbacks.step(0.02)
zoom=true;callbacks.step(0.02)
assert((handled.ads or 0)==before+2,'Second zoom press did not toggle ADS')
-- A zombified interactable uses dedicated USE even during PLAY.
worldnode='xz_zombies:door'
assert(M.registered_items['ak47dev:m9'].on_secondary_use('STACK',p)=='STACK')
assert(forms.portrait.id=='xz_zombies:configure','Door config not reached')
-- FIX50A new wall placement refuses floor and floating (no supporting wall).
local wall=nodes['xz_zombies:wall_ak47']
worldnode='mcl_core:stone'
nodes['mcl_core:stone']={walkable=true}
M.item_place_node=function(stack,placer,pointed,param2)
  handled.wall_placed=(handled.wall_placed or 0)+1
  handled.param2=param2
  return stack,pointed.above
end
assert(wall.on_place('STACK',p,{type='node',under=placed_at,above={x=4,y=6,z=6}})=='STACK')
assert(not handled.wall_placed,'floor placement should not be allowed')
local vertical_pt={type='node',under=placed_at,above={x=4,y=5,z=7}}
wall.on_place('STACK',p,vertical_pt)
assert(handled.wall_placed==1 and handled.param2==0,'vertical wall did not mount')
worldnode='air'
wall.on_place('STACK',p,vertical_pt)
assert(handled.wall_placed==1,'floating wall buy incorrectly placed')
-- Independent native USE is delivered as /xzuse regardless of active inventory slot.
worldnode='xz_zombies:wall_ak47'
M.get_player_by_name=function(name)if name=='portrait' then return p end end
assert(callbacks.xzuse,'native USE command registration missing')
local ads_before=handled.ads or 0
local ok,msg=callbacks.xzuse('portrait','')
assert(ok and msg=='' and forms.portrait.id=='xz_zombies:configure', 'USE with gun did not interact with wall')
assert((handled.ads or 0)==ads_before,'native USE accidentally activated ADS')
worldnode='xz_zombies:door'
assert(callbacks.xzuse('portrait',''))
assert(forms.portrait.id=='xz_zombies:configure','USE did not open door config')
worldnode='ak47dev:ammo_crate'
nodes['ak47dev:ammo_crate']={on_rightclick=function(...)handled.ammo=(handled.ammo or 0)+1 end}
assert(callbacks.xzuse('portrait',''))
assert(handled.ammo==1,'dedicated USE did not refill ammo crate')
assert((handled.ads or 0)==ads_before,'ammo USE triggered ADS')
print('PASS FIX50A: 28 guns preserved, native USE command, ADS isolation, wall-only placement and ammo crate')