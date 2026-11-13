-- FIX55: CoD4 Reign of the Undead v2.x bot decision adapter.
-- Adapted from Reign of the Undead Team (2010-2026), MIT-licensed GSC:
-- scripts/bots/_bot.gsc: bestTarget(), botStateToString(), setSpeed(), wander()
-- scripts/include/waypoints.gsc: waypoint navigation and A* route recovery.
-- https://github.com/marktaff/reign-of-the-undead
-- Full upstream MIT license and special end-credit notice in ROTU-SOURCE-NOTICE.txt.
-- This is not a Quake/GSC VM. Movement/melee MUST remain native VoxeLibre mcl_mobs;
-- no imported proprietary Activision textures, models or sounds.
return function(M)
 local A={}
 local NEXT_PATH_BUDGET=0
 local function now()
  if M.get_us_time then return M.get_us_time()/1000000 end
  return M.get_gametime()
 end
 local function sq(a,b)
  local x,y,z=a.x-b.x,a.y-b.y,a.z-b.z
  return x*x+y*y+z*z
 end
 local function valid(p)
  return p and p.get_pos and p.get_hp and p:get_hp()>0 and p:get_pos()~=nil
 end
 local function seen(entity,origin,player)
  if entity and type(entity.target_visible)=='function' then
   local ok,value=pcall(entity.target_visible,entity,entity.object,player)
   if ok then return value==true end
  end
  if M.line_of_sight then
   local dst=player:get_pos()
   local ok,visible=pcall(M.line_of_sight,
    {x=origin.x,y=origin.y+1.0,z=origin.z},
    {x=dst.x,y=dst.y+1.0,z=dst.z})
   if ok then return visible==true end
  end
  -- On a mock/older engine with no LOS API use nearest, never hallucinate visibility.
  return false
 end
 function A.acquire(record,entity,origin)
  local clock=now()
  local brain=record.rotu_ai
  if not brain then brain={status='SEARCHING',next_scan=0,stuck_for=0,next_route=0};record.rotu_ai=brain end
  if clock<brain.next_scan and valid(brain.target) then
   return brain.target,math.sqrt(sq(origin,brain.target:get_pos()))
  end
  -- Exact target priority in RotU _bot.gsc: bestTarget(): closest VISIBLE
  -- living player; otherwise closest living player; never target a dead player.
  local closest,nearest_visible,close_d,visible_d=nil,nil,math.huge,math.huge
  for _,player in ipairs(M.get_connected_players()) do
   if valid(player) then
    local d=sq(origin,player:get_pos())
    if d<close_d then closest,close_d=player,d end
    if d<visible_d and seen(entity,origin,player) then
     nearest_visible,visible_d=player,d
    end
   end
  end
  brain.target=nearest_visible or closest
  brain.next_scan=clock+0.9
  if brain.target then return brain.target,math.sqrt(sq(origin,brain.target:get_pos())) end
  brain.status='SEARCHING'
  return nil,math.huge
 end
 function A.barrier(record)
  local brain=record.rotu_ai
  if brain then brain.status='BARRICADE';brain.stuck_for=0 end
 end
 function A.think(record,entity,target,distance,dt,round)
  local brain=record.rotu_ai
  if not brain then return false end
  if not valid(target) then brain.status='SEARCHING';return false end
  local pos=record.obj:get_pos()
  if not pos then return false end
  local goal=target:get_pos()
  local visible=seen(entity,pos,target)
  -- RotU states: SEARCHING -> STALKING/PURSUING -> MELEE; when sight lost,
  -- REACQUIRE_TARGET using remembered player position.
  if visible then
   brain.last_seen={x=goal.x,y=goal.y,z=goal.z}
   brain.last_sighted_at=now()
   brain.status=distance <= (entity.reach or 1.8) and 'MELEE' or
    distance<8 and 'PURSUING' or 'STALKING'
  else
   brain.status=brain.last_seen and 'REACQUIRE_TARGET' or 'SEARCHING'
  end
  -- Original RotU setSpeed() switches from walk to run on alert. Keep the
  -- established VoxeLibre speeds/animations rather than setting raw velocities.
  local stage=math.max(1,tonumber(round) or 1)
  entity.walk_velocity=math.max(entity.walk_velocity or .8,.90)
  entity.run_velocity=math.max(entity.run_velocity or 1.8,math.min(3.20,1.95+0.075*(stage-1)))
  entity.pathfinding=1 -- actual VoxeLibre smart_mobs() A* and stuck logic
  if brain.last_pos then
   if sq(pos,brain.last_pos)<0.16 and distance>3 then
    brain.stuck_for=brain.stuck_for+dt
   else
    brain.stuck_for=0
   end
  end
  brain.last_pos={x=pos.x,y=pos.y,z=pos.z}
  -- While built-in gopath is walking a path, never overwrite it with do_attack.
  if entity.state=='gowp' then return true end
  if distance<=3 or distance>23 or type(entity.gopath)~='function' then return false end
  local clock=now()
  if clock<(brain.next_route or 0) or clock<NEXT_PATH_BUDGET then return false end
  -- Repath only if stuck, or after losing sight for at least 1.25 sec.
  local lost=not visible and brain.last_seen and
   (clock-(brain.last_sighted_at or clock))>=1.25
  if brain.stuck_for<1.5 and not lost then return false end
  local dest=brain.last_seen or goal
  if sq(pos,dest)>23*23 then dest=goal end
  brain.next_route=clock+4.0 -- expensive A* pathfinding mobile budget
  NEXT_PATH_BUDGET=clock+0.35 -- across ALL zombies
  local ok,result=pcall(entity.gopath,entity,dest,function(mob)
   mob.order=nil
   if mob.state~='die' and valid(target) then
    mob.state='stand'
    mob:do_attack(target)
   end
  end,false)
  if ok and (result or entity.state=='gowp') then
   brain.status='REACQUIRE_TARGET'
   brain.stuck_for=0
   return true
  end
  return false -- safely delegate back to original v26/native chase
 end
 return A
end
