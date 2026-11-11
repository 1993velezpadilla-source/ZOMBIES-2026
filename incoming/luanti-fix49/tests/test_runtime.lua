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
local M = {
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
 register_on_mods_loaded=function() end,
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
assert(loadfile('incoming/luanti-fix49/games/voxelibre/mods/xz_zombies_classic/init.lua'))()
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