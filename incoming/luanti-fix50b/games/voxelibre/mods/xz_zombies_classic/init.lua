-- FIX44 COD4 Zombies Classic. Adds features without removing any FIX43 assets.
local M = minetest
local MOD = M.get_current_modname()
local storage = M.get_mod_storage()
local modpath = M.get_modpath(MOD)
local root = M.get_modpath('ak47dev')
local source = assert(loadfile(root .. '/arsenal_catalog.lua'))()
local director = assert(loadfile(modpath .. '/round_director.lua'))()
local v26_rules = assert(loadfile(modpath .. '/v26_rules.lua'))()
local v26_modes = assert(loadfile(modpath .. '/v26_modes.lua'))()(M)
local v26_hud = assert(loadfile(modpath .. '/v26_hud.lua'))()(M)
local v26_combatfx = assert(loadfile(modpath .. '/v26_viril_combatfx.lua'))()(M)
local rotu_ai = assert(loadfile(modpath .. '/rotu_ai.lua'))()(M)
local dremorn_visual = assert(loadfile(modpath .. '/dremorn_visual.lua'))()(M,modpath)
local WEAPONS = {
  {id='ak47', item='ak47dev:ak47',label='AK-47',icon='ak47dev_icon.png', price=1200},
  {id='m9',item='ak47dev:m9',label='M9',icon='m9_icon.png',price=500},
}
local ids = {}
for item, d in pairs(source) do
  ids[#ids+1] = {id=d.id,item=item,label=d.label,icon=d.icon,price=1200}
end
table.sort(ids,function(a,b) return a.id<b.id end)
for _,w in ipairs(ids) do WEAPONS[#WEAPONS+1]=w end
assert(#WEAPONS==28,'FIX44 requires exactly 28 existing weapons; found '..#WEAPONS)
local choices, weapon_by_id, item_set = {}, {}, {}
for i,w in ipairs(WEAPONS) do
  choices[i]=M.formspec_escape(w.label)
  weapon_by_id[w.id]=w
  item_set[w.item]=true
end
local form_editor = 'xz_zombies:editor'
local form_buy = 'xz_zombies:configure'
local form_dev = 'xz_zombies:developer'
local state = {active=false,round=0,round_quota=0,spawned=0,kills=0,next_spawn=0,round_delay=0,zombies={},next_round=0}
local v26 -- initialized after node registration
local viewers, developer, huds, prev_physics, prev_armor = {}, {}, {}, {}, {}
-- COD HUD is managed by v26_hud.lua, not floating text above the pause button.
local editor_pages, developer_pages, editor_weapon_index = {}, {}, {}
local ACTIVE_STORAGE='active'
local saved_spawners = M.deserialize(storage:get_string('spawner_positions')) or {}
local function persist_spawners() storage:set_string('spawner_positions', M.serialize(saved_spawners)) end
local original_time_speed = M.settings and M.settings:get('time_speed') or '72'
local function set_world_time_mode(mode)
 if mode ~= 'day' and mode ~= 'night' then mode='normal' end
 storage:set_string('world_time_mode',mode)
 if M.settings and M.settings.set then
  M.settings:set('time_speed',mode=='normal' and original_time_speed or '0')
 end
 if mode=='day' then M.set_timeofday(0.5)
 elseif mode=='night' then M.set_timeofday(0) end
end
-- Keep mode across world reloads; previous nonzero time speed is restored by Normal.
local persisted_time=storage:get_string('world_time_mode')
if persisted_time=='day' or persisted_time=='night' then set_world_time_mode(persisted_time) end

-- FIX45 test: use native VoxeLibre entities and their existing mesh, texture and AI.
local ZOMBIE_MODELS = {
 'mobs_mc:zombie', 'mobs_mc:zombie', 'mobs_mc:zombie',
 'mobs_mc:husk', 'mobs_mc:villager_zombie', -- NO baby zombies.
}
local function native_zombie()
 local pool={}
 for _,name in ipairs(ZOMBIE_MODELS) do
  if M.registered_entities[name] then pool[#pool+1]=name end
 end
 if #pool==0 then return nil end
 return pool[math.random(#pool)]
end
local function zombie_spawn_pos(at)
 -- A spawner can be put on the floor or embedded in a wall. Find space for
 -- both feet and head, on solid ground, before trying to create the mob.
 local offsets={{0,1,0},{1,0,0},{-1,0,0},{0,0,1},{0,0,-1},
                {1,1,0},{-1,1,0},{0,1,1},{0,1,-1},
                {2,0,0},{-2,0,0},{0,0,2},{0,0,-2}}
 local function node(p) return M.get_node_or_nil(p) end
 for _,o in ipairs(offsets) do
  local p={x=at.x+o[1],y=at.y+o[2],z=at.z+o[3]}
  local feet=node(p)
  local head=node({x=p.x,y=p.y+1,z=p.z})
  local ground=node({x=p.x,y=p.y-1,z=p.z})
  local floor=ground and M.registered_nodes[ground.name]
  if feet and head and feet.name=='air' and head.name=='air'
      and floor and floor.walkable then
   return {x=p.x,y=p.y+0.05,z=p.z}
  end
 end
 return nil
end
local function spawn_native_zombie(at)
 local name=native_zombie()
 if not name then return false,'No hay zombis nativos cargados (mobs_mc).' end
 local p=zombie_spawn_pos(at)
 if not p then return false,'No hay espacio libre de dos bloques junto al spawner.' end
 local obj=M.add_entity(p,name)
 if not obj then return false,'Luanti no pudo crear '..name end
 -- This is a round-controlled mob: do not despawn or burn before the test.
 local entity=obj:get_luaentity()
 if entity then
  entity.can_despawn=false
  entity.ignited_by_sunlight=false
  entity.sunlight_damage=0
 end
 obj:set_hp(math.floor(v26_rules.zombie_hp(state.round)))
 local record={obj=obj}
 state.zombies[#state.zombies+1]=record
 if v26 and v26.install_native_ai then v26.install_native_ai(record) end
 if entity then dremorn_visual.apply(entity,obj) end
 state.spawned=state.spawned+1
 return true,name
end

local function allowed(p) return p and p:is_player() and (M.is_singleplayer() or M.check_player_privs(p,{server=true})) end
local function player_points(p) return p:get_meta():get_int('xz_z_points') end
local function set_points(p,n)
 local previous=player_points(p)
 local actual=math.max(0,math.floor(n))
 p:get_meta():set_int('xz_z_points',actual)
 v26_hud.points(p,actual)
 if state.active and actual>previous and actual-previous<=200 then
  v26_hud.award(p,actual-previous)
 end
end
local function tell(p,s) M.chat_send_player(p:get_player_name(), '[Zombies] '..s) end
local function point_charge(p,amount)
  if not state.active then return false end
  if developer[p:get_player_name()] and developer[p:get_player_name()].free then return true end
  if player_points(p)<amount then tell(p,'Necesitas '..amount..' puntos.') return false end
  set_points(p,player_points(p)-amount)
  return true
end
local function give_weapon(p,item)
  local inv=p:get_inventory()
  if not inv or not M.registered_items[item] then return false end
  if inv:contains_item('main',item) then return true end
  if inv:room_for_item('main',ItemStack(item)) then
    local leftover=inv:add_item('main',ItemStack(item))
    return leftover:is_empty()
  end
  return false
end
local function pos_key(pos) return ('%d,%d,%d'):format(pos.x,pos.y,pos.z) end
local function fmt_price(pos,default)
  local meta=M.get_meta(pos)
  local price=meta:get_int('price')
  if price<=0 then price=default;meta:set_int('price',price) end
  return price
end
-- FIX49: Use Luanti's client-reported maximum GUI size, not any specific phone DPI.
-- The reported size can change on device rotation, split-screen and folding.
local function responsive_size(p, want_w, want_h)
 local info = M.get_player_window_information and M.get_player_window_information(p:get_player_name())
 local max = info and info.max_formspec_size
 local maxw = max and tonumber(max.x)
 local maxh = max and tonumber(max.y)
 -- Conservative fallback for older clients that do not report window dimensions.
 if not maxw or maxw < 2 then maxw = 8.4 end
 if not maxh or maxh < 2 then maxh = 6.2 end
 local width = math.max(3.1, math.min(want_w, maxw - 0.25))
 local height = math.max(3.4, math.min(want_h, maxh - 0.25))
 return width, height
end
local function fs_button(t, x, y, w, h, id, caption)
 t[#t+1] = ('button[%.2f,%.2f;%.2f,%.2f;%s;%s]'):format(
    x,y,w,h,id,M.formspec_escape(caption))
end
local function fs_label(t,x,y,caption)
 t[#t+1] = ('label[%.2f,%.2f;%s]'):format(x,y,M.formspec_escape(caption))
end
local function gui_header(w,h,title)
 return {'formspec_version[4]',('size[%.2f,%.2f]'):format(w,h),
  'padding[0.02,0.02]bgcolor[#111925;true]',
  'style_type[button;bgcolor=#29394C;bgcolor_hovered=#395671;border=false]',
  'style_type[button_exit;bgcolor=#354457;bgcolor_hovered=#476079;border=false]',
  ('box[0,0;%.2f,0.70;#1C2B40]'):format(w),
  ('label[0.24,0.36;%s]'):format(M.formspec_escape(title))}
end
local function gui_price(p,pos,kind,desc)
 viewers[p:get_player_name()]={pos=vector.new(pos),kind=kind}
 local price=fmt_price(pos,kind=='wall' and 1200 or kind=='door' and 1000 or kind=='mystery' and 950 or 2500)
 local w,h=responsive_size(p,7.2,3.75)
 local f=gui_header(w,h,'CONFIGURAR PRECIO')
 fs_label(f,0.3,1.0,desc)
 f[#f+1]=('field[0.3,1.35;%.2f,0.75;price;Precio en puntos;%d]'):format(w-0.6,price)
 fs_button(f,0.3,h-1.02,(w-0.9)/2,0.72,'save','GUARDAR')
 f[#f+1]=('button_exit[%.2f,%.2f;%.2f,0.72;cancel;CERRAR]'):format(0.6+(w-0.9)/2,h-1.02,(w-0.9)/2)
 M.show_formspec(p:get_player_name(),form_buy,table.concat(f))
end
local function money_node(pos,label,price)
 local meta=M.get_meta(pos); meta:set_int('price',price);meta:set_string('infotext',label..' - '..price..' pts')
end
local function wall_action(pos,p,w)
  if not state.active then return gui_price(p,pos,'wall','Wall Buy: '..w.label) end
  local price=fmt_price(pos,w.price)
  if p:get_inventory():contains_item('main',w.item) then tell(p,'Ya tienes '..w.label..'.') return end
  if not p:get_inventory():room_for_item('main',ItemStack(w.item)) then tell(p,'Inventario lleno.') return end
  if not point_charge(p,price) then return end
  if give_weapon(p,w.item) then tell(p,'Compraste '..w.label..'.') end
end
for _,w in ipairs(WEAPONS) do
 local weapon = w
 M.register_node(':xz_zombies:wall_'..weapon.id,{
  description='Wall Buy | '..weapon.label,
  drawtype='mesh',mesh='xz_wall_'..weapon.id..'.obj',tiles={'xz_wall_'..weapon.id..'.png'},
  paramtype='light',paramtype2='facedir',sunlight_propagates=true,
  walkable=false,pointable=true,buildable_to=false,
  -- FIX49B: visual model is flush with the backing wall (local -Z).
  -- The touch target is deliberately wider than a small pistol mesh.
  -- A shallow, frame-like hitbox along the surface rather than a cube.
  selection_box={type='fixed',fixed={-.40,-.21,-.499,.40,.21,-.405}},
  groups={cracky=3,oddly_breakable_by_hand=1},inventory_image=weapon.icon,
  -- Always face outward from the surface that received the miniature prop.
  -- This fixes props placed sideways when player yaw differs from wall normal.
  -- FIX50A: an item can only be placed on a real vertical solid wall face.
  -- Invalid taps do not consume the item and cannot create floating wall buys.
  on_place=function(stack,placer,pt)
   if not placer or not placer:is_player() or not pt or pt.type~='node'
       or not pt.under or not pt.above then return stack end
   local dx=pt.above.x-pt.under.x
   local dy=pt.above.y-pt.under.y
   local dz=pt.above.z-pt.under.z
   if dy~=0 or (math.abs(dx)+math.abs(dz))~=1 then
    tell(placer,'Wall Buy: toca una cara VERTICAL de una pared.')
    return stack
   end
   local backing=M.get_node_or_nil(pt.under)
   local def=backing and M.registered_nodes[backing.name]
   if not def or not def.walkable or def.buildable_to then
    tell(placer,'Wall Buy: primero necesitas una pared solida.')
    return stack
   end
   if not M.item_place_node or not M.dir_to_facedir then return stack end
   local facing=M.dir_to_facedir({x=dx,y=0,z=dz})
   return M.item_place_node(stack,placer,pt,facing)
  end,
  -- Keep orientation even when clients use alternate node placement modes.
  after_place_node=function(pos,placer,stack,pt)
   if not pt or not pt.under or not pt.above then return end
   local dx,dz=pt.above.x-pt.under.x,pt.above.z-pt.under.z
   if math.abs(dx)+math.abs(dz)~=1 or pt.above.y~=pt.under.y then return end
   if not M.dir_to_facedir or not M.swap_node then return end
   local node=M.get_node(pos)
   node.param2=M.dir_to_facedir({x=dx,y=0,z=dz})
   M.swap_node(pos,node)
  end,
  on_construct=function(pos) money_node(pos,weapon.label,weapon.price) end,
  on_rightclick=function(pos,node,p) if p and p:is_player() then wall_action(pos,p,weapon) end end,
  on_destruct=function(pos) end,
 })
end
-- FIX50B: reanchor eligible old floating Wall Buys without destroying blocks.
-- Only repair a legacy prop if exactly one nearest unobstructed solid vertical
-- wall is found within three nodes. Other structures are never overwritten.
local wall_buy_nodes = {}
for _,weapon in ipairs(WEAPONS) do
 wall_buy_nodes[#wall_buy_nodes+1] = 'xz_zombies:wall_'..weapon.id
end
local wall_directions = {
 {x=0,y=0,z=1},{x=1,y=0,z=0},
 {x=0,y=0,z=-1},{x=-1,y=0,z=0},
}
local function offset3(p,dir,n)
 return {x=p.x+dir.x*n,y=p.y,z=p.z+dir.z*n}
end
local function same_pos(a,b)
 return a.x==b.x and a.y==b.y and a.z==b.z
end
local function solid_backing(p)
 local node=M.get_node_or_nil(p)
 if not node or node.name=='ignore' or node.name:find('^xz_zombies:') then return false end
 local def=M.registered_nodes[node.name]
 return def and def.walkable and not def.buildable_to
end
local function open_mount_space(p)
 local node=M.get_node_or_nil(p)
 if not node or node.name=='ignore' then return false end
 local def=M.registered_nodes[node.name]
 return def and def.buildable_to
end
local function fix_existing_wall_mount(pos,node)
 if not M.dir_to_facedir or not M.swap_node then return end
 local choices,closest={},nil
 for _,dir in ipairs(wall_directions) do
  for distance=1,3 do
   local back=offset3(pos,dir,-distance)
   if solid_backing(back) then
    local dest=offset3(pos,dir,1-distance)
    local clear=true
    for step=1,distance-1 do
     if not open_mount_space(offset3(pos,dir,-step)) then clear=false;break end
    end
    if clear and (same_pos(dest,pos) or open_mount_space(dest)) then
     if not closest or distance<closest then choices={};closest=distance end
     if distance==closest then choices[#choices+1]={destination=dest,dir=dir} end
    end
    break
   end
   if not open_mount_space(back) then break end
  end
 end
 if #choices==0 then return end
 local selected
 if #choices==1 then selected=choices[1] else
  for _,candidate in ipairs(choices) do
   if M.dir_to_facedir(candidate.dir)==node.param2 then
    selected=candidate;break
   end
  end
 end
 if not selected then return end
 local dest=selected.destination
 local facing=M.dir_to_facedir(selected.dir)
 if same_pos(dest,pos) then
  if node.param2~=facing then
   M.swap_node(pos,{name=node.name,param1=node.param1 or 0,param2=facing})
  end
  return
 end
 if not M.get_meta then return end
 if M.is_protected and (M.is_protected(dest,'') or M.is_protected(pos,'')) then return end
 local meta=M.get_meta(pos)
 if not meta or not meta.to_table then return end
 local old_data=meta:to_table()
 if not old_data then return end
 M.swap_node(dest,{name=node.name,param1=node.param1 or 0,param2=facing})
 local target_meta=M.get_meta(dest)
 if target_meta and target_meta.from_table then target_meta:from_table(old_data) end
 M.swap_node(pos,{name='air'})
end
if M.register_lbm then
 M.register_lbm({
  name='xz_zombies_classic:fix50b_reanchor_existing_wall_buys',
  nodenames=wall_buy_nodes,run_at_every_load=false,
  action=fix_existing_wall_mount,
 })
end

local function mystery_action(pos,p)
 if not state.active then return gui_price(p,pos,'mystery','Mystery Box') end
 local price=fmt_price(pos,950)
 if not point_charge(p,price) then return end
 local available={}
 for _,candidate in ipairs(WEAPONS) do
  if not p:get_inventory():contains_item('main',candidate.item) then available[#available+1]=candidate end
 end
 local w=available[math.random(#available>0 and #available or #WEAPONS)]
 if #available==0 then w=WEAPONS[math.random(#WEAPONS)] end
 if not give_weapon(p,w.item) then set_points(p,player_points(p)+price);tell(p,'Inventario lleno; puntos devueltos.') return end
 tell(p,'MYSTERY BOX: '..w.label)
end
for _,letter in ipairs({'a','b'}) do
 M.register_node(':xz_zombies:mystery_box_'..letter,{
  description='Mystery Box '..string.upper(letter),tiles={'mcl_chests_normal.png'},
  groups={choppy=2,oddly_breakable_by_hand=2},
  on_construct=function(pos) money_node(pos,'Mystery Box '..letter,950) end,
  on_rightclick=function(pos,node,p) if p and p:is_player() then mystery_action(pos,p) end end,
 })
end
M.register_node(':xz_zombies:door',{
 description='Zombies Locked Door',drawtype='nodebox',paramtype='light',paramtype2='facedir',
 node_box={type='fixed',fixed={-.5,-.5,-.14,.5,.5,.14}},
 selection_box={type='fixed',fixed={-.5,-.5,-.14,.5,.5,.14}},
 tiles={'mcl_doors_door_wood_lower.png'},groups={choppy=2},
 on_construct=function(pos) money_node(pos,'Puerta bloqueada',1000) end,
 on_rightclick=function(pos,node,p)
  if not p or not p:is_player() then return end
  if not state.active then return gui_price(p,pos,'door','Puerta') end
  if point_charge(p,fmt_price(pos,1000)) then M.remove_node(pos);tell(p,'Puerta abierta.') end
 end,
})
local PERKS={juggernog={name='Juggernog',price=2500,tile='xz_perk_juggernog.png'},
 staminup={name='Stamin-Up',price=2000,tile='xz_perk_staminup.png'},
 quickrevive={name='Quick Revive',price=1500,tile='xz_perk_quickrevive.png'},
 speedcola={name='Speed Cola',price=3000,tile='xz_perk_speedcola.png'},
 doubletap={name='Double Tap',price=2000,tile='xz_perk_doubletap.png'}}
local function perk_apply(p,id)
 local name=p:get_player_name()
 local meta=p:get_meta()
 meta:set_int('xz_z_perk_'..id,1)
 if id=='juggernog' then p:set_properties({hp_max=40});p:set_hp(math.min(40,p:get_hp()+20)) end
 if id=='staminup' then
  if not prev_physics[name] then prev_physics[name]=p:get_physics_override() end
  local baseline=prev_physics[name]
  p:set_physics_override({speed=(baseline.speed or 1)*1.3})
 end
end
for id,perk in pairs(PERKS) do
 local perk_id, perk_info = id,perk
 M.register_node(':xz_zombies:perk_'..perk_id,{
  description=perk_info.name,tiles={'default_steel_block.png^'..perk_info.tile},
  groups={cracky=2},
  on_construct=function(pos) money_node(pos,perk_info.name,perk_info.price) end,
  on_rightclick=function(pos,node,p)
   if not p or not p:is_player() then return end
   if not state.active then return gui_price(p,pos,'perk',perk_info.name) end
   if p:get_meta():get_int('xz_z_perk_'..perk_id)==1 then tell(p,perk_info.name..' ya comprado.') return end
   if point_charge(p,fmt_price(pos,perk_info.price)) then perk_apply(p,perk_id);tell(p,perk_info.name..' activado.') end
  end,
 })
end
M.register_node(':xz_zombies:spawner',{
 description='Zombies Round Spawner',tiles={'mob_spawner.png'},
 groups={cracky=2},light_source=2,
 on_construct=function(pos)
  M.get_meta(pos):set_string('infotext','Spawner de zombis / rondas')
  saved_spawners[pos_key(pos)]=vector.new(pos);persist_spawners()
 end,
 on_destruct=function(pos) saved_spawners[pos_key(pos)]=nil;persist_spawners() end,
 on_rightclick=function(pos,node,p)
  if not p or not p:is_player() then return end
  if not allowed(p) then return end
  if not state.active then
   tell(p,'Spawner preparado. Presiona PLAY para activar zombis de VoxeLibre.')
   return
  end
  if state.round>0 and state.spawned>=state.round_quota then tell(p,'No quedan zombis por crear en esta ronda.');return end
  if #state.zombies>=director.alive_cap(#M.get_connected_players()) then tell(p,'Limite de zombis vivos alcanzado.');return end
  local ok,desc=spawn_native_zombie(pos)
  if ok then tell(p,'TEST OK: '..desc..' aparecio junto al spawner.')
  else tell(p,'TEST: '..desc);M.log('warning','[xz_zombies_classic] '..desc) end
 end,
})
-- Restore registered spawners when existing saved worlds emerge from disk.
M.register_lbm({label='FIX45 recover Zombies spawners',name='xz_zombies_classic:recover_spawner',
 nodenames={'xz_zombies:spawner'},run_at_every_load=true,
 action=function(pos)
  local key=pos_key(pos)
  if not saved_spawners[key] then
   saved_spawners[key]=vector.new(pos);persist_spawners()
  end
 end,
})
-- NZ:P 0.26 QuakeC gameplay state machine, adapted to Luanti's entity API.
v26=assert(loadfile(modpath .. '/v26_runtime.lua'))()(M,v26_rules,{
 active=function()return state.active end,
 get_round=function()return state.round end,
 add_points=function(player,amount)set_points(player,player_points(player)+amount)end,
 get_zombies=function()return state.zombies end,
 rotu_ai=rotu_ai,
})
-- 1x1 is the original block; multi-cell 1x2 / 2x1 / 2x2 / 3x3
-- reuse the exact seven NZ:P v26 frames and original repair state machine.
assert(loadfile(modpath .. '/v26_sized_barricades.lua'))()(M,v26)
local function reset_perks(p)
  local meta=p:get_meta()
  for id in pairs(PERKS) do meta:set_int('xz_z_perk_'..id,0) end
  if prev_physics[p:get_player_name()] then p:set_physics_override(prev_physics[p:get_player_name()]);prev_physics[p:get_player_name()]=nil end
  p:set_properties({hp_max=20});if p:get_hp()>20 then p:set_hp(20) end
end
local function stop_game()
 state.active=false;state.round=0;state.round_quota=0;state.spawned=0;state.kills=0;state.next_round=0;state.last_spawn_warning=nil;state.v26_spawn_delay=2
 for _,mob in ipairs(state.zombies) do
  if mob.obj and mob.obj:get_pos() then mob.obj:remove() end
 end
 state.zombies={}
 for _,p in ipairs(M.get_connected_players()) do
  reset_perks(p)
  local name=p:get_player_name()
  if prev_armor[name] then p:set_armor_groups(prev_armor[name]);prev_armor[name]=nil end
  developer[name]=nil
  local ok,err=v26_modes.stop(p)
  if not ok then M.log('warning','[xz_zombies_classic] Creative restore: '..tostring(err)) end
  v26_hud.mode(p,false)
  v26_combatfx.stop(p)
 end
 storage:set_int(ACTIVE_STORAGE,0)
end
local function start_game()
 stop_game()
 if not native_zombie() then
  M.chat_send_all('[Zombies] No se encontro el mob de VoxeLibre (mobs_mc). PLAY cancelado.')
  return
 end
 state.active=true;state.round=0;state.round_quota=0;state.next_round=M.get_gametime()+2;state.v26_spawn_delay=2
 state.next_spawn=0
 -- VoxeLibre individual gamemode changes creative->survival for real damage.
 for _,p in ipairs(M.get_connected_players()) do
  local ok,err=v26_modes.play(p)
  if not ok then
   stop_game()
   M.chat_send_all('[Zombies] PLAY cancelado: '..tostring(err))
   return
  end
  v26_hud.mode(p,true)
  set_points(p,500)
 end
 storage:set_int(ACTIVE_STORAGE,1)
 -- No full-screen debug chatter for PLAY; HUD has the status.
end
-- FIX49: Universal responsive phone/tablet/desktop formspecs.
-- Compact pagination avoids a giant fixed 13.2 x 10.3 panel that overlaps controls
-- on 16:9, 20:9, portrait, landscape, foldables, split screen, etc.
local EDITOR_TABS = {'JUEGO','ARMAS','OBJETOS','PERKS','MUNDO'}
local function editor_form(p)
 local name = p:get_player_name()
 local page = math.max(1, math.min(#EDITOR_TABS, editor_pages[name] or 1))
 editor_pages[name] = page
 local w,h = responsive_size(p,9.2,6.5)
 local f=gui_header(w,h,('ZOMBIES EDITOR | %d ARMAS'):format(#WEAPONS))
 fs_button(f,0.25,0.85,0.9,0.68,'page_prev','<')
 fs_label(f,1.35,1.20,('%s (%d/%d)'):format(EDITOR_TABS[page],page,#EDITOR_TABS))
 fs_button(f,w-1.15,0.85,0.9,0.68,'page_next','>')
 -- Every screen uses the same responsive scroll region. No element can overlap
 -- the footer on short/wide phones, and landscape/portrait changes are respected.
 local viewport=math.max(0.75,h-2.60)
 f[#f+1]='scrollbaroptions[min=0;max=100;smallstep=8;largestep=23]'
 f[#f+1]=('scroll_container[0.08,1.65;%.2f,%.2f;editor_scroll;vertical;0.10;0.25]'):format(w-0.51,viewport)
 local y=0.12
 local cw=w-0.80
 local half=(cw-0.16)/2
 if page==1 then
  fs_label(f,0.25,y,('Estado: %s  |  Ronda: %d'):format(state.active and 'PLAY' or 'STOP',state.round))
  y=y+0.48
  fs_button(f,0.25,y,half,0.78,'play','PLAY')
  fs_button(f,0.41+half,y,half,0.78,'stop','STOP')
  y=y+0.95
  fs_button(f,0.25,y,cw,0.78,'developer','DEVELOPER')
  y=y+0.95
  fs_label(f,0.25,y,'Modo editor y juego separados')
 elseif page==2 then
  fs_label(f,0.25,y,'Escoge un arma para colocar en pared')
  y=y+0.42
  local chosen=math.max(1,math.min(#WEAPONS,editor_weapon_index[name] or 1))
  f[#f+1]=('dropdown[0.25,%.2f;%.2f,0.80;weapon;%s;%d;true]'):format(y,cw,table.concat(choices,','),chosen)
  y=y+0.95
  fs_button(f,0.25,y,cw,0.80,'givewall','DAR WALL BUY')
  y=y+0.98
  fs_label(f,0.25,y,'Antes de PLAY: toca el objeto para el precio')
 elseif page==3 then
  if w >= 6.7 then
   fs_button(f,0.25,y,half,0.80,'boxa','MYSTERY BOX A')
   fs_button(f,0.41+half,y,half,0.80,'boxb','MYSTERY BOX B')
   y=y+0.93
  else
   fs_button(f,0.25,y,cw,0.80,'boxa','MYSTERY BOX A')
   y=y+0.93
   fs_button(f,0.25,y,cw,0.80,'boxb','MYSTERY BOX B')
   y=y+0.93
  end
  fs_button(f,0.25,y,cw,0.80,'door','PUERTA CON PRECIO')
  y=y+0.93
  fs_button(f,0.25,y,cw,0.80,'spawner','ZOMBIE SPAWNER')
  y=y+0.93
  for _,size in ipairs({'1x1','1x2','2x1','2x2','3x3'}) do
   fs_button(f,0.25,y,cw,0.80,'barricade_'..size,
     'BARRICADA V26 '..size..' (6 TABLAS)')
   y=y+0.88
  end
 elseif page==4 then
  local entries={{'perk_juggernog','JUGGERNOG'},
    {'perk_speedcola','SPEED COLA'},{'perk_doubletap','DOUBLE TAP'},
    {'perk_quickrevive','QUICK REVIVE'},{'perk_staminup','STAMIN-UP'}}
  -- A single column on narrow displays; two columns when there is room.
  if w>=7.8 and h>=5.7 then
   for i,v in ipairs(entries) do
    local col=(i-1)%2
    local row=math.floor((i-1)/2)
    fs_button(f,0.25+col*(half+0.16),y+row*0.88,half,0.76,v[1],v[2])
   end
  else
   -- On very narrow screens all five perks use a full-width touch target.
   -- Scrolling reveals controls instead of forcing tiny two-column buttons.
   for i,v in ipairs(entries) do
    fs_button(f,0.25,y+(i-1)*0.87,cw,0.76,v[1],v[2])
   end
  end
 elseif page==5 then
  fs_label(f,0.25,y,'Hora del mundo (para este mapa)')
  y=y+0.45
  local mode=storage:get_string('world_time_mode')
  local modes={{'normal','NORMAL'},{'day','SIEMPRE DIA'},{'night','SIEMPRE NOCHE'}}
  for i,v in ipairs(modes) do
   local prefix=(mode==v[1] or (mode=='' and i==1)) and 'OK  ' or ''
   fs_button(f,0.25,y+(i-1)*0.86,cw,0.75,'time_'..v[1],prefix..v[2])
  end
 end
 f[#f+1]='scroll_container_end[]'
 f[#f+1]=('scrollbar[%.2f,1.65;0.21,%.2f;vertical;editor_scroll;0]'):format(w-0.31,viewport)
 f[#f+1]=('button_exit[0.25,%.2f;%.2f,0.67;exit;CERRAR]'):format(h-0.79,w-0.5)
 M.show_formspec(name,form_editor,table.concat(f))
end

local function dev_form(p)
 local name=p:get_player_name()
 local d=developer[name] or {};developer[name]=d
 local page=developer_pages[name] or 1
 local w,h=responsive_size(p,7.8,5.65)
 local f=gui_header(w,h,'ZOMBIES DEVELOPER')
 local half=(w-0.66)/2
 fs_button(f,0.25,0.84,half,0.70,'dev_points','PUNTOS')
 fs_button(f,0.41+half,0.84,half,0.70,'dev_cheats','CHEATS')
 local viewport=math.max(0.75,h-2.66)
 f[#f+1]='scrollbaroptions[min=0;max=100;smallstep=8;largestep=23]'
 f[#f+1]=('scroll_container[0.08,1.67;%.2f,%.2f;dev_scroll;vertical;0.10;0.25]'):format(w-0.51,viewport)
 if page==1 then
  fs_label(f,0.25,0.27,'Pruebas de puntos y arsenal')
  fs_button(f,0.25,0.72,half,0.79,'pts1000','+1,000')
  fs_button(f,0.41+half,0.72,half,0.79,'pts10000','+10,000')
  fs_button(f,0.25,1.67,w-0.80,0.79,'allguns','ACCESO A 28 ARMAS')
 else
  local options={{'god_toggle','VIDA INFINITA',d.god},
    {'ammo_toggle','BALAS INFINITAS',d.ammo},
    {'free_toggle','COMPRAS GRATIS',d.free}}
  for i,o in ipairs(options) do
   fs_button(f,0.25,0.15+(i-1)*0.86,w-0.80,0.73,o[1],(o[3] and '[ON]  ' or '[OFF]  ')..o[2])
  end
 end
 f[#f+1]='scroll_container_end[]'
 f[#f+1]=('scrollbar[%.2f,1.67;0.21,%.2f;vertical;dev_scroll;0]'):format(w-0.31,viewport)
 f[#f+1]=('button_exit[0.25,%.2f;%.2f,0.72;done;CERRAR]'):format(h-0.87,w-0.5)
 M.show_formspec(name,form_dev,table.concat(f))
end
local function give_editor_item(p,item)
 if not allowed(p) then return end
 local inv=p:get_inventory()
 if not inv:room_for_item('main',ItemStack(item)) then tell(p,'Necesitas espacio para colocar '..item..'.') return end
 inv:add_item('main',ItemStack(item))
end
M.register_tool(':xz_zombies:editor_tool',{
 description='ZOMBIES CLASSIC | EDITOR / DEVELOPER',inventory_image='mob_spawner.png',
 on_use=function(item,p) editor_form(p);return item end,
 on_secondary_use=function(item,p) editor_form(p);return item end,
})
M.register_on_joinplayer(function(p)
 local name=p:get_player_name()
 -- Compact COD-style HUD at bottom edges; leave original controls visible.
 v26_hud.attach(p)
 local ok,err=v26_modes.join(p,state.active)
 if not ok then M.log('warning','[xz_zombies_classic] Gamemode join: '..tostring(err)) end
 v26_hud.mode(p,state.active)
 if allowed(p) and not p:get_inventory():contains_item('main','xz_zombies:editor_tool') then
  p:get_inventory():add_item('main','xz_zombies:editor_tool')
 end
 set_points(p,math.max(player_points(p),state.active and 500 or 0))
 if state.active then
  for id in pairs(PERKS) do if p:get_meta():get_int('xz_z_perk_'..id)==1 then perk_apply(p,id) end end
 end
end)
M.register_on_leaveplayer(function(p)
 local n=p:get_player_name()
 v26_hud.detach(p)
 v26_combatfx.detach(p)
 viewers[n]=nil;developer[n]=nil;prev_physics[n]=nil;prev_armor[n]=nil;editor_pages[n]=nil;developer_pages[n]=nil;editor_weapon_index[n]=nil
end)
M.register_on_player_receive_fields(function(p,form,fields)
 local name=p:get_player_name()
 if form==form_buy then
  local v=viewers[name]
  if not v or not allowed(p) then return true end
  if fields.save then
   local price=tonumber(fields.price)
   if price and price>=1 and price<=100000 then
    local pos=v.pos
    local n=M.get_node_or_nil(pos)
    if n and n.name:find('^xz_zombies:') then
     local meta=M.get_meta(pos);meta:set_int('price',math.floor(price))
     meta:set_string('infotext',n.name:match(':([^:]+)$')..' - '..math.floor(price)..' pts')
    end
   end
   viewers[name]=nil
   return true
  end
  if fields.quit then viewers[name]=nil end
  return true
 end
 if form==form_dev then
  if not allowed(p) then return true end
  if fields.dev_points then developer_pages[name]=1;dev_form(p);return true end
  if fields.dev_cheats then developer_pages[name]=2;dev_form(p);return true end
  developer[name]=developer[name] or {};local d=developer[name]
  if fields.god_toggle then
   d.god=not d.god
   if d.god then
    if not prev_armor[name] then prev_armor[name]=p:get_armor_groups() end
    p:set_armor_groups({immortal=1})
   elseif prev_armor[name] then
    p:set_armor_groups(prev_armor[name]);prev_armor[name]=nil
   end
  end
  if fields.ammo_toggle then d.ammo=not d.ammo end
  if fields.free_toggle then d.free=not d.free end
  if fields.pts1000 then set_points(p,player_points(p)+1000) end
  if fields.pts10000 then set_points(p,player_points(p)+10000) end
  if fields.god then
   d.god=(fields.god=='true')
   if d.god then
    if not prev_armor[name] then prev_armor[name]=p:get_armor_groups() end
    p:set_armor_groups({immortal=1})
   elseif prev_armor[name] then
    p:set_armor_groups(prev_armor[name]);prev_armor[name]=nil
   end
  end
  if fields.ammo then d.ammo=fields.ammo=='true' end
  if fields.free then d.free=fields.free=='true' end
  if fields.allguns then
   if _G.weapon_bridge and weapon_bridge.open_catalogue then weapon_bridge.open_catalogue(p) else tell(p,'Usa /armas para las 28 armas.') end
   return true
  end
  if not fields.quit then dev_form(p) end
  return true
 end
 if form~=form_editor then return false end
 if not allowed(p) then return true end
 if fields.page_prev then editor_pages[name]=((editor_pages[name] or 1)-2)%#EDITOR_TABS+1;editor_form(p);return true end
 if fields.page_next then editor_pages[name]=((editor_pages[name] or 1))%#EDITOR_TABS+1;editor_form(p);return true end
 if fields.time_normal or fields.time_day or fields.time_night then
  set_world_time_mode(fields.time_day and 'day' or fields.time_night and 'night' or 'normal')
  editor_form(p);return true
 end
 if fields.weapon then
  local new=tonumber(fields.weapon)
  if new and WEAPONS[new] then editor_weapon_index[name]=new end
 end
 if fields.play then start_game();editor_form(p);return true end
 if fields.stop then stop_game();editor_form(p);return true end
 if fields.developer then if state.active then dev_form(p) else tell(p,'Presiona PLAY para abrir Developer.') end;return true end
 local selections={boxa='xz_zombies:mystery_box_a',boxb='xz_zombies:mystery_box_b',door='xz_zombies:door',spawner='xz_zombies:spawner',
   barricade='xz_zombies:v26_barricade_6',
   barricade_1x1='xz_zombies:v26_barricade_6',
   barricade_1x2='xz_zombies:v26_barricade_6_1x2',
   barricade_2x1='xz_zombies:v26_barricade_6_2x1',
   barricade_2x2='xz_zombies:v26_barricade_6_2x2',
   barricade_3x3='xz_zombies:v26_barricade_6_3x3'}
 for id in pairs(PERKS) do selections['perk_'..id]='xz_zombies:perk_'..id end
 if fields.givewall then
  local chosen=tonumber(fields.weapon) or editor_weapon_index[name] or 1
  editor_weapon_index[name]=chosen
  local weapon=WEAPONS[chosen] or WEAPONS[1]
  give_editor_item(p,'xz_zombies:wall_'..weapon.id)
  return true
 end
 for field,item in pairs(selections) do if fields[field] then give_editor_item(p,item);return true end end
 return true
end)
M.register_chatcommand('zombies',{description='Open Zombies Classic editor',func=function(name)
 local p=M.get_player_by_name(name)
 if not p then return false,'No player' end
 editor_form(p);return true
end})
M.register_chatcommand('zdev',{description='Open Zombies developer mode',func=function(name)
 local p=M.get_player_by_name(name)
 if not allowed(p) or not state.active then return false,'Solo administrador en PLAY' end
 dev_form(p);return true
end})
-- Read-only diagnostics; no weapon, ADS, or USE handler changes.
M.register_chatcommand('zstatus',{description='Zombies round, remaining enemies, spawners',func=function(name)
 local p=M.get_player_by_name(name)
 if not p then return false,'Jugador no encontrado' end
 local count=0
 for _ in pairs(saved_spawners) do count=count+1 end
 return true,('Zombies %s | Ronda %d | Restantes %d | Vivos %d | Spawners %d | Bajas %d'):format(
  state.active and 'PLAY' or 'STOP',state.round,
  director.remaining(state.round_quota,state.spawned,#state.zombies),
  #state.zombies,count,state.kills)
end})
local function update_round()
 local t=M.get_gametime()
 if not state.active then return end
 if state.next_round>0 and t>=state.next_round then
  state.round=state.round+1
  state.next_round=0
  state.spawned=0
  state.kills=0
  state.round_quota=v26_rules.round_quota(state.round,#M.get_connected_players())
  if state.round>1 then state.v26_spawn_delay=v26_rules.next_spawn_delay(state.v26_spawn_delay or 2,1) end
  for _,p in ipairs(M.get_connected_players()) do v26.reset_player_round(p,state.round) end
  state.next_spawn=t
  -- Round info is shown in the compact HUD, not debug chat.
 end
 -- Account once for each round-owned native mob, never for unrelated world mobs.
 local alive={}
 for _,record in ipairs(state.zombies) do
  local obj=record.obj
  if obj and obj:get_pos() and obj:get_hp()>0 then
   alive[#alive+1]=record
  else
   if record.attacker then
    local p=M.get_player_by_name(record.attacker)
    if p and not record.v26_kill_awarded then
     -- v26 DamageHandler already credited +10 for the contact. DieHandler
     -- credits the remaining fatal award, never 50 twice.
     local style=record.v26_last_hit_style or 'lowertorso'
     local kill=v26_rules.damage_score(true,style)
     local prepaid=record.v26_prepaid_last_hit or 0
     set_points(p,player_points(p)+math.max(0,kill-prepaid))
    end
   end
   state.kills=state.kills+1
  end
 end
 state.zombies=alive
 if state.round==0 then return end
 if state.spawned<state.round_quota and
    #state.zombies<director.alive_cap(#M.get_connected_players()) and
    t>=state.next_spawn then
  state.next_spawn=t+(state.v26_spawn_delay or 2)
  local candidates={}
  for _,at in pairs(saved_spawners) do
   local node=M.get_node_or_nil(at)
   if node and node.name=='xz_zombies:spawner' then
    for _,p in ipairs(M.get_connected_players()) do
     if p:get_hp()>0 and vector.distance(p:get_pos(),at)<45 then
      candidates[#candidates+1]=at
      break
     end
    end
   end
  end
  if #candidates>0 then
   local at=candidates[math.random(#candidates)]
   local ok,reason=spawn_native_zombie(at)
   if not ok and (not state.last_spawn_warning or t-state.last_spawn_warning>=12) then
    state.last_spawn_warning=t
    M.log('warning','[xz_zombies_classic] '..reason)
   end
  elseif not state.last_spawn_warning or t-state.last_spawn_warning>=15 then
   state.last_spawn_warning=t
   -- Avoid on-screen debug warnings while surviving.
  end
 elseif state.spawned>=state.round_quota and #state.zombies==0 and state.next_round==0 then
  state.next_round=t+5
  -- Wave transitions are visible in the HUD, not persistent chat.
 end
end
-- Native COD4 projectile source (ak47dev/combat.lua) retains the original
-- target:punch() call.  Post-impact callback gives score for each confirmed
-- hit, while QuakeC window/damage rules supply the original +10/+50 amounts.
local function cod4_post_impact(shooter,target,before,after,damage,intersection)
 if not state.active or not shooter or not shooter.is_player or not shooter:is_player() then return end
 if not target or type(before)~='number' or before<=0 or (tonumber(damage) or 0)<=0 then return end
 for _,record in ipairs(state.zombies) do
  if record.obj==target then
   -- This is an actual COD4 server-side raycast collision. V26's original
   -- DamageHandler grants per-hit score on the event, not on a synchronous
   -- health delta, which VoxeLibre can defer to its on_step.
   local critical=v26.is_head_hit(record,intersection)
   local value=v26.cod4_projectile_impact(record,shooter,before,after,damage,critical)
   if value>0 then v26_combatfx.hit(shooter,damage,critical) end
   return
  end
 end
end
_G.xz_zombies_classic=_G.xz_zombies_classic or {}
_G.xz_zombies_classic.on_cod4_impact=cod4_post_impact
M.register_on_mods_loaded(function()
 local seen={}
 -- Preserve every mob's on_punch and AI; credit all native variants, not only zombie.
 for _,entity_name in ipairs(ZOMBIE_MODELS) do
  if not seen[entity_name] then
   seen[entity_name]=true
   local def=M.registered_entities[entity_name]
   if def then
    local original=def.on_punch
    def.on_punch=function(self,puncher,...)
     local record
     if state.active and puncher and puncher.is_player and puncher:is_player() and self.object then
      for _,candidate in ipairs(state.zombies) do
       if candidate.obj==self.object then
        record=candidate
        record.attacker=puncher:get_player_name()
        break
       end
      end
     end
     local before=record and self.object:get_hp()
     -- Retain native mob attack/animation/damage behavior exactly.
     local result
     if original then result=original(self,puncher,...) end
     -- COD4 bullets emit a definite hit event from combat.lua after the
     -- original punch. Do not also award here or points will double.
     -- Fists and other non-COD4 melee still score through native on_punch.
     if record and before then
      local stack=puncher:get_wielded_item()
      local weapon=stack and stack:get_name() or ''
      if not item_set[weapon] then
       local function award_melee_damage()
        local after=record.obj and record.obj:get_hp()
        v26.zombie_on_punch(record,puncher,before,after)
       end
       if M.after then M.after(0,award_melee_damage) else award_melee_damage() end
      end
     end
     return result
    end
   end
  end
 end
end)
-- FIX50A: dedicated native USE button sends one server command per press.
-- It never triggers PLACE, DIG, ADS or any wielded item callback.
-- Server performs its own short, unobstructed raycast. This also works with
-- weapons equipped, and rejects purchases behind an intervening wall.
local zoom_ads_previous = {}
local zoom_ads_actions = {}
local recent_native_use = {}
local function find_zombies_target(p)
 if not M.raycast or not p or not p:is_player() then return end
 local loc=p:get_pos()
 local props=p:get_properties() or {}
 local eye={x=loc.x,y=loc.y+(props.eye_height or 1.47),z=loc.z}
 local dir=p:get_look_dir()
 local finish={x=eye.x+dir.x*4.5,y=eye.y+dir.y*4.5,z=eye.z+dir.z*4.5}
 for pt in M.raycast(eye,finish,false,false) do
  if pt.type=='node' then
   local node=M.get_node_or_nil(pt.under)
   if not node then return end
   if node.name:find('^xz_zombies:') or node.name=='ak47dev:ammo_crate' then
    local def=M.registered_nodes[node.name]
    if def and type(def.on_rightclick)=='function' then
     return pt.under,node,def,pt
    end
   end
   return -- solid/pointable obstacle; don't interact through it
  end
 end
end
M.register_chatcommand('xz_use',{
 description='Zombies: interact with the object in front (native USE button)',
 params='',
 func=function(name)
  local p=M.get_player_by_name(name)
  if not p then return false,'Player unavailable' end
  local now=M.get_us_time and M.get_us_time()/1000000 or M.get_gametime()
  local last=recent_native_use[name]
  if last and now-last<0.18 then return true,'' end
  recent_native_use[name]=now
  local pos,node,def,pt=find_zombies_target(p)
  if not def then return true,'' end
  -- The node callback retains existing server-side price and ownership checks.
  def.on_rightclick(pos,node,p,p:get_wielded_item(),pt)
  return true,''
 end,
})
M.register_on_mods_loaded(function()
 -- Native ZOOM remains ADS; the old weapon PLACE/secondary override was removed.
 -- Do not override the first-person weapons, their FIRE or their normal ADS.
 local count=0
 for item in pairs(item_set) do
  local def=M.registered_items[item]
  if def and type(def.on_secondary_use)=='function' then
   local original=def.on_secondary_use
   zoom_ads_actions[item]=function(p)
    return original(p:get_wielded_item(),p)
   end
   count=count+1
  end
 end
 M.log('action','[xz_zombies_classic] FIX50A native USE independent; original gun callbacks preserved: '..count)
end)
M.register_on_leaveplayer(function(p)
 local name=p:get_player_name()
 recent_native_use[name]=nil
 zoom_ads_previous[name]=nil
end)

local elapsed=0
local ai_elapsed=0
local score_hud_elapsed=0
M.register_globalstep(function(dt)
 -- Detect actual ZOOM button presses, independently of the PLACE/USE button.
 -- Trigger exactly once per press; do not toggle repeatedly while held.
 for _,p in ipairs(M.get_connected_players()) do
  local name=p:get_player_name()
  local controls=p:get_player_control()
  local pressed=controls and controls.zoom or false
  if pressed and not zoom_ads_previous[name] then
   local item=p:get_wielded_item():get_name()
   local ads=zoom_ads_actions[item]
   if ads then ads(p) end
  end
  zoom_ads_previous[name]=not not pressed
 end
 -- Score cascade runs at ~12Hz, independent from slow server wave tick.
 score_hud_elapsed=score_hud_elapsed+dt
 if score_hud_elapsed>=0.085 then
  v26_hud.step(score_hud_elapsed)
  v26_combatfx.step()
  score_hud_elapsed=0
 end
 -- NZ:P v26 Zombie_Think compatibility: only round-controlled mobs, not world mobs.
 ai_elapsed=ai_elapsed+dt
 if state.active and ai_elapsed>=0.25 then
  for _,record in ipairs(state.zombies) do v26.zombie_think(record,ai_elapsed) end
  ai_elapsed=0
 end
 elapsed=elapsed+dt
 if elapsed<1 then return end
 elapsed=0
 update_round()
 for _,p in ipairs(M.get_connected_players()) do
  local name=p:get_player_name()
  local remaining=director.remaining(state.round_quota,state.spawned,#state.zombies)
  v26_hud.wave(p,state.round,remaining,state.active)
  v26_hud.points(p,player_points(p))
  local d=developer[name]
  if state.active and d and d.ammo and _G.weapon_bridge then
   local item=p:get_wielded_item():get_name()
   local s
   local api=weapon_bridge.arsenal_api
   if api and api.definitions[item] then s=api.state(p)
   elseif weapon_bridge.core_state and (item=='ak47dev:ak47' or item=='ak47dev:m9') then s=weapon_bridge.core_state(p) end
   if s then
    local def=api and api.definitions[item]
    local cap=def and def.capacity or item=='ak47dev:m9' and 15 or 30
    if s.ammo<cap then s.ammo=cap end
    s.reserve=9999
    if s.gl_ammo~=nil then s.gl_ammo=1;s.gl_reserve=999 end
   end
  end
  if state.active and p:get_meta():get_int('xz_z_perk_speedcola')==1 and _G.weapon_bridge then
   local api=weapon_bridge.arsenal_api
   local s=api and api.definitions[p:get_wielded_item():get_name()] and api.state(p)
   if s and s.reload_end and s.reload_end>0 and not s.xz_speed_treated then
    local t=M.get_us_time()/1000000
    s.reload_end=t+(s.reload_end-t)*.65
    s.xz_speed_treated=true
   elseif s and (not s.reload_end or s.reload_end<=0) then s.xz_speed_treated=false end
  end
 end
end)
M.log('action','[xz_zombies_classic] FIX54 exact Xziel Viril combat numbers and confirmed bullet hit score, original NZP VM source preserved.')