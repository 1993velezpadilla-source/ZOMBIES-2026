-- FIX52B VoxeLibre gameplay modes.
-- Uses the ORIGINAL VoxeLibre API (not global creative_mode settings).
-- Core source: mods/PLAYER/mcl_gamemode/init.lua, set_gamemode/get_gamemode.
return function(M)
 local A={}
 local function api()
  local g=rawget(_G,'mcl_gamemode')
  if g and type(g.set_gamemode)=='function' and type(g.get_gamemode)=='function' then return g end
  return nil
 end
 function A.play(player)
  local g=api()
  if not g then return false,'VoxeLibre mcl_gamemode API no disponible' end
  local name=player:get_player_name()
  local previous=g.get_gamemode(player)
  if previous~='survival' then g.set_gamemode(player,'survival') end
  if g.get_gamemode(player)~='survival' or (M.is_creative_enabled and M.is_creative_enabled(name)) then
   return false,'VoxeLibre no cambio a supervivencia'
  end
  return true
 end
 function A.stop(player)
  local g=api()
  if not g then return false,'VoxeLibre mcl_gamemode API no disponible' end
  if g.get_gamemode(player)~='creative' then g.set_gamemode(player,'creative') end
  return g.get_gamemode(player)=='creative'
 end
 function A.join(player,is_playing)
  if is_playing then return A.play(player) end
  return A.stop(player)
 end
 return A
end
