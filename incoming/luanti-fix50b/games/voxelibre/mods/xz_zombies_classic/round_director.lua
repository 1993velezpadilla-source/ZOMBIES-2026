-- FIX51 Round Director: pure, deterministic Zombies Classic wave rules.
-- Kept separate from native weapons so weapon animations, ADS and assets are unchanged.
local D = {}

local function bounded_integer(value, low, high)
  local n=math.floor(tonumber(value) or low)
  return math.max(low, math.min(high, n))
end

function D.player_count(players)
  return bounded_integer(players, 1, 4)
end

function D.quota(round, players)
  local r=bounded_integer(round, 1, 999)
  local extra=D.player_count(players)-1
  -- Solo begins at 8 enemies. Co-op scales without unbounded Android entity loads.
  return math.min(96, 5 + r*3 + extra*(2+math.floor(r/2)))
end

function D.alive_cap(players)
  -- Keep 10-12 native mobs alive simultaneously for mobile memory/FPS.
  return math.min(12, 8 + D.player_count(players)*2)
end

function D.spawn_interval(round)
  local r=bounded_integer(round, 1, 999)
  return math.max(0.90, 3.0 - 0.11*(r-1))
end

function D.health(round)
  local r=bounded_integer(round, 1, 999)
  return math.min(900, math.floor(20 + r*4 + r*r*0.45))
end

function D.remaining(quota, spawned, alive)
  local q=bounded_integer(quota, 0, 10000)
  local s=bounded_integer(spawned, 0, 10000)
  local a=bounded_integer(alive, 0, 10000)
  return math.max(0, q-s+a)
end

function D.hud(round, quota, spawned, alive, points, active)
  local pts=bounded_integer(points, 0, 100000000)
  if not active then return ('ZOMBIES  READY  |  %d PTS'):format(pts) end
  if round<=0 then return ('ZOMBIES  PREPARE  |  %d PTS'):format(pts) end
  return ('ZOMBIES  R%02d  |  %d LEFT  |  %d PTS'):format(
    round, D.remaining(quota,spawned,alive),pts)
end

return D
