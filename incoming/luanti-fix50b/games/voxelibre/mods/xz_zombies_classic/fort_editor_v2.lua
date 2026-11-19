-- FIX61 FREEFORM MAP EDITOR. Compatible with persistent FIX60 architecture.
-- True glTF source dimensions, sub-node placement/movement, short touch pages,
-- repeatable ghost preview, per-instance transforms, and compound colliders.
return function(M, modpath, may_edit)
 local m=io.open(modpath..'/polyhaven_fort_manifest.lua','rb')
 if not m then return {try_select=function()return false end,try_select_object=function()return false end} end
 m:close()
 local entries=assert(loadfile(modpath..'/polyhaven_fort_manifest.lua'))()
 local collision=assert(loadfile(modpath..'/fort_collision.lua'))()(M,entries)
 local by_id,by_node={},{}
 for _,entry in ipairs(entries) do
  entry.kind='mesh'
  by_id[entry.id]=entry
  by_node['xz_zombies:'..entry.id]=entry
 end
 local object_name='xz_zombies_classic:fort_architecture'
 local ghost_name='xz_zombies_classic:fort_select_fx'
 local form='xz_zombies:fort_transform'
 local chosen,placing,enabled={}, {}, {}
 local editor -- Forward-declared for callbacks on registered entities.
 local low,high=.10,256
 local control_steps={.05,.25,1,5}
 local function finite(v) return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge end
 local function clamp(v,a,b)
  if not finite(v) then return a end
  return math.max(a,math.min(b,v))
 end
 local function copy(p) return {x=p.x,y=p.y,z=p.z} end
 local function vector_add(p,a) return {x=p.x+a.x,y=p.y+a.y,z=p.z+a.z} end
 local function turn(n) return (finite(n) and n or 0)%(2*math.pi) end
 local function is_builder(p,pos)
  if not p or not p.is_player or not p:is_player() then return false end
  if may_edit and not may_edit() then return false end
  if not (M.is_singleplayer and M.is_singleplayer())
    and not (M.check_player_privs and M.check_player_privs(p,{server=true})) then return false end
  if pos and M.is_protected and M.is_protected(pos,p:get_player_name()) then return false end
  return true
 end
 local function object_ok(obj)
  if not obj or not obj.get_pos or not obj:get_pos() or not obj.get_luaentity then return nil end
  local l=obj:get_luaentity()
  if l and l.name==object_name and l.arch_id then return l end
 end
 local function entry_for(id,kind)
  if kind=='mesh' then return by_id[id] end
  if kind=='node' and M.registered_nodes and M.registered_nodes[id] then
   local n=M.registered_nodes[id]
   return {id=id,kind='node',label=n.description or id,
    box={-.5,-.5,-.5,.5,.5,.5},natural_scale=1}
  end
 end
 local function get_node_piece(pos,permit_generic)
  local n=M.get_node_or_nil and M.get_node_or_nil(pos)
  if not n or n.name=='air' or n.name=='ignore' then return nil,nil end
  local entry=by_node[n.name]
  if entry then return entry,n end
  local def=M.registered_nodes and M.registered_nodes[n.name]
  -- Never convert doors, chests, wall buys, spawners, or scripted nodes.
  if permit_generic and def and not def.on_rightclick and not def.on_construct
    and not def.after_place_node and not def.on_timer
    and def.walkable~=false and not n.name:find('^xz_zombies:') then
   return entry_for(n.name,'node'),n
  end
  return nil,n
 end
 local function forward_yaw(param2)
  if M.facedir_to_dir and M.dir_to_yaw then return M.dir_to_yaw(M.facedir_to_dir(param2 or 0)) end
  return ((param2 or 0)%4)*math.pi/2
 end
 local function kind_and_entry(l)
  local kind=l.kind or 'mesh'
  return kind,entry_for(l.arch_id,kind)
 end
 local function foot_y(l,scale)
  local _,e=kind_and_entry(l)
  local b=e and e.box or {-.5,-.5,-.5,.5,.5,.5}
  return (l.object and l.object:get_pos() or {y=0}).y+b[2]*scale
 end
 local function choose_scale(e)
  return clamp(e.natural_scale or 1,low,high)
 end
 local function apply(l)
  local kind,e=kind_and_entry(l)
  if not e or not l.object or not l.object:get_pos() then return false end
  l.scale=clamp(l.scale or 1,low,high)
  l.rotation=l.rotation or {x=0,y=turn(l.yaw or 0),z=0}
  for _,axis in ipairs({'x','y','z'}) do l.rotation[axis]=turn(l.rotation[axis]) end
  local sz=kind=='mesh' and 10*l.scale or .667*l.scale
  local props={
   visual=kind=='mesh' and 'mesh' or 'wielditem',
   mesh=kind=='mesh' and e.mesh or '',
   textures=kind=='mesh' and {'xz_fort_atlas.png'} or {e.id},
   wield_item=kind=='node' and e.id or '',
   visual_size={x=sz,y=sz,z=sz},
   pointable=true,is_visible=true,static_save=true,
   shaded=true,glow=0,
  }
  l.object:set_properties(props)
  if l.object.set_rotation then l.object:set_rotation(copy(l.rotation))
  elseif l.object.set_yaw then l.object:set_yaw(l.rotation.y) end
  if l.object.set_armor_groups then l.object:set_armor_groups({immortal=1}) end
  collision.update(l,e,l.scale,l.rotation,l.collision_mode or 'auto')
  return true
 end
 M.register_entity(':'..object_name,{
  initial_properties={
   visual='mesh',mesh='xz_fort_01.obj',textures={'xz_fort_atlas.png'},
   physical=true,collide_with_objects=true,pointable=true,static_save=true,
   visual_size={x=10,y=10,z=10},
   selectionbox={-.5,-.5,-.5,.5,.5,.5},
   collisionbox={-.5,-.5,-.5,.5,.5,.5},
  },
  on_activate=function(self,staticdata)
   local ok,dat=pcall(function() return staticdata and staticdata~='' and M.deserialize and M.deserialize(staticdata) end)
   if not ok or type(dat)~='table' then
    if self.object then self.object:remove() end
    return
   end
   local kind=dat.kind or 'mesh'
   if not entry_for(dat.id,kind) then
    if self.object then self.object:remove() end
    return
   end
   self.arch_id=dat.id
   self.kind=kind
   self.scale=clamp(tonumber(dat.scale) or 1,low,high)
   self.rotation=type(dat.rotation)=='table' and dat.rotation
       or {x=0,y=dat.yaw or 0,z=0}
   self.collision_mode=dat.collision_mode or 'auto'
   apply(self)
  end,
  get_staticdata=function(self)
   if not self.arch_id or not M.serialize then return '' end
   return M.serialize({id=self.arch_id,kind=self.kind or 'mesh',
    scale=self.scale,rotation=self.rotation,collision_mode=self.collision_mode,
    version=2})
  end,
  on_punch=function() return true end,
  on_rightclick=function(self,p)
   if editor then editor.try_select_object(p,self.object,true) end
  end,
  on_deactivate=function(self)
   collision.clear(self)
  end,
 })
 M.register_entity(':'..ghost_name,{
  initial_properties={
   visual='mesh',mesh='xz_fort_01.obj',
   textures={'xz_fort_atlas.png^[colorize:#00C9FF:190'},
   visual_size={x=10.30,y=10.30,z=10.30},
   pointable=false,physical=false,collide_with_objects=false,
   selectionbox={0,0,0,0,0,0},collisionbox={0,0,0,0,0,0},
   static_save=false,glow=11,shaded=false,
  }
 })
 local function remove_ghost(a)
  if a and a.ghost and a.ghost.get_pos and a.ghost:get_pos() then a.ghost:remove() end
  if a then a.ghost=nil end
 end
 local function dismiss(name)
  remove_ghost(chosen[name])
  chosen[name]=nil
 end
 local function draw(s)
  remove_ghost(s)
  local pos=s.kind=='object' and s.object and s.object:get_pos() or s.pos
  if not pos or not M.add_entity then return end
  local obj=M.add_entity(pos,ghost_name)
  if not obj then return end
  s.ghost=obj
  local l=s.kind=='object' and object_ok(s.object)
  local scale=l and l.scale or 1
  local rotate=l and l.rotation or {x=0,y=forward_yaw(s.node and s.node.param2 or 0),z=0}
  local e=s.entry
  if e.kind=='mesh' then
   obj:set_properties({visual='mesh',mesh=e.mesh,
    textures={'xz_fort_atlas.png^[colorize:#00C9FF:195'},
    visual_size={x=10.22*scale,y=10.22*scale,z=10.22*scale},
    physical=false,collide_with_objects=false,pointable=false,
    static_save=false,glow=12,shaded=false})
  else
   obj:set_properties({visual='wielditem',wield_item=e.id,textures={e.id},
    visual_size={x=.690*scale,y=.690*scale,z=.690*scale},
    pointable=false,physical=false,collide_with_objects=false,
    static_save=false,glow=12})
  end
  if obj.set_rotation then obj:set_rotation(copy(rotate))
  elseif obj.set_yaw then obj:set_yaw(rotate.y) end
 end
 local function number(v) return ('%.2f'):format(v or 0) end
 local function panel(p,s)
  local info=M.get_player_window_information and M.get_player_window_information(p:get_player_name())
  local max=info and info.max_formspec_size or {}
  local w=math.max(3.8,math.min(5.4,(tonumber(max.x) or 6)-.18))
  local h=math.max(4.0,math.min(4.7,(tonumber(max.y) or 5)-.10))
  local l=s.kind=='object' and object_ok(s.object)
  local scale=l and l.scale or 1
  local rot=l and l.rotation or {x=0,y=forward_yaw(s.node and s.node.param2 or 0),z=0}
  local step=control_steps[s.precision or 2]
  local xoff=(w-.56)/2
  local cell=(w-.52)/4
  local fs={
   'formspec_version[4]',
   ('size[%.2f,%.2f]'):format(w,h),
   'position[0.985,0.97]anchor[1,1]',
   'no_prepend[]bgcolor[#06101CE8;false]',
   'style_type[button;bgcolor=#19334A;bgcolor_hovered=#266B91;textcolor=#F7FBFF;border=false]',
   'style_type[button_exit;bgcolor=#1B3D55;bgcolor_hovered=#286E91;textcolor=#FFFFFF;border=false]',
   ('box[0,0;%.2f,%.2f;#0B1726F6]'):format(w,h),
   ('box[0,0;%.2f,0.07;#00C9FF]'):format(w),
   ('box[0,0.07;%.2f,0.53;#142639]'):format(w),
   'label[0.18,0.34;ZOMBIES    3D BUILDER]',
   ('label[0.18,0.85;%s]'):format(M.formspec_escape((s.entry.label or 'OBJECT'):sub(1,35))),
   ('label[0.18,1.20;TAMANO  %sx    |    PASO  %s]'):format(number(scale),number(step)),
  }
  for i,tab in ipairs({'MOVER','ESCALA','ROTAR','FISICA'}) do
   fs[#fs+1]=('button[%.2f,1.42;%.2f,0.47;tab_%d;%s]'):format(.18+(i-1)*cell,cell-.025,i,tab)
  end
  local pnum=s.page or 1
  local function button(x,y,width,id,label)
   fs[#fs+1]=('button[%.2f,%.2f;%.2f,0.43;%s;%s]'):format(x,y,width,id,M.formspec_escape(label))
  end
  if pnum==1 then
   fs[#fs+1]='label[0.20,2.03;POSICION LIBRE  /  XYZ]'
   for i,axis in ipairs({'X','Y','Z'}) do
    local y=2.14+(i-1)*.47
    button(.18,y,xoff-.09,'move_'..axis..'_minus',axis..'  -')
    button(.26+xoff,y,xoff-.09,'move_'..axis..'_plus',axis..'  +')
   end
   button(.18,3.57,(w-.54)/3,'precision_1','FINO')
   button(.27+(w-.54)/3,3.57,(w-.54)/3,'precision_2','MEDIO')
   button(.36+2*(w-.54)/3,3.57,(w-.54)/3,'precision_3','1.0')
  elseif pnum==2 then
   fs[#fs+1]=('label[0.20,2.04;ESCALA ACTUAL  %sx]'):format(number(scale))
   button(.18,2.23,xoff-.09,'scale_minus','-0.25')
   button(.26+xoff,2.23,xoff-.09,'scale_plus','+0.25')
   button(.18,2.84,xoff-.09,'scale_big_minus','-1.00')
   button(.26+xoff,2.84,xoff-.09,'scale_big_plus','+1.00')
   button(.18,3.47,w-.36,'scale_reset','TAMANO ORIGINAL')
   fs[#fs+1]='label[0.20,4.02;PRECISION 0.10x - 256x]'
  elseif pnum==3 then
   fs[#fs+1]='label[0.20,2.03;ROTACION  /  GRADOS]'
   button(.18,2.16,xoff-.09,'turn_minus','Y -15')
   button(.26+xoff,2.16,xoff-.09,'turn_plus','Y +15')
   button(.18,2.62,xoff-.09,'left','Y -90')
   button(.26+xoff,2.62,xoff-.09,'right','Y +90')
   button(.18,3.10,xoff-.09,'axis_x_minus','X -15')
   button(.26+xoff,3.10,xoff-.09,'axis_x_plus','X +15')
   button(.18,3.58,w-.36,'rotation_advanced','PRECISION  XYZ')
  elseif pnum==5 then
   fs[#fs+1]='label[0.20,2.03;AJUSTE FINO   /   1 GRADO]'
   button(.18,2.16,xoff-.09,'fine_x_minus','X  -1')
   button(.26+xoff,2.16,xoff-.09,'fine_x_plus','X  +1')
   button(.18,2.62,xoff-.09,'fine_y_minus','Y  -1')
   button(.26+xoff,2.62,xoff-.09,'fine_y_plus','Y  +1')
   button(.18,3.10,xoff-.09,'fine_z_minus','Z  -1')
   button(.26+xoff,3.10,xoff-.09,'fine_z_plus','Z  +1')
   button(.18,3.58,w-.36,'rotation_back','VOLVER  /  ROTACION')
  else
   fs[#fs+1]='label[0.20,2.04;COLISION Y PASO LIBRE]'
   button(.18,2.25,xoff-.09,'mode_auto','AUTO')
   button(.26+xoff,2.25,xoff-.09,'mode_solid','SOLIDO')
   button(.18,2.83,xoff-.09,'mode_arch','ARCO LIBRE')
   button(.26+xoff,2.83,xoff-.09,'mode_stairs','ESCALERA')
   button(.18,3.40,xoff-.09,'mode_stairs_reverse','ESCALERA INV')
   button(.26+xoff,3.40,xoff-.09,'mode_none','SIN COLISION')
   fs[#fs+1]='label[0.20,3.96;COLISION A TU GUSTO]'
  end
  fs[#fs+1]=('button_exit[%.2f,%.2f;%.2f,0.48;close;LISTO]'):format(.18,h-.57,w-.36)
  return table.concat(fs)
 end
 local function show(p)
  local s=chosen[p:get_player_name()]
  if s and M.show_formspec then M.show_formspec(p:get_player_name(),form,panel(p,s)) end
 end
 local function select(p,pos,explicit)
  if not is_builder(p,pos) then return false end
  if not explicit then
   local stack=p.get_wielded_item and p:get_wielded_item()
   local held=stack and stack.get_name and stack:get_name() or ''
   if held~='' and held~='xz_zombies:editor_tool' then return false end
  end
  local entry,node=get_node_piece(pos,explicit)
  if not entry then return false end
  local name=p:get_player_name()
  dismiss(name)
  remove_ghost(placing[name])
  chosen[name]={kind='node',pos=copy(pos),node=node,entry=entry,page=1,precision=2}
  draw(chosen[name])
  show(p)
  return true
 end
 local function select_obj(p,obj,explicit)
  local l=object_ok(obj)
  if not l or not is_builder(p,obj:get_pos()) then return false end
  if not explicit then
   local stack=p.get_wielded_item and p:get_wielded_item()
   local held=stack and stack.get_name and stack:get_name() or ''
   if held~='' and held~='xz_zombies:editor_tool' then return false end
  end
  local entry=entry_for(l.arch_id,l.kind)
  if not entry then return false end
  local name=p:get_player_name()
  dismiss(name)
  remove_ghost(placing[name])
  chosen[name]={kind='object',object=obj,entry=entry,page=1,precision=2}
  draw(chosen[name])
  show(p)
  return true
 end
 local function create(pos,id,kind,scale,rotation,mode)
  if not M.add_entity or not M.serialize then return nil end
  local st=M.serialize({id=id,kind=kind,scale=scale,
   rotation=rotation or {x=0,y=0,z=0},collision_mode=mode or 'auto',version=2})
  local obj=M.add_entity(pos,object_name,st)
  if not object_ok(obj) then
   if obj and obj.get_pos and obj:get_pos() then obj:remove() end
   return nil
  end
  return obj
 end
 local function convert(s)
  if s.kind=='object' then return object_ok(s.object) end
  if not M.remove_node then return nil end
  local e,node=get_node_piece(s.pos,true)
  if not e or e.id~=s.entry.id then return nil end
  -- Preserve old visible position/size until the user performs an action.
  local rot={x=0,y=forward_yaw(node.param2),z=0}
  local new=create(s.pos,e.id,e.kind,1,rot)
  if not new then return nil end
  local result=M.remove_node(s.pos)
  if result==false then new:remove();return nil end
  s.kind='object'
  s.object=new
  s.node=nil
  return object_ok(new)
 end
 local function field_changed(p,form_name,fields)
  if form_name~=form then return end
  if not p or not p.is_player or not p:is_player() then return true end
  local name=p:get_player_name()
  local s=chosen[name]
  if not s then return true end
  if fields.quit or fields.close then dismiss(name);return true end
  for i=1,4 do
   if fields['tab_'..i] then s.page=i;show(p);return true end
  end
  if fields.rotation_advanced then s.page=5;show(p);return true end
  if fields.rotation_back then s.page=3;show(p);return true end
  if fields.precision_1 or fields.precision_2 or fields.precision_3 then
   s.precision=fields.precision_1 and 1 or fields.precision_2 and 2 or 3
   show(p)
   return true
  end
  local has_action=false
  for id in pairs(fields) do
   if id:find('^scale_') or id:find('^move_') or id:find('^axis_')
    or id:find('^mode_') or id:find('^fine_') or id=='left' or id=='right'
    or id:find('^turn_') then has_action=true end
  end
  if not has_action then return true end
  local pos=s.kind=='object' and s.object and s.object:get_pos() or s.pos
  if not pos or not is_builder(p,pos) then dismiss(name);return true end
  if s.kind=='node' then
   local e,node=get_node_piece(s.pos,true)
   if not e or e.id~=s.entry.id then dismiss(name);return true end
   s.node=node
  elseif not object_ok(s.object) then dismiss(name);return true end
  local l=convert(s)
  if not l then
   if M.chat_send_player then
    M.chat_send_player(name,'[3D Builder] No se pudo editar. El bloque original sigue intacto.')
   end
   return true
  end
  local before=copy(s.object:get_pos())
  local oldscale=l.scale
  local ybase=foot_y(l,oldscale)
  local next_scale=oldscale
  if fields.scale_minus then next_scale=oldscale-.25 end
  if fields.scale_plus then next_scale=oldscale+.25 end
  if fields.scale_big_minus then next_scale=oldscale-1 end
  if fields.scale_big_plus then next_scale=oldscale+1 end
  if fields.scale_reset then next_scale=choose_scale(s.entry) end
  next_scale=clamp(next_scale,low,high)
  if next_scale~=oldscale then
   l.scale=next_scale
   local b=s.entry.box or {-.5,-.5,-.5,.5,.5,.5}
   local newpos=copy(before)
   newpos.y=ybase-b[2]*next_scale
   if s.object.set_pos then s.object:set_pos(newpos) end
  end
  for _,axis in ipairs({'X','Y','Z'}) do
   if fields['move_'..axis..'_minus'] or fields['move_'..axis..'_plus'] then
    local direction=fields['move_'..axis..'_plus'] and 1 or -1
    local now=s.object:get_pos()
    local new=copy(now)
    local step=control_steps[s.precision or 2]
    local key=axis:lower()
    new[key]=now[key]+step*direction
    if s.object.set_pos then s.object:set_pos(new) end
   end
  end
  local rot=l.rotation or {x=0,y=0,z=0}
  local rad=math.pi/180
  if fields.left then rot.y=turn(rot.y-90*rad) end
  if fields.right then rot.y=turn(rot.y+90*rad) end
  if fields.turn_minus then rot.y=turn(rot.y-15*rad) end
  if fields.turn_plus then rot.y=turn(rot.y+15*rad) end
  for _,axis in ipairs({'x','z'}) do
   if fields['axis_'..axis..'_minus'] then rot[axis]=turn(rot[axis]-15*rad) end
   if fields['axis_'..axis..'_plus'] then rot[axis]=turn(rot[axis]+15*rad) end
  end
  for _,axis in ipairs({'x','y','z'}) do
   if fields['fine_'..axis..'_minus'] then rot[axis]=turn(rot[axis]-rad) end
   if fields['fine_'..axis..'_plus'] then rot[axis]=turn(rot[axis]+rad) end
  end
  l.rotation=rot
  for _,mode in ipairs({'auto','solid','arch','stairs','stairs_reverse','none'}) do
   if fields['mode_'..mode] then l.collision_mode=mode end
  end
  apply(l)
  draw(s)
  show(p)
  return true
 end
 M.register_on_player_receive_fields(field_changed)
 local function placement_position(p,pt,e,scale)
  local hit=pt and pt.intersection_point
  if not hit and M.raycast and p.get_pos and p.get_look_dir then
   local a=p:get_pos()
   local height=p.get_properties and (p:get_properties() or {}).eye_height or 1.47
   local origin={x=a.x,y=a.y+height,z=a.z}
   local d=p:get_look_dir()
   local finish={x=origin.x+d.x*5,y=origin.y+d.y*5,z=origin.z+d.z*5}
   for hitthing in M.raycast(origin,finish,false,false) do
    if hitthing.type=='node' and hitthing.intersection_point then
     hit=hitthing.intersection_point
    end
    break
   end
  end
  if not hit then
   if pt and pt.above then hit=pt.above
   elseif p.get_pos and p.get_look_dir then
    local v=p:get_pos()
    local d=p:get_look_dir()
    hit={x=v.x+d.x*2.8,y=v.y+d.y*2.8,z=v.z+d.z*2.8}
   else return nil end
  end
  local b=e.box or {-.5,-.5,-.5,.5,.5,.5}
  -- Place mesh FEET at the target surface. Never center 4m-high walls
  -- inside the floor or dig the map just to enlarge a staircase.
  local above=pt and pt.above
  local under=pt and pt.under
  local dy=above and under and above.y-under.y or 1
  local y=hit.y-b[2]*scale
  if dy<0 then y=hit.y-b[5]*scale end
  return {x=hit.x,y=y,z=hit.z}
 end
 local function place_new(stack,p,pt)
  if not p or not p.get_player_name or not is_builder(p) then return stack end
  local id=stack and stack.get_name and stack:get_name()
  local e=by_node[id or '']
  if not e or not pt or pt.type~='node' then return stack end
  local scale=choose_scale(e)
  local pos=placement_position(p,pt,e,scale)
  if not pos or (M.is_protected and M.is_protected(pos,p:get_player_name())) then return stack end
  local obj=create(pos,e.id,'mesh',scale,{x=0,y=0,z=0})
  if not obj then return stack end
  local n=p:get_player_name()
  remove_ghost(placing[n])
  if not (M.is_creative_enabled and M.is_creative_enabled(n)) and stack.take_item then
   stack:take_item(1)
  end
  -- Immediately opens the proper 3D panel, no inventory slot has to be empty.
  select_obj(p,obj,true)
  return stack
 end
 local function place_generic(stack,p,pt)
  if not p or not enabled[p:get_player_name()] or not is_builder(p) then return nil end
  local id=stack and stack.get_name and stack:get_name()
  local e=entry_for(id,'node')
  local d=M.registered_nodes and M.registered_nodes[id or '']
  if not e or not d or d.on_rightclick or d.on_construct or d.on_timer
    or d.after_place_node or not pt or pt.type~='node' then return nil end
  local pos=placement_position(p,pt,e,1)
  if not pos or (M.is_protected and M.is_protected(pos,p:get_player_name())) then return stack end
  local obj=create(pos,id,'node',1,{x=0,y=0,z=0})
  if not obj then return stack end
  if not (M.is_creative_enabled and M.is_creative_enabled(p:get_player_name()))
   and stack.take_item then stack:take_item(1) end
  select_obj(p,obj,true)
  return stack
 end
 local function see_mode(p)
  if p and p.get_player_name then return enabled[p:get_player_name()] end
 end
 local function set_mode(p,v)
  if not is_builder(p) then return false end
  enabled[p:get_player_name()]=v==nil and not enabled[p:get_player_name()] or not not v
  if not enabled[p:get_player_name()] then
   dismiss(p:get_player_name())
   remove_ghost(placing[p:get_player_name()])
  end
  if M.chat_send_player then
   M.chat_send_player(p:get_player_name(),enabled[p:get_player_name()]
    and '[3D Builder] ACTIVO: apunta y pulsa USE con cualquier bloque en la mano.'
    or '[3D Builder] DESACTIVADO.')
  end
  return enabled[p:get_player_name()]
 end
 local function use_target(p)
  if not p or not p.get_pos or not p.get_look_dir or not M.raycast or not is_builder(p) then return false end
  local loc=p:get_pos()
  local properties=p.get_properties and p:get_properties() or {}
  local eye={x=loc.x,y=loc.y+(properties.eye_height or 1.47),z=loc.z}
  local dir=p:get_look_dir()
  local dest={x=eye.x+dir.x*5,y=eye.y+dir.y*5,z=eye.z+dir.z*5}
  for pt in M.raycast(eye,dest,true,false) do
   if pt.type=='object' then
    if select_obj(p,pt.ref,true) then return true end
    -- Skip ordinary mobs, weapons and players, but don't start editing
    -- something behind an unrelated interactive object.
   elseif pt.type=='node' then
    local e,n=get_node_piece(pt.under,see_mode(p))
    if e then return select(p,pt.under,true) end
    return false
   end
  end
  -- Large Poly Haven modules can be >15m long. Native Luanti point/raycast
  -- doesn't reliably hit an entity whose selectionbox extends >5m.
  -- On deliberate USE ONLY, intersect the look ray with nearby
  -- architecture bounds without scanning every frame.
  if M.get_objects_inside_radius then
   local closest,closest_t
   for _,candidate in ipairs(M.get_objects_inside_radius(eye,40)) do
    local l=object_ok(candidate)
    if l then
     local e=entry_for(l.arch_id,l.kind)
     local center=candidate:get_pos()
     local yaw=l.rotation and l.rotation.y or 0
     local c,s=math.cos(yaw),math.sin(yaw)
     local x=eye.x-center.x
     local z=eye.z-center.z
     local origin={c*x-s*z,eye.y-center.y,s*x+c*z}
     local velocity={c*dir.x-s*dir.z,dir.y,s*dir.x+c*dir.z}
     local b=e and e.box or {-.5,-.5,-.5,.5,.5,.5}
     local hx=math.max(math.abs(b[1]),math.abs(b[4]))*l.scale
     local hy=math.max(math.abs(b[2]),math.abs(b[5]))*l.scale
     local hz=math.max(math.abs(b[3]),math.abs(b[6]))*l.scale
     local ext={hx,hy,hz}
     local t0,t1=0,5
     for axis=1,3 do
      local o,d,h=origin[axis],velocity[axis],ext[axis]
      if math.abs(d)<.00001 then
       if o < -h or o>h then t0=100 end
      else
       local a=(-h-o)/d
       local b1=(h-o)/d
       if a>b1 then a,b1=b1,a end
       t0=math.max(t0,a)
       t1=math.min(t1,b1)
      end
     end
     if t0<=t1 and t0<=5 and (not closest_t or t0<closest_t) then
      closest,closest_t=candidate,t0
     end
    end
   end
   if closest then return select_obj(p,closest,true) end
  end
  return false
 end
 -- Same ghost appears before placement; it follows the aiming ray.
 local elapsed=0
 M.register_globalstep(function(dt)
  elapsed=elapsed+dt
  if elapsed<.22 then return end
  elapsed=0
  if not M.get_connected_players then return end
  for _,p in ipairs(M.get_connected_players()) do
   if p and p.get_player_name then
    local name=p:get_player_name()
    local stack=p.get_wielded_item and p:get_wielded_item()
    local held=stack and stack.get_name and stack:get_name() or ''
    local e=by_node[held]
    if not e or not is_builder(p) or chosen[name] then
     remove_ghost(placing[name]);placing[name]=nil
    elseif p.get_pos and p.get_look_dir then
     local record=placing[name]
     local scale=choose_scale(e)
     local pos=placement_position(p,nil,e,scale)
     if pos then
      if not record then record={entry=e};placing[name]=record end
      if not record.ghost or not record.ghost.get_pos or not record.ghost:get_pos() then
       record.ghost=M.add_entity(pos,ghost_name)
      elseif record.ghost.set_pos then record.ghost:set_pos(pos) end
      if record.ghost then
       record.ghost:set_properties({
        visual='mesh',mesh=e.mesh,
        textures={'xz_fort_atlas.png^[colorize:#00C9FF:180'},
        visual_size={x=10.2*scale,y=10.2*scale,z=10.2*scale},
        physical=false,pointable=false,collide_with_objects=false,
        static_save=false,glow=12,
       })
      end
     end
    end
   end
  end
 end)
 M.register_on_leaveplayer(function(p)
  if not p or not p.get_player_name then return end
  local name=p:get_player_name()
  dismiss(name)
  remove_ghost(placing[name]);placing[name]=nil
  enabled[name]=nil
 end)
 editor={
  try_select=select,try_select_object=select_obj,place_new=place_new,
  use_target=use_target,set_mode=set_mode,is_enabled=see_mode,place_generic=place_generic,
 }
 return editor
end
