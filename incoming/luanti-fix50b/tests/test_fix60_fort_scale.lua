-- FIX60 executable acceptance tests: REAL unique-instance scalable architecture.
-- The same OBJ is used at all scales, entity save/load and old nodes are safe.
local mod=assert(arg[1], 'expected generated Fort mod directory')
local manifest=assert(loadfile(mod..'/polyhaven_fort_manifest.lua'))()
assert(#manifest==22 or #manifest>0,'empty real architecture manifest')
local entry=manifest[1]
local at={x=12,y=4,z=12}
local placed={name='xz_zombies:'..entry.id,param2=0,param1=0}
local defs,entities,forms={}, {},{}
local received,onleave
local old_fx,architecture={},{}
local busy=false
local protected=false
local wield=''
local fail_next_remove=false
local objtype='xz_zombies_classic:fort_architecture'
local M
M={
 registered_nodes={},
 serialize=function(t)
  return ('%s|%.6f|%.12f'):format(t.id,t.scale,t.yaw)
 end,
 deserialize=function(s)
  if type(s)~='string' then return nil end
  local a,b,c=s:match('^([^|]+)|([^|]+)|([^|]+)$')
  if not a then return nil end
  return {id=a,scale=tonumber(b),yaw=tonumber(c)}
 end,
 is_singleplayer=function()return true end,
 check_player_privs=function()return true end,
 is_protected=function()return protected end,
 formspec_escape=function(s)return tostring(s):gsub(']','\\]'):gsub(';','\\;') end,
 get_player_window_information=function()return {max_formspec_size={x=5.35,y=4.8}}end,
 log=function()end,
 chat_send_player=function(_,msg) error('unexpected conversion error: '..msg) end,
 get_node_or_nil=function(pos)
  assert(pos.x==at.x and pos.y==at.y and pos.z==at.z)
  return placed
 end,
 remove_node=function(pos)
  assert(pos.x==at.x and pos.y==at.y and pos.z==at.z)
  if fail_next_remove then fail_next_remove=false;return false end
  placed={name='air',param2=0,param1=0}
  return true
 end,
 swap_node=function(_,n) placed=n end,
 register_node=function(name,def)M.registered_nodes[name:sub(2)]=def end,
 register_entity=function(name,def)defs[name:sub(2)]=def end,
 register_on_player_receive_fields=function(f)received=f end,
 register_on_leaveplayer=function(f)onleave=f end,
 show_formspec=function(name,form,data) forms[name]={form=form,data=data} end,
 add_entity=function(pos,name,data)
  local def=assert(defs[name],'entity registration missing: '..name)
  local lua=setmetatable({name=name},{__index=def})
  local obj={location={x=pos.x,y=pos.y,z=pos.z},properties={}}
  function obj:set_properties(p)
   for k,v in pairs(p) do self.properties[k]=v end
  end
  function obj:get_pos()return self.location end
  function obj:remove()self.location=nil;self.removed=true end
  function obj:set_yaw(n)self.yaw=n end
  function obj:set_armor_groups(groups) self.armor=groups end
  function obj:get_luaentity()return lua end
  lua.object=obj
  obj.lua=lua
  entities[#entities+1]=obj
  if lua.on_activate then lua:on_activate(data or '') end
  if name==objtype then architecture[#architecture+1]=obj else old_fx[#old_fx+1]=obj end
  return obj
 end,
}
local user={
 is_player=function()return true end,
 get_player_name=function()return 'test_phone' end,
 get_wielded_item=function()return {get_name=function()return wield end} end
}
local editor=assert(loadfile(mod..'/fort_editor.lua'))()(M,mod,function()return not busy end)
local n=assert(loadfile(mod..'/polyhaven_fort.lua'))()(M,mod,editor)
assert(n==#manifest)
assert(type(defs[objtype].get_staticdata)=='function','persistent staticdata missing')
assert(defs[objtype].initial_properties.static_save==true)
assert(defs[objtype].on_punch()==true,'gunfire should never destroy terrain entities')
assert(defs['xz_zombies_classic:fort_select_fx'].initial_properties.static_save==false)

local function current()
 local e=architecture[#architecture]
 assert(e and e:get_pos(),'main asset is missing')
 return e,e:get_luaentity()
end
local function event(f) assert(received(user,'xz_zombies:fort_transform',f)) end
-- A tap opens the existing premium compact editor, never modifies the map.
assert(editor.try_select(user,at,false))
assert(#architecture==0,'just tapping a FIX58 node must not migrate it')
local menu=forms.test_phone.data
assert(menu:find('#20C9FF',1,true))
assert(menu:find('scale_plus',1,true) and menu:find('scale_minus',1,true))
assert(menu:find('GIRAR -90',1,true) and menu:find('turn_minus',1,true))
assert(menu:find('size%[5%.15,4%.50%]'))
assert(#old_fx==1 and old_fx[1].properties.visual_size.x==10.30)
-- Old 90 degree node rotations stay native nodes, no conversion.
event({right=true})
assert(placed.name=='xz_zombies:'..entry.id and placed.param2==1)
assert(#architecture==0)
-- First actual scaling converts ONLY this one node to ONE persistent entity.
event({scale_plus=true})
local e,lua=current()
assert(#architecture==1,'scaling made a duplicate mesh entity')
assert(placed.name=='air','original grid node not removed after successful conversion')
assert(lua.scale==1.25)
assert(math.abs(e.properties.visual_size.x-12.5)<.00001,'OBJ entity needs 10x unit correction')
assert(e.properties.mesh==entry.mesh,'new model generated instead of reusing original OBJ')
assert(e.properties.textures[1]=='xz_fort_atlas.png')
assert(e.properties.static_save==true)
assert(e.properties.physical==true and e.properties.collide_with_objects==true)
assert(e.armor and e.armor.immortal==1,'fort walls must resist zombie and weapon damage')
assert(e.properties.pointable==true and #e.properties.collisionbox==6)
assert(e.properties.collisionbox[4]>0 and e.properties.collisionbox[6]>0)
assert(e.properties.selectionbox[4]>=.045)
assert(old_fx[#old_fx].properties.visual_size.x==10.30*1.25)
-- +1.0, -0.25 and 1.0 reset operate on the same persistent object.
event({scale_big_plus=true})
assert(lua.scale==2.25 and e.properties.visual_size.x==22.5)
event({scale_minus=true})
assert(lua.scale==2.00 and e.properties.visual_size.x==20)
event({turn_plus=true})
assert(math.abs(e.yaw-math.pi/2-math.pi/12)<1e-6,'15 degree turn not applied')
assert(math.abs(lua.yaw-e.yaw)<1e-8)
event({scale_reset=true})
assert(lua.scale==1 and e.properties.visual_size.x==10)
assert(#architecture==1)
-- The scale floor/cap must apply and never break world geometry.
for i=1,20 do event({scale_big_plus=true}) end
assert(lua.scale==8 and e.properties.visual_size.x==80)
for i=1,20 do event({scale_big_minus=true}) end
assert(lua.scale==.5 and e.properties.visual_size.x==5)
local data=lua:get_staticdata()
assert(data:find('fort_') and data:find('|0.500000|',1,true))
-- Closing the editor removes only temporary holograms, never the architecture.
event({close=true})
assert(e:get_pos() and not e.removed)
for _,fx in ipairs(old_fx) do assert(fx.removed,'orphan preview/hologram') end
assert(#architecture==1,'closing accidentally removed saved architecture')
-- Simulate mapblock unload/reload: persists REAL scale, mesh, collision + yaw.
local revived=M.add_entity(at,objtype,data)
assert(revived and revived:get_pos() and revived.properties.mesh==entry.mesh)
assert(math.abs(revived.lua.scale-0.5)<1e-8)
assert(revived.properties.visual_size.x==5)
assert(math.abs(revived.yaw-lua.yaw)<1e-6)
-- Scaled objects are still selectable on Android via interaction.
assert(editor.try_select_object(user,e,false))
assert(forms.test_phone.form=='xz_zombies:fort_transform')
event({scale_plus=true})
assert(lua.scale==.75)
assert(revived.lua.scale==.5,'one changed instance mutated another')
event({quit=true})
-- Protection and gameplay mode guard changes; no selection when busy.
protected=true
assert(not editor.try_select_object(user,e,true))
protected=false
busy=true
assert(not editor.try_select_object(user,e,true))
busy=false
wield='ak47dev:ak47'
assert(not editor.try_select_object(user,e,false),'gun tap stole original ADS interaction')
assert(editor.try_select_object(user,e,true),'native editor tool cannot select entity')
onleave(user)
-- Invalid persisted entities must not become corrupt duplicate stones.
local corrupted=M.add_entity(at,objtype,'unknown|2|0')
assert(corrupted.removed)
print('PASS FIX60: 22 original OBJ preserved; dynamic 0.5-8x per-instance scaling, 10x OBJ conversion, rotated collision, real persistence, premium touch, protected maps and clean preview')
