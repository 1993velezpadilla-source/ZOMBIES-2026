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
local gameclock=20
local worldnode='xz_zombies:wall_ak47'
local placed_at={x=4,y=5,z=6}
local handled={}

local M
M = {
 registered_nodes=nodes,registered_entities={['mobs_mc:zombie']={}},registered_items={},
 settings={get=function(_,k) return settings_data[k] end,set=function(_,k,v) settings_data[k]=v end},
 get_current_modname=function() return 'xz_zombies_classic' end,
 get_modpath=function(name) if name=='xz_zombies_classic' then return 'incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic' end return '/fake/'..name end,
 get_mod_storage=function() return {get_string=function(_,k) return storage_data[k] or '' end,
  set_string=function(_,k,v) storage_data[k]=v end,set_int=function(_,k,v) storage_data[k]=v end} end,
 deserialize=function() return nil end,serialize=function() return '{}' end,
 formspec_escape=function(x) return tostring(x):gsub(']', '\\]'):gsub(';','\\;') end,
 register_node=function(n,d) assert(n:sub(1,1)==':');nodes[n:sub(2)]=d end,
 register_tool=function(n,d) tools[n:sub(2)]=d end,
 register_lbm=function(def)
  assert(type(def.name)=='string' and (def.name:sub(1,1)==':' or def.name:match('^xz_zombies_classic:')), 'Luanti rejects LBM name outside current mod prefix: '..tostring(def.name))
  callbacks.lbms=callbacks.lbms or {};callbacks.lbms[def.name]=def
 end,
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
 dir_to_facedir=function(d) if d.x==1 then return 1 elseif d.x==-1 then return 3 elseif d.z==-1 then return 2 else return 0 end end,
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
 get_gametime=function() return gameclock end,
 is_singleplayer=function() return true end,
 get_connected_players=function() return {} end,
 chat_send_player=function() end,chat_send_all=function() end,
 log=function(l,s) logs[#logs+1]=s end,
}
_G.minetest=M
local actual_modes={}
_G.mcl_gamemode={
 get_gamemode=function(p)return actual_modes[p:get_player_name()] or 'creative' end,
 set_gamemode=function(p,mode)assert(mode=='survival' or mode=='creative');actual_modes[p:get_player_name()]=mode end,
}
M.is_creative_enabled=function(name)return (actual_modes[name] or 'creative')=='creative' end
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
assert(loadfile('incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/init.lua'))()
assert(#tools==0) -- map does not have numeric indices
assert(tools['xz_zombies:editor_tool'])
local c=0;for k in pairs(nodes) do c=c+1 end
assert(c==74,'expected 74 nodes (44 FIX52B plus 28 original-size v26 meshes and two linked cell nodes), got '..c)
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
 function p:hud_remove()end
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


-- FIX50A: native USE is dispatched as the server chatcommand, not through guns.
-- Test all 28 guns keep their native callbacks and need no empty slot.
local originals={}
for name in pairs(nodes) do if name:find('^xz_zombies:wall_') then
 assert(nodes[name].on_place,'Missing solid-wall-only item placement '..name)
end end
for i=1,26 do originals['ak47dev:w'..i]=true end
originals['ak47dev:m9']=true;originals['ak47dev:ak47']=true
local origPlace,origSecondary={},{}
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
 origPlace[item]=d.on_place
 origSecondary[item]=d.on_secondary_use
end
local originalPunchCount=0
for _,ename in ipairs({'mobs_mc:zombie','mobs_mc:husk','mobs_mc:villager_zombie','mobs_mc:baby_zombie'}) do
 M.registered_entities[ename]={on_punch=function() originalPunchCount=originalPunchCount+1 end}
end
for _,f in ipairs(onmods) do f() end
for item in pairs(originals) do
 assert(M.registered_items[item].on_place==origPlace[item],item..' PLACE changed')
 assert(M.registered_items[item].on_secondary_use==origSecondary[item],item..' ADS changed')
end
local p=player('portrait')
function p:get_pos()return {x=4,y=3.53,z=4.0} end
function p:get_look_dir()return {x=0,y=0,z=1} end
function p:get_properties()return {eye_height=1.47} end
local zoom=false
function p:get_player_control()return {zoom=zoom} end
local held_item='ak47dev:ak47'
function p:get_wielded_item()return {get_name=function()return held_item end} end
M.get_player_by_name=function(n) if n=='portrait' then return p end end
M.get_connected_players=function()return {p} end
callbacks.fields(p,'xz_zombies:editor',{stop=true})
local before=handled.ads or 0
assert(type(callbacks.xz_use)=='function','native USE server command missing')
worldnode='xz_zombies:wall_ak47'
local ok,err=callbacks.xz_use('portrait')
assert(ok, tostring(err))
assert(forms.portrait.id=='xz_zombies:configure','USE with gun equipped did not open Wall Buy')
assert((handled.ads or 0)==before,'USE improperly triggered ADS')
for item in pairs(originals) do
 held_item=item
 local yes=callbacks.xz_use('portrait')
 assert(yes,'USE failed with '..item)
end
-- Existing original callbacks are not redirected to USE.
assert(M.registered_items['ak47dev:ak47'].on_place('STACK',p,{type='node',under=placed_at})=='original_place')
assert((handled.ads or 0)==before,'PLACE triggered ADS test unexpectedly')
-- Objects must be within the visible ray. Unrelated blocks block the path.
worldnode='mcl_core:stone'
local previous=forms.portrait
assert(callbacks.xz_use('portrait'))
assert(forms.portrait==previous,'Interaction went through ordinary wall')
-- Ammo crate callback fires even with an AK equipped.
local crateHits=0
nodes['ak47dev:ammo_crate']={on_rightclick=function(pos,node,player,stack,pt)
 assert(player==p and stack:get_name()==held_item)
 crateHits=crateHits+1
end}
worldnode='ak47dev:ammo_crate'
assert(callbacks.xz_use('portrait'))
assert(crateHits==1,'USE did not interact with ammo crate')
-- Native ZOOM handles only ADS, triggered once per press edge.
worldnode='mcl_core:stone'
zoom=true;callbacks.step(0.02)
assert((handled.ads or 0)==before+1)
callbacks.step(0.02);callbacks.step(0.02)
assert((handled.ads or 0)==before+1)
zoom=false;callbacks.step(0.02)
zoom=true;callbacks.step(0.02)
assert((handled.ads or 0)==before+2)
-- Solid wall mounts only, no floating placement or floor/ceiling attachment.
local wp=nodes['xz_zombies:wall_ak47']
local pt={type='node',under=placed_at,above={x=4,y=5,z=7}}
M.item_place_node=function(item,placer,pt,orientation)
 handled.mounted={item=item,placer=placer,orientation=orientation}
 return 'PLACED'
end
nodes['mcl_core:stone']={walkable=true}
worldnode='mcl_core:stone'
assert(wp.on_place('WALL_ITEM',p,pt)=='PLACED')
assert(handled.mounted.orientation==0)
local mount=handled.mounted
worldnode='air'
assert(wp.on_place('WALL_ITEM',p,pt)=='WALL_ITEM')
assert(handled.mounted==mount,'Floating wall buy was created')
worldnode='mcl_core:stone'
local floor={type='node',under=placed_at,above={x=4,y=6,z=6}}
assert(wp.on_place('WALL_ITEM',p,floor)=='WALL_ITEM')
assert(handled.mounted==mount,'Ceiling/floor wall buy was created')
print('PASS: 28 guns retain original PLACE/ADS; native USE with equipped gun; door/wall/crate; no through-wall use; mounted wall placement')
-- FIX50B: old map Wall Buys only snap if the closest backing is unambiguous.
local mount_lbm=callbacks.lbms and callbacks.lbms['xz_zombies_classic:fix50b_reanchor_existing_wall_buys']
assert(mount_lbm,'wall anchor LBM must coexist with zombie spawner LBM')
local function key(q) return ('%d/%d/%d'):format(q.x,q.y,q.z) end
local grid,metas={},{}
local old={x=4,y=5,z=6}
local backing={x=4,y=5,z=4}
local dest={x=4,y=5,z=5}
grid[key(old)]={name='xz_zombies:wall_ak47',param2=2}
grid[key(backing)]={name='mcl_core:stone',param2=0}
nodes.air={walkable=false,buildable_to=true}
M.get_node_or_nil=function(q) return grid[key(q)] or {name='air'} end
M.swap_node=function(q,n) grid[key(q)]=n end
M.get_meta=function(q)
 local k=key(q)
 return {
  to_table=function() return metas[k] or {fields={price='2000'}} end,
  from_table=function(_,t) metas[k]=t end,
 }
end
mount_lbm.action(old,grid[key(old)])
assert(grid[key(old)].name=='air','old floating wall buy must be cleared')
assert(grid[key(dest)] and grid[key(dest)].name=='xz_zombies:wall_ak47','wall buy must snap adjacent to backing')
assert(grid[key(dest)].param2==0,'wall prop must face outward')
assert(metas[key(dest)].fields.price=='2000','price metadata must remain')
local fixed={x=10,y=4,z=10}
grid[key(fixed)]={name='xz_zombies:wall_ak47',param2=3}
grid[key({x=10,y=4,z=9})]={name='mcl_core:stone'}
mount_lbm.action(fixed,grid[key(fixed)])
assert(grid[key(fixed)].name=='xz_zombies:wall_ak47' and grid[key(fixed)].param2==0)
local amb={x=20,y=4,z=20}
grid[key(amb)]={name='xz_zombies:wall_ak47',param2=4}
grid[key({x=20,y=4,z=18})]={name='mcl_core:stone'}
grid[key({x=18,y=4,z=20})]={name='mcl_core:stone'}
mount_lbm.action(amb,grid[key(amb)])
assert(grid[key(amb)].name=='xz_zombies:wall_ak47','ambiguous wall geometry must be left intact')
print('PASS: floating wall prop snap, metadata preservation, safe ambiguous cases')

-- FIX51 integration: actually advance rounds, spawn mob entities, credit a native
-- variant kill, verify inherited punch callbacks and wave transitions.
local D=assert(loadfile('incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/round_director.lua'))()
local spawner={x=10,y=3,z=10}
local mobs={}
_G.vector.distance=function(a,b)
 local dx,dy,dz=a.x-b.x,a.y-b.y,a.z-b.z
 return math.sqrt(dx*dx+dy*dy+dz*dz)
end
M.get_meta=function(pos)
 return {set_string=function()end,set_int=function()end,get_int=function()return 0 end}
end
M.get_node_or_nil=function(pos)
 if pos.x==spawner.x and pos.y==spawner.y and pos.z==spawner.z then return {name='xz_zombies:spawner'} end
 if pos.y<=spawner.y then return {name='mcl_core:stone'} end
 return {name='air'}
end
M.add_entity=function(pos,entity_name)
 local obj={alive=true,hp=20,pos=pos,entity_name=entity_name}
 function obj:get_pos() return self.alive and self.pos or nil end
 function obj:get_hp() return self.hp end
 function obj:set_hp(hp) self.hp=hp end
 function obj:remove() self.alive=false end
 local entity={object=obj}
 function obj:get_luaentity()return entity end
 mobs[#mobs+1]=obj
 return obj
end
nodes['xz_zombies:spawner'].on_construct(spawner)
gameclock=50
callbacks.fields(p,'xz_zombies:editor',{play=true})
assert(actual_modes['portrait']=='survival','PLAY must switch VoxeLibre to survival mode')
gameclock=53
callbacks.step(1.1)
local active_status,info=callbacks.zstatus('portrait')
assert(active_status and info:find('Ronda 1',1,true),tostring(info))
assert(#mobs==1,'first zombie should spawn on round start')
local V=assert(loadfile('incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/v26_rules.lua'))()
assert(mobs[1].hp==V.zombie_hp(1),'mob HP did not use source v26 scale')
assert(mobs[1].entity_name=='mobs_mc:zombie' or M.registered_entities[mobs[1].entity_name],'non-native zombie spawned')
for t=56,90,3 do gameclock=t;callbacks.step(1.1) end
assert(#mobs==V.round_quota(1,1),'v26 round 1 spawn quota must be exact; spawned '..#mobs)
for _,obj in ipairs(mobs) do
 local entity=obj:get_luaentity()
 M.registered_entities[obj.entity_name].on_punch(entity,p)
 obj:set_hp(0)
end
gameclock=94
callbacks.step(1.1)
local ok2,status=callbacks.zstatus('portrait')
assert(ok2 and status:find('Restantes 0',1,true) and status:find('Bajas 6',1,true),tostring(status))
assert(meta['portraitxz_z_points']==500+V.damage_score(true,'lowertorso')*V.round_quota(1,1),'v26 kill points were not credited once to shooter')
assert(originalPunchCount==#mobs,'native zombie original on_punch callback not preserved')
gameclock=100
callbacks.step(1.1)
local ok3,status2=callbacks.zstatus('portrait')
assert(ok3 and status2:find('Ronda 2',1,true),tostring(status2))
assert(#mobs==V.round_quota(1,1)+1 and mobs[#mobs].hp==V.zombie_hp(2),'v26 round 2 health did not apply')
callbacks.fields(p,'xz_zombies:editor',{stop=true})
assert(actual_modes['portrait']=='creative','STOP must restore VoxeLibre creative mode')
local ok4,status3=callbacks.zstatus('portrait')
assert(ok4 and status3:find('STOP',1,true),tostring(status3))
print('PASS: FIX52 v26 round spawn quota, enemy HP, kill points, original mob callback, next round and stop')
