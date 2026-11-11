-- FIX44 COD4 Zombies Classic. Adds features without removing any FIX43 assets.
local M = minetest
local MOD = M.get_current_modname()
local storage = M.get_mod_storage()
local modpath = M.get_modpath(MOD)
local root = M.get_modpath('ak47dev')
local source = assert(loadfile(root .. '/arsenal_catalog.lua'))()
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
local state = {active=false,round=0,spawned=0,kills=0,next_spawn=0,round_delay=0,zombies={},next_round=0}
local viewers, developer, huds, prev_physics, prev_armor = {}, {}, {}, {}, {}
local ACTIVE_STORAGE='active'
local saved_spawners = M.deserialize(storage:get_string('spawner_positions')) or {}
local function persist_spawners() storage:set_string('spawner_positions', M.serialize(saved_spawners)) end
-- FIX45 test: use native VoxeLibre entities and their existing mesh, texture and AI.
local ZOMBIE_MODELS = {
 'mobs_mc:zombie', 'mobs_mc:zombie', 'mobs_mc:zombie',
 'mobs_mc:husk', 'mobs_mc:villager_zombie', 'mobs_mc:baby_zombie',
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
 obj:set_hp(20+state.round*4)
 state.zombies[#state.zombies+1]={obj=obj}
 state.spawned=state.spawned+1
 return true,name
end

local function allowed(p) return p and p:is_player() and (M.is_singleplayer() or M.check_player_privs(p,{server=true})) end
local function player_points(p) return p:get_meta():get_int('xz_z_points') end
local function set_points(p,n)
  p:get_meta():set_int('xz_z_points',math.max(0,math.floor(n)))
  if huds[p:get_player_name()] then p:hud_change(huds[p:get_player_name()],'text',('ZOMBIES  R%d  |  %d PTS'):format(state.round,player_points(p))) end
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
local function gui_price(p,pos,kind,desc)
  viewers[p:get_player_name()]={pos=vector.new(pos),kind=kind}
  local price=fmt_price(pos,kind=='wall' and 1200 or kind=='door' and 1000 or kind=='mystery' and 950 or 2500)
  M.show_formspec(p:get_player_name(),form_buy,'formspec_version[4]size[8.5,4.2]label[0.5,0.5;'..M.formspec_escape(desc)..']field[0.5,1.2;7.5,0.9;price;Precio;'..price..']button[0.6,2.6;3.2,0.8;save;GUARDAR]button_exit[4.3,2.6;3.2,0.8;cancel;CERRAR]')
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
 M.register_node('xz_zombies:wall_'..weapon.id,{
  description='Wall Buy | '..weapon.label,
  drawtype='mesh',mesh='xz_wall_'..weapon.id..'.obj',tiles={'xz_wall_'..weapon.id..'.png'},
  paramtype='light',paramtype2='facedir',sunlight_propagates=true,
  walkable=false,pointable=true,buildable_to=false,
  selection_box={type='fixed',fixed={-.47,-.18,-.15,.47,.24,.15}},
  groups={cracky=3,oddly_breakable_by_hand=1},inventory_image=weapon.icon,
  on_construct=function(pos) money_node(pos,weapon.label,weapon.price) end,
  on_rightclick=function(pos,node,p) if p and p:is_player() then wall_action(pos,p,weapon) end end,
  on_destruct=function(pos) end,
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
 M.register_node('xz_zombies:mystery_box_'..letter,{
  description='Mystery Box '..string.upper(letter),tiles={'mcl_chests_normal.png'},
  groups={choppy=2,oddly_breakable_by_hand=2},
  on_construct=function(pos) money_node(pos,'Mystery Box '..letter,950) end,
  on_rightclick=function(pos,node,p) if p and p:is_player() then mystery_action(pos,p) end end,
 })
end
M.register_node('xz_zombies:door',{
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
 M.register_node('xz_zombies:perk_'..perk_id,{
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
M.register_node('xz_zombies:spawner',{
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
  if #state.zombies>=12 then tell(p,'Limite de 12 zombis vivos alcanzado.');return end
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
local function reset_perks(p)
  local meta=p:get_meta()
  for id in pairs(PERKS) do meta:set_int('xz_z_perk_'..id,0) end
  if prev_physics[p:get_player_name()] then p:set_physics_override(prev_physics[p:get_player_name()]);prev_physics[p:get_player_name()]=nil end
  p:set_properties({hp_max=20});if p:get_hp()>20 then p:set_hp(20) end
end
local function stop_game()
 state.active=false;state.round=0;state.spawned=0;state.kills=0;state.next_round=0
 for _,mob in ipairs(state.zombies) do
  if mob.obj and mob.obj:get_pos() then mob.obj:remove() end
 end
 state.zombies={}
 for _,p in ipairs(M.get_connected_players()) do
  reset_perks(p)
  local name=p:get_player_name()
  if prev_armor[name] then p:set_armor_groups(prev_armor[name]);prev_armor[name]=nil end
  developer[name]=nil
 end
 storage:set_int(ACTIVE_STORAGE,0)
end
local function start_game()
 stop_game()
 if not native_zombie() then
  M.chat_send_all('[Zombies] No se encontro el mob de VoxeLibre (mobs_mc). PLAY cancelado.')
  return
 end
 state.active=true;state.round=0;state.next_round=M.get_gametime()+2
 state.next_spawn=0
 for _,p in ipairs(M.get_connected_players()) do set_points(p,500) end
 storage:set_int(ACTIVE_STORAGE,1)
 M.chat_send_all('[Zombies] PLAY listo. Coloca un Spawner y acercate a menos de 45 bloques. Tocalo para TEST instantaneo.')
end
local function editor_form(p)
 local name=p:get_player_name()
 local admin=allowed(p)
 local f={'formspec_version[4]size[13.2,10.3]bgcolor[#16191F;true]',
 'label[0.4,0.4;ZOMBIES CLASSIC | FIX44 | 28 ARMAS]',
 ('label[0.4,0.95;Estado: %s | Ronda: %d]'):format(state.active and 'PLAY' or 'STOP',state.round),
 'button[0.4,1.5;2.8,0.8;play;PLAY]button[3.5,1.5;2.8,0.8;stop;STOP]',
 'button[6.6,1.5;2.9,0.8;developer;DEVELOPER]',
 'label[0.4,2.6;Crear Wall Buys - todos tienen su modelo 3D propio]',
 'dropdown[0.4,3.0;8.7,0.8;weapon;'..table.concat(choices,',')..';1;true]',
 'button[9.4,3.0;3.3,0.8;givewall;DAR WALL BUY]',
 'button[0.4,4.2;4.0,0.8;boxa;MYSTERY BOX A]',
 'button[4.6,4.2;4.0,0.8;boxb;MYSTERY BOX B]',
 'button[8.8,4.2;3.9,0.8;door;PUERTA CON PRECIO]',
 'button[0.4,5.4;4,0.8;spawner;ZOMBIE SPAWNER]',
 'button[4.6,5.4;4,0.8;perk_juggernog;JUGGERNOG]',
 'button[8.8,5.4;3.9,0.8;perk_speedcola;SPEED COLA]',
 'button[0.4,6.6;4,0.8;perk_doubletap;DOUBLE TAP]',
 'button[4.6,6.6;4,0.8;perk_quickrevive;QUICK REVIVE]',
 'button[8.8,6.6;3.9,0.8;perk_staminup;STAMIN-UP]',
 'label[0.4,7.8;Coloca el bloque. Pulsa para configurar precio antes de PLAY.]',
 'label[0.4,8.4;En PLAY pulsa el bloque para comprar. /zombies abre este menu.]',
 'button_exit[9.1,9.3;3.5,0.7;quit;CERRAR]' }
 if not admin then f[#f+1]='label[0.4,9.3;Modo editor solo disponible para administrador.]' end
 M.show_formspec(name,form_editor,table.concat(f))
end
local function dev_form(p)
 local name=p:get_player_name()
 developer[name]=developer[name] or {}
 local d=developer[name]
 local f={'formspec_version[4]size[10.2,7.2]bgcolor[#15171E;true]',
  'label[0.4,0.5;ZOMBIES DEVELOPER]',
  'button[0.5,1.5;4.0,0.8;pts1000;+1,000 PUNTOS]',
  'button[5.0,1.5;4.4,0.8;pts10000;+10,000 PUNTOS]',
  ('checkbox[0.6,3.0;god;VIDA INFINITA;%s]'):format(tostring(d.god or false)),
  ('checkbox[5.1,3.0;ammo;BALAS INFINITAS;%s]'):format(tostring(d.ammo or false)),
  ('checkbox[0.6,4.2;free;COMPRAS GRATIS;%s]'):format(tostring(d.free or false)),
  'button[5.0,4.0;4.4,0.9;allguns;ACCESO A 28 ARMAS]',
  'button_exit[6.1,5.9;3.3,0.8;done;CERRAR]'}
 M.show_formspec(name,form_dev,table.concat(f))
end
local function give_editor_item(p,item)
 if not allowed(p) then return end
 local inv=p:get_inventory()
 if not inv:room_for_item('main',ItemStack(item)) then tell(p,'Necesitas espacio para colocar '..item..'.') return end
 inv:add_item('main',ItemStack(item))
end
M.register_tool('xz_zombies:editor_tool',{
 description='ZOMBIES CLASSIC | EDITOR / DEVELOPER',inventory_image='mob_spawner.png',
 on_use=function(item,p) editor_form(p);return item end,
 on_secondary_use=function(item,p) editor_form(p);return item end,
})
M.register_on_joinplayer(function(p)
 local name=p:get_player_name()
 huds[name]=p:hud_add({hud_elem_type='text',position={x=0.5,y=0.05},alignment={x=0,y=0},number=0xffe4b5,text='ZOMBIES CLASSIC',z_index=180})
 if allowed(p) and not p:get_inventory():contains_item('main','xz_zombies:editor_tool') then
  p:get_inventory():add_item('main','xz_zombies:editor_tool')
 end
 set_points(p,math.max(player_points(p),state.active and 500 or 0))
 if state.active then
  for id in pairs(PERKS) do if p:get_meta():get_int('xz_z_perk_'..id)==1 then perk_apply(p,id) end end
 end
end)
M.register_on_leaveplayer(function(p)
 local n=p:get_player_name();huds[n]=nil;viewers[n]=nil;developer[n]=nil;prev_physics[n]=nil;prev_armor[n]=nil
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
  developer[name]=developer[name] or {};local d=developer[name]
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
 if fields.play then start_game();editor_form(p);return true end
 if fields.stop then stop_game();editor_form(p);return true end
 if fields.developer then if state.active then dev_form(p) else tell(p,'Presiona PLAY para abrir Developer.') end;return true end
 local selections={boxa='xz_zombies:mystery_box_a',boxb='xz_zombies:mystery_box_b',door='xz_zombies:door',spawner='xz_zombies:spawner'}
 for id in pairs(PERKS) do selections['perk_'..id]='xz_zombies:perk_'..id end
 if fields.givewall then
  local chosen=tonumber(fields.weapon) or 1
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
local function update_round()
 local t=M.get_gametime()
 if not state.active then return end
 if state.next_round>0 and t>=state.next_round then
  state.round=state.round+1;state.next_round=0;state.spawned=0;state.kills=0
  M.chat_send_all('[Zombies] RONDA '..state.round)
 end
 local alive={}
 for _,record in ipairs(state.zombies) do
  local obj=record.obj
  if obj and obj:get_pos() and obj:get_hp()>0 then alive[#alive+1]=record
  else
   if record.attacker then
    local p=M.get_player_by_name(record.attacker)
    if p then set_points(p,player_points(p)+100) end
   end
   state.kills=state.kills+1
  end
 end
 state.zombies=alive
 if state.round==0 then return end
 local total=5+state.round*3
 if state.spawned<total and #state.zombies<12 and t>=state.next_spawn then
  state.next_spawn=t+3
  local candidates={}
  for _,at in pairs(saved_spawners) do
   local n=M.get_node_or_nil(at)
   if n and n.name=='xz_zombies:spawner' then
    for _,p in ipairs(M.get_connected_players()) do
     if vector.distance(p:get_pos(),at)<45 then candidates[#candidates+1]=at;break end
    end
   end
  end
  if #candidates>0 then
   local at=candidates[math.random(#candidates)]
   local ok,reason=spawn_native_zombie(at)
   if not ok and (not state.last_spawn_warning or t-state.last_spawn_warning>=10) then
    state.last_spawn_warning=t
    M.log('warning','[xz_zombies_classic] '..reason)
   end
  end
 elseif state.spawned>=total and #state.zombies==0 and state.next_round==0 then
  state.next_round=t+5
 end
end
M.register_on_mods_loaded(function()
 local def=M.registered_entities['mobs_mc:zombie']
 if not def then M.log('warning','[xz_zombies_classic] mobs_mc:zombie missing; spawner cannot create zombies.') return end
 -- Track last hit for round-kill points; original AI and on_punch are preserved.
 local original=def.on_punch
 def.on_punch=function(self,puncher,...)
  if state.active and puncher and puncher:is_player() and self.object then
   for _,rec in ipairs(state.zombies) do if rec.obj==self.object then rec.attacker=puncher:get_player_name();break end end
  end
  if original then return original(self,puncher,...) end
 end
end)
local elapsed=0
M.register_globalstep(function(dt)
 elapsed=elapsed+dt
 if elapsed<1 then return end
 elapsed=0
 update_round()
 for _,p in ipairs(M.get_connected_players()) do
  local name=p:get_player_name()
  if huds[name] then p:hud_change(huds[name],'text',('ZOMBIES  R%d  |  %d PTS'):format(state.round,player_points(p))) end
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
M.log('action','[xz_zombies_classic] FIX45 native VoxeLibre zombie spawner test loaded. Original arsenal remains untouched.')
