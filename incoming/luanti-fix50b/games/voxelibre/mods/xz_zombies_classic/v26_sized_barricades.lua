-- FIX53: 1x1 / 1x2 / 2x1 / 2x2 / 3x3 original NZ:P v26 barricades.
-- Geometry: exact NZ:P Team window.mdl frame (0,6,13,20,27,34,41)
-- re-scaled in the ORIGINAL converter to the selected block opening dimensions.
-- GAMEPLAY: original window.qc six-plank state, +10 repair per .75sec; one
-- strike = one plank. No new fake wood models or behavior.
return function(M,A)
 local SZ={{1,1},{1,2},{2,1},{2,2},{3,3}}
 local names={}
 local function key(pos)
  return ('%d,%d,%d'):format(pos.x,pos.y,pos.z)
 end
 local function fromkey(s)
  local x,y,z=s:match('^(-?%d+),(-?%d+),(-?%d+)$')
  if x then return {x=tonumber(x),y=tonumber(y),z=tonumber(z)} end
 end
 local function nname(stage,w,h)
  return ('xz_zombies:v26_barricade_%d_%dx%d'):format(stage,w,h)
 end
 local PART_SOLID='xz_zombies:v26_barricade_part_solid'
 local PART_OPEN='xz_zombies:v26_barricade_part_open'
 local function part(name)return name==PART_SOLID or name==PART_OPEN end
 -- Match mesh rotation. 4 horizontal facedirs are 0,1,2,3.
 local function offset(pos,u,v,rot)
  local x,z
  if rot==1 then x,z=0,u
  elseif rot==2 then x,z=-u,0
  elseif rot==3 then x,z=0,-u
  else x,z=u,0 end
  return {x=pos.x+x,y=pos.y+v,z=pos.z+z}
 end
 local function iter(pos,w,h,rot,fn)
  for v=0,h-1 do for u=0,w-1 do
   if u~=0 or v~=0 then fn(offset(pos,u,v,rot),u,v) end
  end end
 end
 local function stage_info(pos)
  local n=M.get_node_or_nil(pos)
  if not n then return nil end
  if part(n.name) then
   local parent=fromkey(M.get_meta(pos):get_string('nzp_v26_anchor'))
   if not parent then return nil end
   pos=parent
   n=M.get_node_or_nil(pos)
   if not n then return nil end
  end
  local stage,w,h=n.name:match('^xz_zombies:v26_barricade_([0-6])_(%d)x(%d)$')
  if not stage then return nil end
  stage,w,h=tonumber(stage),tonumber(w),tonumber(h)
  if not names[w..'x'..h] then return nil end
  return pos,stage,w,h,n.param2 or 0
 end

 -- These small extension points let the ORIGINAL v26_runtime.lua drive
 -- repairs, break sounds and score caps even for the multi-cell shapes.
 function A.sized_resolve(pos)
  local a=stage_info(pos)
  return a or pos
 end
 function A.sized_get_stage(pos)
  local _,stage=stage_info(pos)
  return stage
 end
 function A.sized_change_stage(pos,stage)
  local anchor,old,w,h,rot=stage_info(pos)
  if not anchor then return false end
  if stage<0 or stage>6 then return false end
  M.swap_node(anchor,{name=nname(stage,w,h),param2=rot})
  M.get_meta(anchor):set_int('nzp_v26_planks',stage)
  local companion=stage>0 and PART_SOLID or PART_OPEN
  iter(anchor,w,h,rot,function(p)
   local oldnode=M.get_node_or_nil(p)
   if oldnode and part(oldnode.name) and
     M.get_meta(p):get_string('nzp_v26_anchor')==key(anchor) then
    M.swap_node(p,{name=companion,param2=rot})
   end
  end)
  return true
 end

 local function remove_children(pos,w,h,rot)
  iter(pos,w,h,rot,function(p)
   local n=M.get_node_or_nil(p)
   if n and part(n.name) and M.get_meta(p):get_string('nzp_v26_anchor')==key(pos) then
    M.remove_node(p)
   end
  end)
 end

 function A.place_sized(pos,w,h,placer)
  local label=w..'x'..h
  if not names[label] then return false,'Tamaño no reconocido' end
  local dir=placer and placer.get_look_dir and placer:get_look_dir() or {x=0,y=0,z=1}
  local rot=(M.dir_to_facedir and M.dir_to_facedir(dir) or 0)%4
  local who=placer and placer.get_player_name and placer:get_player_name() or ''
  local all={{x=pos.x,y=pos.y,z=pos.z}}
  iter(pos,w,h,rot,function(p) all[#all+1]=p end)
  -- Atomic preflight: never overwrite other map blocks or protected cells.
  for _,p in ipairs(all) do
   local n=M.get_node_or_nil(p)
   if not n or (n.name~='air' and not (M.registered_nodes[n.name] and M.registered_nodes[n.name].buildable_to)) then
    return false,'Espacio ocupado: '..label
   end
   if M.is_protected and M.is_protected(p,who) then return false,'Zona protegida' end
  end
  -- One true ORIGINAL window model across full opening, and one companion
  -- collision cell in each remaining block; all cells share one 6-plank count.
  M.set_node(pos,{name=nname(6,w,h),param2=rot})
  M.get_meta(pos):set_int('nzp_v26_planks',6)
  M.get_meta(pos):set_string('nzp_v26_size',label)
  iter(pos,w,h,rot,function(p)
   M.set_node(p,{name=PART_SOLID,param2=rot})
   M.get_meta(p):set_string('nzp_v26_anchor',key(pos))
  end)
  return true
 end

 for _,dims in ipairs(SZ) do names[dims[1]..'x'..dims[2]]=true end
 -- Existing 1x1 original block names and mesh are left byte-for-byte intact.
 for _,dims in ipairs(SZ) do
  local w,h=dims[1],dims[2]
  if w~=1 or h~=1 then
   for stage=0,6 do
    local full=nname(stage,w,h)
    M.register_node(':'..full,{
     description=('NZ:P v26 | Barricada %dx%d (%d/6)'):format(w,h,stage),
     drawtype=stage>0 and 'mesh' or 'airlike',
     mesh=stage>0 and ('nzp_v26_window_%d_%dx%d.obj'):format(stage,w,h) or nil,
     tiles=stage>0 and {'nzp_v26_window.png'} or nil,
     paramtype='light',paramtype2='facedir',sunlight_propagates=true,
     groups={choppy=2,oddly_breakable_by_hand=2,
       not_in_creative_inventory=stage==6 and 0 or 1},
     selection_box={type='fixed',fixed={-0.5,-0.5,-0.17,w-0.5,h-0.5,0.17}},
     collision_box={type='fixed',fixed={-0.5,-0.5,-0.17,w-0.5,h-0.5,0.17}},
     walkable=stage>0,buildable_to=false,
     on_construct=function(pos)
      local meta=M.get_meta(pos)
      meta:set_int('nzp_v26_planks',stage)
      meta:set_string('nzp_v26_size',w..'x'..h)
      meta:set_string('infotext',('Barricada NZ:P v26 %dx%d | %d/6'):format(w,h,stage))
     end,
     on_rightclick=function(pos,node,p) A.repair(pos,p) end,
     on_destruct=function(pos) remove_children(pos,w,h,M.get_node(pos).param2 or 0) end,
     on_place=stage==6 and function(itemstack,placer,pointed)
      if not placer or not placer:is_player() or not pointed or pointed.type~='node' then return itemstack end
      local yes,err=A.place_sized(pointed.above,w,h,placer)
      if yes then
       if not M.is_creative_enabled or not M.is_creative_enabled(placer:get_player_name()) then
        if itemstack.take_item then itemstack:take_item(1) end
       end
      elseif M.chat_send_player then
       M.chat_send_player(placer:get_player_name(),'[Zombies] '..err)
      end
      return itemstack
     end or nil,
    })
   end
  end
 end
 for _,solid in ipairs({true,false}) do
  local n=solid and PART_SOLID or PART_OPEN
  M.register_node(':'..n,{
   description='NZ:P v26 | barricade companion',
   drawtype='airlike',paramtype='light',paramtype2='facedir',
   sunlight_propagates=true,walkable=solid,pointable=true,
   buildable_to=false,groups={not_in_creative_inventory=1,unbreakable=1},
   selection_box={type='fixed',fixed={-0.5,-0.5,-0.13,0.5,0.5,0.13}},
   collision_box={type='fixed',fixed={-0.5,-0.5,-0.13,0.5,0.5,0.13}},
   on_rightclick=function(pos,node,p) A.repair(pos,p) end,
   on_dig=function(pos,node,digger)
    local anchor=fromkey(M.get_meta(pos):get_string('nzp_v26_anchor'))
    if anchor then M.remove_node(anchor) else M.remove_node(pos) end
   end,
  })
 end
 A.sizes=SZ
 return A
end
