-- FIX56: Retain RotU target priorities, restore native VoxeLibre live pursuit.
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
  -- ORIGINAL VoxeLibre mcl_mobs/combat.lua has live chase + smart_mobs A*.
  -- FIX55's gopath() forced a stale static destination (line-following bug).
  -- Re-use the native attack controller; DO NOT create a parallel path follower.
  local stage=math.max(1,tonumber(round) or 1)
  entity.walk_velocity=math.max(entity.walk_velocity or .8,.90)
  entity.run_velocity=math.max(entity.run_velocity or 1.8,math.min(3.20,1.95+0.075*(stage-1)))
  entity.pathfinding=1
  local clock=now()
  -- Rescue an in-progress FIX55 fixed-position path (this instance only).
  -- VoxeLibre gopath() explicitly rejects destinations while state='gowp'.
  if entity.state=='gowp' then
   entity.state='stand'
   entity._target=nil
   entity.current_target=nil
   entity.waypoints=nil
   entity.callback_arrived=nil
   brain.status='REACQUIRE_TARGET'
   brain.next_awareness_at=0
  end
  -- CoD-like horde awareness: monsters know the current player's general
  -- position even behind walls, but attack visibility is checked NATIVELY.
  -- Only update a moving target occasionally; never compute A* in this layer.
  if not visible and entity.path and clock>=(brain.next_awareness_at or 0) then
   brain.next_awareness_at=clock+1.0
   local last=brain.last_awareness_goal
   if not last or sq(last,goal)>=9 then
    entity.path.last_seen_target_pos={x=goal.x,y=goal.y,z=goal.z}
    -- Release outdated VoxeLibre waypoint chain to current live destination.
    -- The built-in smart_mobs() chooses its own new path when LOS/stuck calls for it.
    entity.path.following=false
    entity.path.way=nil
    brain.last_awareness_goal={x=goal.x,y=goal.y,z=goal.z}
   end
   -- Do not give up on the player just because a wall hides them. Only
   -- the original native controller decides whether melee is possible.
   entity.target_time_lost=nil
  end
  -- Send movement, attack, jump, and pathfinding ownership back to the
  -- existing, tested VoxeLibre do_states_attack() and smart_mobs().
  return false
 end
 return A
end
