-- FIX59 Phase 1: tactile premium selection for existing FIX58 Fort mesh nodes.
-- No mesh duplication, combat changes, engine changes or world conversion.
return function(M, modpath, may_edit)
 local file=io.open(modpath..'/polyhaven_fort_manifest.lua','rb')
 if not file then
  return {try_select=function() return false end}
 end
 file:close()
 local manifest=assert(loadfile(modpath..'/polyhaven_fort_manifest.lua'))()
 local pieces={}
 for _,entry in ipairs(manifest) do
  pieces['xz_zombies:'..entry.id]=entry
 end
 local chosen={}
 local fx_name='xz_zombies_classic:fort_select_fx'
 local form_name='xz_zombies:fort_transform'
 local function allowed(p,pos)
  if not p or not p.is_player or not p:is_player() then return false end
  if may_edit and not may_edit() then return false end
  local name=p:get_player_name()
  if not (M.is_singleplayer() or (M.check_player_privs and M.check_player_privs(p,{server=true}))) then return false end
  if pos and M.is_protected and M.is_protected(pos,name) then return false end
  return true
 end
 local function get_piece(pos)
  if not pos or not M.get_node_or_nil then return nil,nil end
  local node=M.get_node_or_nil(pos)
  return node and pieces[node.name],node
 end
 local function release(name)
  local old=chosen[name]
  if old and old.fx and old.fx:get_pos() then old.fx:remove() end
  chosen[name]=nil
 end
 local function direction_yaw(param2)
  if M.facedir_to_dir and M.dir_to_yaw then
   return M.dir_to_yaw(M.facedir_to_dir(param2 or 0))
  end
  return (param2 or 0)%4 * math.pi/2
 end
 M.register_entity(':'..fx_name,{
  initial_properties={
   physical=false,collide_with_objects=false,pointable=false,
   visual='mesh',mesh='xz_fort_01.obj',
   textures={'xz_fort_atlas.png^[colorize:#00B8FF:200'},
   visual_size={x=1.035,y=1.035,z=1.035},
   glow=12,shaded=false,static_save=false,
   selectionbox={0,0,0,0,0,0},
   collisionbox={0,0,0,0,0,0},
  },
 })
 local function draw_fx(pos,entry,node)
  if not M.add_entity then return nil end
  local obj=M.add_entity(pos,fx_name)
  if not obj then return nil end
  obj:set_properties({
   mesh=entry.mesh,
   textures={'xz_fort_atlas.png^[colorize:#00B8FF:205'},
   visual_size={x=1.035,y=1.035,z=1.035},
   glow=12,pointable=false,physical=false,collide_with_objects=false,
   selectionbox={0,0,0,0,0,0},
   collisionbox={0,0,0,0,0,0},
   static_save=false,
  })
  if obj.set_yaw then obj:set_yaw(direction_yaw(node.param2)) end
  return obj
 end
 local function layout(p,entry)
  local info=M.get_player_window_information and M.get_player_window_information(p:get_player_name())
  local max=info and info.max_formspec_size
  local maxw=tonumber(max and max.x) or 6.2
  local maxh=tonumber(max and max.y) or 5
  local w=math.max(3.4,math.min(5.2,maxw-0.20))
  local h=math.max(2.95,math.min(3.45,maxh-0.20))
  local name=M.formspec_escape((entry.label or 'Fort') :sub(1,35))
  local left_w=(w-0.72)/2
  local out={
   'formspec_version[4]',
   ('size[%.2f,%.2f]'):format(w,h),
   'position[0.5,0.97]anchor[0.5,1]',
   'no_prepend[]bgcolor[#0B1220EE;false]',
   'style_type[button;bgcolor=#18364C;bgcolor_hovered=#245A7A;textcolor=#F4FBFF;border=false]',
   'style_type[button_exit;bgcolor=#202F42;bgcolor_hovered=#344B61;textcolor=#DAE8F2;border=false]',
   ('box[0,0;%.2f,%.2f;#0B1625F5]'):format(w,h),
   ('box[0,0;%.2f,0.10;#20C9FF]'):format(w),
   ('box[0,0.10;%.2f,0.59;#15263B]'):format(w),
   'label[0.23,0.40;ZOMBIES  /  3D EDITOR]',
   'label[0.23,1.04;MODULAR FORT 01]',
   ('label[0.23,1.42;%s]'):format(name),
   'label[0.23,1.81;ROTACION DE LA PIEZA]',
   ('button[0.23,2.00;%.2f,0.62;left;GIRAR -90]'):format(left_w),
   ('button[%.2f,2.00;%.2f,0.62;right;GIRAR +90]'):format(0.49+left_w,left_w),
   ('button_exit[0.23,%.2f;%.2f,0.57;close;LISTO]'):format(h-0.68,w-0.46)
  }
  return table.concat(out)
 end
 local function show(p)
  local s=chosen[p:get_player_name()]
  if not s then return end
  M.show_formspec(p:get_player_name(),form_name,layout(p,s.entry))
 end
 local function try_select(p,pos,from_tool)
  if not allowed(p,pos) then return false end
  if not from_tool then
   local wield=p.get_wielded_item and p:get_wielded_item()
   local held=wield and wield.get_name and wield:get_name() or ''
   -- Never steal ordinary construction taps from blocks held in the hand.
   if held~='' and held~='xz_zombies:editor_tool' then return false end
  end
  local entry,node=get_piece(pos)
  if not entry then return false end
  local name=p:get_player_name()
  release(name)
  local copy={x=pos.x,y=pos.y,z=pos.z}
  chosen[name]={pos=copy,entry=entry,fx=draw_fx(copy,entry,node)}
  show(p)
  return true
 end
 M.register_on_player_receive_fields(function(p,form,fields)
  if form~=form_name then return end
  if not p or not p.is_player or not p:is_player() then return true end
  local name=p:get_player_name()
  local s=chosen[name]
  if not s then return true end
  if fields.quit or fields.close then release(name);return true end
  if not (fields.left or fields.right) then return true end
  if not allowed(p,s.pos) then release(name);return true end
  local entry,node=get_piece(s.pos)
  if not entry or entry.id~=s.entry.id then release(name);return true end
  -- Node rotation is persistent in the map; no geometry or collision rewrite.
  local next_param=(node.param2 or 0)%4
  next_param=(next_param+(fields.left and 3 or 1))%4
  if M.swap_node then
   M.swap_node(s.pos,{name=node.name,param1=node.param1 or 0,param2=next_param})
   if s.fx and s.fx:get_pos() and s.fx.set_yaw then s.fx:set_yaw(direction_yaw(next_param)) end
  end
  show(p)
  return true
 end)
 M.register_on_leaveplayer(function(p)
  if p and p.get_player_name then release(p:get_player_name()) end
 end)
 return {try_select=try_select}
end
