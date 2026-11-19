-- FIX61 acceptance tests. Real generated CC0 source dimensions and Lua APIs.
local mod=assert(arg[1], 'pass compiled mod directory')
local manifest=assert(loadfile(mod..'/polyhaven_fort_manifest.lua'))()
assert(#manifest>0)
local one=manifest[1]
assert(type(one.natural_scale)=='number' and one.natural_scale>0)
assert(type(one.source_extent)=='table' and #one.source_extent==3)
local mx=math.max(one.source_extent[1],one.source_extent[2],one.source_extent[3])
assert(math.abs(one.natural_scale-mx/.96)<.002,'glTF source dimension lost')
local defs,world,entities,forms,store={},{},{},{},{}
local fields,onleave,globalstep
local blocker=false
local game=false
local open=true
local stackname='xz_zombies:'..one.id
local uid=0
local M
local function key(p) return ('%.2f,%.2f,%.2f'):format(p.x,p.y,p.z) end
local function deep(v)
 if type(v)~='table' then return v end
 local d={}
 for k,x in pairs(v) do d[k]=deep(x) end
 return d
end
local function count_entities(ename,alive_only)
 local count=0
 for _,o in ipairs(entities) do
  if o.name==ename and (not alive_only or o:get_pos()) then count=count+1 end
 end
 return count
end
M={
 registered_nodes={},
 serialize=function(dat)
  uid=uid+1
  local id='SAVE_'..uid
  store[id]=deep(dat)
  return id
 end,
 deserialize=function(s) return deep(store[s]) end,
 is_singleplayer=function()return true end,
 is_protected=function()return blocker end,
 is_creative_enabled=function()return true end,
 formspec_escape=function(s)return tostring(s):gsub(']','\\]'):gsub(';','\\;') end,
 get_player_window_information=function()
  return {max_formspec_size={x=5.35,y=4.8},touch_controls=true}
 end,
 register_entity=function(name,d)assert(name:sub(1,1)==':');defs[name:sub(2)]=d end,
 register_node=function(name,d)assert(name:sub(1,1)==':');M.registered_nodes[name:sub(2)]=d end,
 get_node_or_nil=function(p)return world[key(p)] or {name='air',param2=0} end,
 remove_node=function(p)world[key(p)]={name='air'};return true end,
 swap_node=function(p,n)world[key(p)]=n end,
 register_globalstep=function(fn)globalstep=fn end,
 register_on_player_receive_fields=function(fn)fields=fn end,
 register_on_leaveplayer=function(fn)onleave=fn end,
 get_connected_players=function()return {} end,
 show_formspec=function(w,form,s)forms[w]={form=form,s=s}end,
 chat_send_player=function()end,
 log=function()end,
}
M.add_entity=function(pos,ename,staticdata)
 local d=assert(defs[ename],'Missing entity definition '..ename)
 local o={name=ename,pos=deep(pos),props=deep(d.initial_properties or {})}
 local lua=setmetatable({object=o,name=ename},{__index=d})
 o.lua=lua
 function o:get_pos()return self.pos end
 function o:set_pos(p)self.pos=deep(p)end
 function o:remove()self.pos=nil;self.removed=true end
 function o:get_luaentity()return self.lua end
 function o:set_properties(p)for k,v in pairs(p) do self.props[k]=deep(v) end end
 function o:set_rotation(v)self.rot=deep(v)end
 function o:set_yaw(v)self.yaw=v end
 function o:set_armor_groups(t)self.armor=t end
 entities[#entities+1]=o
 if lua.on_activate then lua:on_activate(staticdata or '') end
 return o
end
local ray_target
M.raycast=function(a,b,objs,liq)
 local sent=false
 return function()
  if sent then return nil end
  sent=true
  if ray_target and (objs or ray_target.type=='node') then return ray_target end
  return nil
 end
end
local player={
 get_player_name=function()return 'android' end,
 is_player=function()return true end,
 get_wielded_item=function()
  return {get_name=function()return stackname end,take_item=function()end}
 end,
 get_pos=function()return {x=1,y=2,z=3} end,
 get_look_dir=function()return {x=0,y=0,z=1} end,
 get_properties=function()return {eye_height=1.47} end,
}
local editor=assert(loadfile(mod..'/fort_editor_v2.lua'))()(M,mod,function()return not game end)
assert(type(editor.place_new)=='function' and type(editor.place_generic)=='function')
assert(type(editor.use_target)=='function')
local fort=assert(loadfile(mod..'/polyhaven_fort.lua'))()(M,mod,editor)
assert(fort==#manifest)
local oldpos={x=11,y=3,z=15}
world[key(oldpos)]={name='xz_zombies:'..one.id,param2=1}
-- Legacy maps are untouched by startup; no mass migration.
assert(count_entities('xz_zombies_classic:fort_architecture')==0)
-- Source-size, not normalized 1m, placement at decimal coordinates.
local hit={type='node',
 under={x=3,y=4,z=4},above={x=3,y=5,z=4},
 intersection_point={x=3.17,y=4.50,z=4.67}}
local stack={
 get_name=function()return 'xz_zombies:'..one.id end,
 take_item=function()error('creative should not consume building pieces')end
}
local unchanged=editor.place_new(stack,player,hit)
assert(unchanged==stack)
local name='xz_zombies_classic:fort_architecture'
assert(count_entities(name,true)==1)
local arch
for _,o in ipairs(entities) do if o.name==name then arch=o end end
local l=arch.lua
assert(l.arch_id==one.id and l.kind=='mesh')
assert(math.abs(l.scale-one.natural_scale)<.001,'DEFAULT MESH SIZE not original')
assert(arch.props.mesh==one.mesh)
assert(math.abs(arch:get_pos().x-3.17)<.001 and math.abs(arch:get_pos().z-4.67)<.001,'grid snapped free placement')
assert(math.abs(arch:get_pos().y+(one.box[2]*l.scale)-4.5)<.0001,'model started below ground')
assert(arch.props.visual_size.x==10*l.scale)
assert(arch.props.pointable and arch.props.static_save)
assert(arch.armor.immortal==1)
local fs=forms.android.s
assert(fs:find('ZOMBIES    3D BUILDER',1,true))
assert(not fs:find('scroll_container',1,true),'touch editor must not require scrollbar')
assert(fs:find('tab_1',1,true) and fs:find('tab_4',1,true))
assert(fs:find('MOVER',1,true) and fs:find('FISICA',1,true))
local function act(t) assert(fields(player,'xz_zombies:fort_transform',t)) end
local y0=arch:get_pos().y+one.box[2]*l.scale
act({tab_2=true})
act({scale_big_plus=true})
assert(math.abs(l.scale-(one.natural_scale+1))<.01)
assert(math.abs(arch:get_pos().y+one.box[2]*l.scale-y0)<.001,'resizing dug into terrain')
assert(arch.props.visual_size.x==10*l.scale)
act({tab_1=true})
local x0=arch:get_pos().x
act({precision_1=true})
act({move_X_plus=true})
assert(math.abs(arch:get_pos().x-x0-.05)<.0001,'sub-node movement failed')
local y1=arch:get_pos().y
act({move_Y_minus=true})
assert(math.abs(arch:get_pos().y-y1+.05)<.0001,'free vertical movement failed')
act({tab_3=true})
act({axis_x_plus=true})
act({axis_z_minus=true})
assert(math.abs(l.rotation.x-math.pi/12)<.0001)
assert(math.abs(l.rotation.z-2*math.pi+math.pi/12)<.0001)
act({tab_4=true})
act({mode_arch=true})
assert(l.collision_mode=='arch')
assert(arch.props.physical==false,'arch has a solid cube blocking passage')
assert(count_entities('xz_zombies_classic:fort_collision_part',true)==3,'arch requires 3 actual contact surfaces')
act({mode_stairs=true})
assert(arch.props.physical==false,'stair collider must not be one huge cube')
local steps=count_entities('xz_zombies_classic:fort_collision_part',true)
assert(steps>=8 and steps<=24,'stair step collider count')
act({mode_none=true})
assert(arch.props.physical==false)
assert(count_entities('xz_zombies_classic:fort_collision_part',true)==0)
act({mode_solid=true})
assert(arch.props.physical==true)
-- Once saved, position, scale, angles, mesh and hitbox config survive reload.
local save=l:get_staticdata()
local restored=M.add_entity(arch:get_pos(),name,save)
assert(restored and restored.lua.arch_id==l.arch_id)
assert(math.abs(restored.lua.scale-l.scale)<.0001)
assert(restored.lua.collision_mode=='solid')
assert(math.abs(restored.rot.x-l.rotation.x)<.0001)
assert(restored:get_pos().x==arch:get_pos().x)
assert(restored.props.mesh==one.mesh)
act({close=true})
assert(arch:get_pos() and restored:get_pos(),'closing editor deleted saved architecture')
-- Legacy 1x FIX58 nodes remain, and can convert to freeform only when touched.
stackname=''
assert(editor.try_select(player,oldpos,false))
assert(world[key(oldpos)].name=='xz_zombies:'..one.id)
act({tab_1=true})
act({move_Z_plus=true})
assert(world[key(oldpos)].name=='air','legacy node failed to migrate when moved')
-- Any ordinary stone block uses the same editor if intentionally selected.
M.registered_nodes['mcl_core:stone']={walkable=true,description='Stone'}
local stonepos={x=20,y=7,z=20}
world[key(stonepos)]={name='mcl_core:stone',param2=0}
assert(editor.set_mode(player,true))
stackname='ak47dev:ak47'
assert(editor.try_select(player,stonepos,true),'admin USE must work while gun held')
act({tab_1=true})
act({move_X_plus=true})
assert(world[key(stonepos)].name=='air','ordinary cube not promoted to editable 3D item')
local generic
for _,o in ipairs(entities) do if o.name==name and o.lua.arch_id=='mcl_core:stone' then generic=o end end
assert(generic and generic.props.visual=='wielditem' and generic.props.wield_item=='mcl_core:stone')
assert(math.abs(generic.props.visual_size.x-.667)<.001)
act({close=true})
-- Objects can be pointed and edited with guns in the hotbar; no empty slot.
ray_target={type='object',ref=arch}
assert(editor.use_target(player)==true)
assert(forms.android.form=='xz_zombies:fort_transform')
act({quit=true})
-- Protection blocks editing without modifying original props.
blocker=true
assert(not editor.try_select_object(player,arch,true))
blocker=false
game=true
assert(not editor.try_select_object(player,arch,true))
game=false
assert(editor.try_select_object(player,arch,true))
onleave(player)
assert(arch:get_pos(),'disconnect accidentally removed a map object')
print('PASS FIX61: true source dimensions, 3D free placement, persistent XYZ transforms, ground anchoring, premium no-scroll touch, arch + stair compound physics, generic nodes and USE with equipped gun')
