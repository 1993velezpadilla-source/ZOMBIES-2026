-- FIX60: TRUE per-instance scale for the 22 original Poly Haven OBJ meshes.
-- Uses a persisted Lua entity ONLY when scaling a node the first time.
-- Old FIX58/FIX59 nodes and maps remain untouched until the user scales them.
-- OBJ nodes use 1 mesh unit per node; entities use 10 mesh units per node.
return function(M, modpath, may_edit)
 local source=io.open(modpath..'/polyhaven_fort_manifest.lua','rb')
 if not source then return {try_select=function()return false end,try_select_object=function()return false end} end
 source:close()

 local manifest=assert(loadfile(modpath..'/polyhaven_fort_manifest.lua'))()
 local pieces,by_id={},{}
 for _,item in ipairs(manifest) do
  pieces['xz_zombies:'..item.id]=item
  by_id[item.id]=item
 end
 local chosen={}
 local fx_name='xz_zombies_classic:fort_select_fx'
 local entity_name='xz_zombies_classic:fort_architecture'
 local form_name='xz_zombies:fort_transform'
 local min_scale,max_scale=0.50,8.0

 local function finite(n)
  return type(n)=='number' and n==n and n~=math.huge and n~=-math.huge
 end
 local function clamp(n,a,b)
  if not finite(n) then return a end
  return math.max(a,math.min(b,n))
 end
 local function wrap_yaw(n)
  if not finite(n) then return 0 end
  return n%(2*math.pi)
 end
 local function can_edit(p,pos)
  if not p or type(p.is_player)~='function' or not p:is_player() then return false end
  if may_edit and not may_edit() then return false end
  if not (M.is_singleplayer and M.is_singleplayer())
   and not (M.check_player_privs and M.check_player_privs(p,{server=true})) then return false end
  if pos and M.is_protected and M.is_protected(pos,p:get_player_name()) then return false end
  return true
 end
 local function held_allowed(p,explicit_tool)
  if explicit_tool then return true end
  local stack=p.get_wielded_item and p:get_wielded_item()
  local held=stack and stack.get_name and stack:get_name() or ''
  return held=='' or held=='xz_zombies:editor_tool'
 end
 local function direction_yaw(param2)
  if M.facedir_to_dir and M.dir_to_yaw then
   return M.dir_to_yaw(M.facedir_to_dir(param2 or 0))
  end
  return (param2 or 0)%4*math.pi/2
 end
 local function get_node_piece(pos)
  if not pos or not M.get_node_or_nil then return nil,nil end
  local node=M.get_node_or_nil(pos)
  return node and pieces[node.name],node
 end
 local function valid_entity(obj)
  if not obj or not obj.get_pos or not obj:get_pos() or not obj.get_luaentity then return nil end
  local lua=obj:get_luaentity()
  if lua and lua.fort_id and by_id[lua.fort_id] and lua.name==entity_name then return lua end
  return nil
 end
 -- Axis-aligned bounding boxes cannot follow the exact silhouette of an
 -- arbitrary rotated mesh. Use a conservative rotated AABB for touch + physics.
 local function scaled_box(item,scale,yaw)
  local b=item.box or {-.48,-.48,-.48,.48,.48,.48}
  local hx=math.max(math.abs(b[1]),math.abs(b[4]))*scale
  local hy=math.max(math.abs(b[2]),math.abs(b[5]))*scale
  local hz=math.max(math.abs(b[3]),math.abs(b[6]))*scale
  local co,si=math.abs(math.cos(yaw)),math.abs(math.sin(yaw))
  local x=math.max(.045,co*hx+si*hz)
  local z=math.max(.045,si*hx+co*hz)
  local y=math.max(.05,hy)
  return {-x,-y,-z,x,y,z}
 end
 local function apply(lua)
  local item=by_id[lua.fort_id]
  if not item or not lua.object then return false end
  lua.scale=clamp(lua.scale or 1,min_scale,max_scale)
  lua.yaw=wrap_yaw(lua.yaw or 0)
  local box=scaled_box(item,lua.scale,lua.yaw)
  -- CRITICAL OBJ node-to-entity 10x adjustment: 10*scale recreates
  -- exactly the same 1x proportions as the FIX58 original OBJ node.
  lua.object:set_properties({
   visual='mesh',mesh=item.mesh,textures={'xz_fort_atlas.png'},
   visual_size={x=10*lua.scale,y=10*lua.scale,z=10*lua.scale},
   pointable=true,physical=true,collide_with_objects=true,
   selectionbox=box,collisionbox=box,static_save=true,
   shaded=true,glow=0
  })
  lua.object:set_yaw(lua.yaw)
  if lua.object.set_armor_groups then lua.object:set_armor_groups({immortal=1}) end
  return true
 end

 local editor -- late-bound for entity callbacks
 M.register_entity(':'..entity_name,{
  initial_properties={
   physical=true,collide_with_objects=true,pointable=true,
   visual='mesh',mesh='xz_fort_01.obj',
   textures={'xz_fort_atlas.png'},
   visual_size={x=10,y=10,z=10},
   selectionbox={-.48,-.48,-.48,.48,.48,.48},
   collisionbox={-.48,-.48,-.48,.48,.48,.48},
   static_save=true,
  },
  on_activate=function(self,staticdata)
   -- No anonymous placeholder entity is ever left behind.
   local data=type(staticdata)=='string' and staticdata~=''
       and M.deserialize and M.deserialize(staticdata) or nil
   if type(data)~='table' or not by_id[data.id] then
    if self.object then self.object:remove() end
    return
   end
   self.fort_id=data.id
   self.scale=clamp(data.scale or 1,min_scale,max_scale)
   self.yaw=wrap_yaw(data.yaw or 0)
   apply(self)
  end,
  get_staticdata=function(self)
   if not self.fort_id or not by_id[self.fort_id] or not M.serialize then return '' end
   return M.serialize({id=self.fort_id,scale=self.scale,yaw=self.yaw,version=1})
  end,
  -- Architectural entities are terrain: weapons must never destroy them.
  on_punch=function() return true end,
  on_rightclick=function(self,p)
   if editor then editor.try_select_object(p,self.object,false) end
  end,
 })
 M.register_entity(':'..fx_name,{
  initial_properties={
   physical=false,collide_with_objects=false,pointable=false,
   visual='mesh',mesh='xz_fort_01.obj',
   textures={'xz_fort_atlas.png^[colorize:#00B8FF:200'},
   -- FIX59's 1.035x OBJ highlight was actually one tenth of node size.
   visual_size={x=10.30,y=10.30,z=10.30},glow=12,
   shaded=false,static_save=false,
   selectionbox={0,0,0,0,0,0},collisionbox={0,0,0,0,0,0},
  }
 })

 local function forget(name)
  local old=chosen[name]
  if old and old.fx and old.fx.get_pos and old.fx:get_pos() then old.fx:remove() end
  chosen[name]=nil
 end
 local function preview(s)
  if s.fx and s.fx.get_pos and s.fx:get_pos() then s.fx:remove() end
  s.fx=nil
  if not M.add_entity then return end
  local pos=s.pos
  if s.kind=='entity' then
   if not valid_entity(s.object) then return end
   pos=s.object:get_pos()
  end
  local obj=M.add_entity(pos,fx_name)
  if not obj then return end
  local scale=s.kind=='entity' and s.object:get_luaentity().scale or 1
  local yaw=s.kind=='entity' and s.object:get_luaentity().yaw
    or direction_yaw(s.node and s.node.param2 or 0)
  obj:set_properties({
   visual='mesh',mesh=s.entry.mesh,
   textures={'xz_fort_atlas.png^[colorize:#00B8FF:190'},
   visual_size={x=10.30*scale,y=10.30*scale,z=10.30*scale},
   pointable=false,physical=false,collide_with_objects=false,
   selectionbox={0,0,0,0,0,0},collisionbox={0,0,0,0,0,0},
   glow=12,shaded=false,static_save=false
  })
  if obj.set_yaw then obj:set_yaw(yaw) end
  s.fx=obj
 end
 local function scale_of(s)
  if s.kind=='entity' and valid_entity(s.object) then return s.object:get_luaentity().scale end
  return 1
 end
 local function form(p,s)
  local info=M.get_player_window_information and M.get_player_window_information(p:get_player_name())
  local max=info and info.max_formspec_size
  local maxw=tonumber(max and max.x) or 6.2
  local maxh=tonumber(max and max.y) or 5.3
  local w=math.max(3.40,math.min(5.20,maxw-.20))
  local h=math.max(3.10,math.min(4.50,maxh-.30))
  local label=M.formspec_escape((s.entry.label or 'FORT'):sub(1,38))
  local cw=w-.64
  local third=(cw-.14)/3
  local half=(cw-.10)/2
  local quarter=(cw-.18)/4
  local scale=scale_of(s)
  local out={
   'formspec_version[4]',
   ('size[%.2f,%.2f]'):format(w,h),
   'position[0.5,0.97]anchor[0.5,1]',
   'no_prepend[]bgcolor[#0B1421EE;false]',
   'style_type[button;bgcolor=#193A52;bgcolor_hovered=#256184;textcolor=#F1FAFF;border=false]',
   'style_type[button_exit;bgcolor=#263447;bgcolor_hovered=#38546B;textcolor=#F1FAFF;border=false]',
   ('box[0,0;%.2f,%.2f;#0A1523F5]'):format(w,h),
   ('box[0,0;%.2f,0.08;#20C9FF]'):format(w),
   ('box[0,0.08;%.2f,0.56;#16283D]'):format(w),
   'label[0.22,0.36;ZOMBIES  /  3D EDITOR]',
   ('scroll_container[0.12,0.69;%.2f,%.2f;fort_scroll;vertical;0.12;0.28]'):format(w-.47,h-1.40),
   ('label[0.15,0.28;%s]'):format(label),
   ('label[0.15,0.69;TAMANO ACTUAL   %.2fx]'):format(scale),
   ('button[0.15,0.91;%.2f,0.55;scale_minus;-0.25]'):format(third),
   ('button[%.2f,0.91;%.2f,0.55;scale_reset;1.00x]'):format(.22+third,third),
   ('button[%.2f,0.91;%.2f,0.55;scale_plus;+0.25]'):format(.29+third*2,third),
   ('button[0.15,1.55;%.2f,0.53;scale_big_minus;REDUCIR -1x]'):format(half),
   ('button[%.2f,1.55;%.2f,0.53;scale_big_plus;AGRANDAR +1x]'):format(.25+half,half),
   'label[0.15,2.37;ROTAR  /  GUARDAR AL INSTANTE]',
   ('button[0.15,2.58;%.2f,0.55;left;GIRAR -90]'):format(quarter),
   ('button[%.2f,2.58;%.2f,0.55;turn_minus; -15]'):format(.21+quarter,quarter),
   ('button[%.2f,2.58;%.2f,0.55;turn_plus; +15]'):format(.27+quarter*2,quarter),
   ('button[%.2f,2.58;%.2f,0.55;right;GIRAR +90]'):format(.33+quarter*3,quarter),
   'scroll_container_end[]',
   ('scrollbar[%.2f,0.69;0.22,%.2f;vertical;fort_scroll;0]'):format(w-.29,h-1.40),
   ('button_exit[0.23,%.2f;%.2f,0.53;close;LISTO]'):format(h-.64,w-.46)
  }
  return table.concat(out)
 end
 local function show(p)
  local s=chosen[p:get_player_name()]
  if s then M.show_formspec(p:get_player_name(),form_name,form(p,s)) end
 end

 local function try_select(p,pos,explicit_tool)
  if not can_edit(p,pos) or not held_allowed(p,explicit_tool) then return false end
  local entry,node=get_node_piece(pos)
  if not entry then return false end
  local name=p:get_player_name()
  forget(name)
  local copy={x=pos.x,y=pos.y,z=pos.z}
  local s={kind='node',pos=copy,node=node,entry=entry}
  chosen[name]=s
  preview(s)
  show(p)
  return true
 end
 local function try_select_object(p,obj,explicit_tool)
  local lua=valid_entity(obj)
  if not lua or not held_allowed(p,explicit_tool) or not can_edit(p,obj:get_pos()) then return false end
  local name=p:get_player_name()
  forget(name)
  local s={kind='entity',object=obj,entry=by_id[lua.fort_id],pos=obj:get_pos()}
  chosen[name]=s
  preview(s)
  show(p)
  return true
 end
 editor={try_select=try_select,try_select_object=try_select_object}

 local function convert(s)
  if s.kind=='entity' then return valid_entity(s.object) end
  local item,node=get_node_piece(s.pos)
  if not item or item.id~=s.entry.id or not M.serialize or not M.add_entity or not M.remove_node then
   return nil
  end
  local payload=M.serialize({id=item.id,scale=1,yaw=direction_yaw(node.param2),version=1})
  local obj=M.add_entity(s.pos,entity_name,payload)
  if not obj or not valid_entity(obj) then
   if obj and obj.get_pos and obj:get_pos() then obj:remove() end
   return nil
  end
  local success=M.remove_node(s.pos)
  if success==false then obj:remove();return nil end
  s.kind='entity'
  s.node=nil
  s.object=obj
  return obj:get_luaentity()
 end
 M.register_on_player_receive_fields(function(p,name,fields)
  if name~=form_name then return end
  if not p or not p.is_player or not p:is_player() then return true end
  local key=p:get_player_name()
  local s=chosen[key]
  if not s then return true end
  if fields.quit or fields.close then forget(key);return true end
  local scaling=(fields.scale_plus or fields.scale_minus or fields.scale_reset
    or fields.scale_big_plus or fields.scale_big_minus)
  local turning=(fields.left or fields.right or fields.turn_minus or fields.turn_plus)
  if not scaling and not turning then return true end
  local pos=s.kind=='entity' and s.object and s.object:get_pos() or s.pos
  if not can_edit(p,pos) then forget(key);return true end
  if s.kind=='entity' and not valid_entity(s.object) then forget(key);return true end
  if s.kind=='node' then
   local item,node=get_node_piece(s.pos)
   if not item or item.id~=s.entry.id then forget(key);return true end
   s.node=node
  end
  if scaling then
   local old=scale_of(s)
   local delta=fields.scale_big_plus and 1 or fields.scale_big_minus and -1
    or fields.scale_plus and .25 or fields.scale_minus and -.25 or 0
   local target=fields.scale_reset and 1 or clamp(math.floor((old+delta)*100+.5)/100,min_scale,max_scale)
   if s.kind=='node' and target~=1 then
    if not convert(s) then
     if M.chat_send_player then M.chat_send_player(key,'[3D Editor] No se pudo convertir la pieza. Se conserva el bloque original.') end
     return true
    end
   end
   if s.kind=='entity' then
    local lua=valid_entity(s.object)
    if lua then lua.scale=target;apply(lua) end
   end
  elseif turning then
   local delta=fields.left and -math.pi/2 or fields.right and math.pi/2
       or fields.turn_minus and -math.pi/12 or math.pi/12
   if s.kind=='node' and (fields.left or fields.right) then
    local node=s.node
    local param=((node.param2 or 0)%4+(fields.left and 3 or 1))%4
    if M.swap_node then M.swap_node(s.pos,{name=node.name,param1=node.param1 or 0,param2=param}) end
    s.node={name=node.name,param1=node.param1 or 0,param2=param}
   else
    if s.kind=='node' and not convert(s) then return true end
    local lua=valid_entity(s.object)
    if lua then lua.yaw=wrap_yaw(lua.yaw+delta);apply(lua) end
   end
  end
  preview(s)
  show(p)
  return true
 end)
 M.register_on_leaveplayer(function(p)
  if p and p.get_player_name then forget(p:get_player_name()) end
 end)
 return editor
end
