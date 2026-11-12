-- NZ:P v0.26 -> Luanti runtime API adapter.
-- The behavior, values and state changes come from ORIGINAL NZ:P QuakeC:
-- server/entities/window.qc, server/ai/{ai_core,zombie_core}.qc,
-- server/damage.qc.  Copyright NZ:P Team. GPL-2.0-or-later.
-- This file translates QuakeC world/entity calls to Luanti's API; does not
-- replace the native COD4 first-person weapons, audio, HUD or controls.
return function(M,V,hooks)
 local A={}

 local function now()
  return M.get_us_time and M.get_us_time()/1000000 or M.get_gametime()
 end
 local function stage_name(stage)
  return "xz_zombies:v26_barricade_"..tostring(stage)
 end
 A.stage_name=stage_name
 local function get_meta(p)
  return M.get_meta(p)
 end
 local function get_stage(p)
  local n=M.get_node_or_nil(p)
  if not n then return nil end
  return tonumber(n.name:match("^xz_zombies:v26_barricade_([0-6])$"))
 end
 A.get_stage=get_stage

 local function emit(pos,sound)
  if M.sound_play then M.sound_play(sound,{pos=pos,gain=0.6,max_hear_distance=14}) end
 end

 local function change_stage(pos,newstage)
  local old=M.get_node(pos)
  local param2=old and old.param2 or 0
  M.swap_node(pos,{name=stage_name(newstage),param2=param2})
  get_meta(pos):set_int("nzp_v26_planks",newstage)
 end

 local function reward_repair(player)
  local pm=player:get_meta()
  local round=hooks.get_round()
  if pm:get_int("nzp_v26_barricade_reward_round")~=round then
   pm:set_int("nzp_v26_barricade_reward_round",round)
   pm:set_int("nzp_v26_barricade_reward",0)
  end
  local earned=pm:get_int("nzp_v26_barricade_reward")
  if earned < V.repair_cap(round) then
   pm:set_int("nzp_v26_barricade_reward",earned+V.repair_points)
   hooks.add_points(player,V.repair_points)
  end
 end

 function A.repair(pos,player)
  if not hooks.active() or not player or not player:is_player() then return false end
  if player:get_hp()<=0 then return false end
  if M.is_protected and M.is_protected(pos,player:get_player_name()) then return false end
  local stage=get_stage(pos)
  if not stage or stage>=6 then return false end
  local meta=get_meta(pos)
  local when=now()
  if when<meta:get_float("nzp_v26_next_repair") then return false end
  -- QuakeC window_touch: exactly ONE plank per USE, .75 seconds between.
  meta:set_float("nzp_v26_next_repair",when+V.repair_delay)
  change_stage(pos,stage+1)
  emit(pos,"nzp_v26_barricade")
  reward_repair(player)
  return true
 end

 function A.zombie_break(pos)
  local stage=get_stage(pos)
  if not stage or stage<=0 then return false end
  -- QuakeC Window_Damage: remove exactly ONE board on each rip attack.
  change_stage(pos,stage-1)
  emit(pos,"nzp_v26_barricade_destroy")
  return true
 end

 local descriptor={
  description="NZ:P v26 | Barricada (6 tablas originales)",
  paramtype="light",paramtype2="facedir",
  sunlight_propagates=true,
  groups={choppy=2,oddly_breakable_by_hand=2},
  selection_box={type="fixed",fixed={-0.5,-0.5,-0.2,0.5,0.5,0.2}},
  on_rightclick=function(pos,node,clicker)
   A.repair(pos,clicker)
  end,
 }
 for i=0,6 do
  local desc={}
  for k,v in pairs(descriptor) do desc[k]=v end
  desc.description="NZ:P v26 | Barricada "..i.."/6"
  desc.groups={choppy=2,oddly_breakable_by_hand=2,not_in_creative_inventory=(i==6 and 0 or 1)}
  desc.drawtype=(i==0 and "airlike" or "mesh")
  if i>0 then
   desc.mesh="nzp_v26_window_"..i..".obj"
   desc.tiles={"nzp_v26_window.png"}
  end
  desc.walkable=(i>0)
  desc.buildable_to=false
  desc.on_construct=function(pos)
   local meta=get_meta(pos)
   meta:set_int("nzp_v26_planks",i)
   meta:set_string("infotext","Barricada NZ:P v26 | "..i.."/6")
  end
  M.register_node(":"..stage_name(i),desc)
 end

 function A.reset_player_round(player,round)
  local meta=player:get_meta()
  meta:set_int("nzp_v26_barricade_reward_round",round)
  meta:set_int("nzp_v26_barricade_reward",0)
 end

 -- World/AI translation layer for Zombie_Think, Inside_Walk and
 -- zombie_attack2. Target retarget every 5s, 60 Quake units melee
 -- trigger, 64 units damage cutoff, attack delay 1..2s.
 -- Quake coordinate conversion: 32 source units ~ 1 Luanti node.
 local UNIT=32
 local function length(a,b)
  local dx,dy,dz=a.x-b.x,a.y-b.y,a.z-b.z
  return math.sqrt(dx*dx+dy*dy+dz*dz)
 end
 local function living_target(obj)
  local origin=obj:get_pos()
  if not origin then return nil end
  local closest,best=nil,math.huge
  for _,p in ipairs(M.get_connected_players()) do
   if p:get_hp()>0 then
    local q=p:get_pos()
    local dist=length(origin,q)
    if dist<best then closest,best=p,dist end
   end
  end
  return closest,best
 end

 local function nearest_barricade(origin,target)
  if not target then return nil end
  -- Single-window gate: barricade is between zombie and target, not simply
  -- any board in the room. Exact window state semantics from window.qc.
  local targetpos=target:get_pos()
  local facing={x=targetpos.x-origin.x,z=targetpos.z-origin.z}
  local norm=math.sqrt(facing.x*facing.x+facing.z*facing.z)
  if norm<0.01 then return nil end
  facing.x,facing.z=facing.x/norm,facing.z/norm
  local best,bestdist=nil,math.huge
  for dx=-2,2 do for dy=-1,1 do for dz=-2,2 do
   local pos={x=math.floor(origin.x+dx+0.5),y=math.floor(origin.y+dy+0.5),z=math.floor(origin.z+dz+0.5)}
   local stage=get_stage(pos)
   if stage and stage>0 then
    local vx,vz=pos.x-origin.x,pos.z-origin.z
    local toward=vx*facing.x+vz*facing.z
    local dis=math.sqrt(vx*vx+vz*vz)
    if toward>0 and dis<bestdist and dis<=2.1 then
     best,bestdist=pos,dis
    end
   end
  end end end
  return best,bestdist
 end

 local function attack_player(p,obj)
  if p and p:get_hp()>0 and obj then
   -- Original v26 50/100 damage = 10 of VoxeLibre's 20 health points.
   -- MCL damage requires an actual punch ObjectRef; this is a set_hp hit,
   -- so use the supported Mob classification rather than type='punch'.
   -- Passing a fake punch without object is the EXACT cause of the crash.
   p:set_hp(math.max(0,p:get_hp()-V.attack_damage/5),{
    type='set_hp',_mcl_type='mob',_mcl_direct=obj,_mcl_source=obj
   })
  end
 end

 function A.zombie_think(record,dt)
  local obj=record.obj
  if not obj or not obj:get_pos() or obj:get_hp()<=0 then return end
  local entity=obj:get_luaentity()
  local native=entity and type(entity.do_attack)=='function'
  local target,distance=record.v26_target,math.huge
  local t=now()
  if not target or not target:get_pos() or target:get_hp()<=0 or (record.v26_retarget or 0)<=t then
   target,distance=living_target(obj)
   record.v26_target=target
   record.v26_retarget=t+V.attack_retarget_delay
  elseif target then
   distance=length(obj:get_pos(),target:get_pos())
  end
  if not target then return end
  local origin=obj:get_pos()
  local barrier=nearest_barricade(origin,target)
  record.v26_barrier=barrier
  if barrier then
   -- Original window.qc one plank per hit. Native AI must NOT attack player
   -- through the window; its do_states() is suspended by the per-mob do_custom
   -- wrapper below while it rips planks.
   if native then
    entity.attack=nil
    entity.state='stand'
    if entity.set_velocity then entity:set_velocity(0) end
   end
   if t>=(record.v26_attack_next or 0) then
    record.v26_attack_next=t+V.attack_min_cooldown+math.random()*V.attack_random_cooldown
    A.zombie_break(barrier)
   end
   return
  end
  if native then
   -- FIX53: the old obj:set_velocity() was overwritten every server step by
   -- VoxeLibre's mcl_mobs:do_states(). do_attack() is its actual pathfinding
   -- and animation controller, and respects the real survival gamemode.
   -- We set native attack damage to the scaled original v26 damage at spawn.
   entity.force_attack=true
   entity._aggro=true
   entity.view_range=math.max(45,entity.view_range or 16)
   if entity.state~='attack' or entity.attack~=target then
    if entity.state=='attack' and entity.attack~=target then entity.state='stand' end
    entity:do_attack(target)
   end
   return
  end
  -- Compatibility fallback ONLY for custom mobs lacking VoxeLibre's
  -- do_attack() API. It retains original v26 delay and damage scaling.
  if distance<V.attack_trigger_range_quake/UNIT then
   if t>=(record.v26_attack_next or 0) then
    record.v26_attack_next=t+V.attack_min_cooldown+math.random()*V.attack_random_cooldown
    if length(obj:get_pos(),target:get_pos())<V.attack_range_quake/UNIT then
     attack_player(target,obj)
    end
   end
   return
  end
  local goal=target:get_pos()
  if M.line_of_sight and not M.line_of_sight(origin,goal) and M.find_path then
   if t>=(record.v26_path_at or 0) then
    record.v26_path=M.find_path(origin,goal,12,1,3,'A*')
    record.v26_path_at=t+1
   end
   if record.v26_path and #record.v26_path>=2 then goal=record.v26_path[2] end
  end
  local dx,dz=goal.x-origin.x,goal.z-origin.z
  local flat=math.sqrt(dx*dx+dz*dz)
  if flat>0.03 and obj.set_velocity and obj.get_velocity then
   local old=obj:get_velocity() or {y=0}
   local speed=(8/0.12)/UNIT -- v26 zombie_walk1 original Quake units
   obj:set_velocity({x=dx/flat*speed,y=old.y,z=dz/flat*speed})
  end
 end

 function A.install_native_ai(record)
  local entity=record.obj and record.obj:get_luaentity()
  if not entity or type(entity.do_attack)~='function' then return false end
  local original=entity.do_custom
  entity.force_attack=true
  entity._aggro=true
  entity.type='monster'
  entity.attack_type='dogfight'
  entity.view_range=math.max(entity.view_range or 16,45)
  entity.reach=V.attack_trigger_range_quake/UNIT
  entity.damage=V.attack_damage/5
  -- Vanilla Mob on_step invokes do_custom before do_states. Suppress only
  -- attack state while physically blocked by a live original v26 window.
  -- This hook belongs to THIS spawned instance, not all VoxeLibre mobs.
  entity.do_custom=function(self,dtime)
   if record.v26_barrier and A.get_stage(record.v26_barrier)>0 then
    self.attack=nil
    self.state='stand'
    if self.set_velocity then self:set_velocity(0) end
    return false
   end
   if original then return original(self,dtime) end
  end
  return true
 end

 function A.zombie_on_punch(record,puncher,health_before,health_after)
  if not hooks.active() or not puncher or not puncher.is_player or not puncher:is_player() then return end
  local old=math.max(0,tonumber(health_before) or 0)
  local new=tonumber(health_after)
  if not new or new>=old or old<=0 then return end
  local lethal=new<=0
  local style="lowertorso"
  local stack=puncher:get_wielded_item()
  local weapon=stack and stack:get_name() or ""
  if weapon:find("knife",1,true) or weapon:find("melee",1,true) then style="melee" end
  local award=V.damage_score(lethal,style)
  hooks.add_points(puncher,award)
  record.attacker=puncher:get_player_name()
  if lethal then record.v26_kill_awarded=true end
 end

 return A
end
