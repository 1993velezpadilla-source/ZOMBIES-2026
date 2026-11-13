-- FIX57: optional Dremorn visualization for Zombies Classic round mobs only.
-- No third-party asset is stored in the repo. Requires legitimate Dremorn GLB + PNG.
-- Luanti 5.17+/5.18 named glTF ObjectRef animations (real engine API).
return function(M, modpath)
 local A={enabled=false,model='xz_dremorn_zombie.glb',texture='xz_dremorn_body.png'}
 local function contains(dir,name)
  if type(M.get_dir_list)~='function' then return false end
  local ok,files=pcall(M.get_dir_list,dir,false)
  if not ok or type(files)~='table' then return false end
  for _,file in ipairs(files) do if file==name then return true end end
  return false
 end
 A.enabled=contains(modpath..'/models',A.model)
   and contains(modpath..'/textures',A.texture)
 -- Animation names as published by Dremorn on CGTrader. Actual exported GLB
 -- MUST pass validation (Blender action names can change during FBX import).
 local tracks={
  stand={track='idle1',speed=1,loop=true},
  walk={track='walk',speed=1,loop=true},
  run={track='run',speed=1,loop=true},
  punch={track='atack1',speed=1,loop=false},
  punch2={track='atack2',speed=1,loop=false},
  die={track='death1',speed=1,loop=false},
 }
 A.track_names={}
 for state,def in pairs(tracks) do A.track_names[state]=def.track end
 function A.apply(entity,obj)
  if not A.enabled or not entity or not obj
    or type(obj.play_animation)~='function'
    or type(obj.stop_animation)~='function'
    or type(obj.set_properties)~='function'
    or type(entity.set_animation)~='function' then return false end
  -- Do not alter any other mcl_mobs registrations or zombie instances.
  local old_set_animation=entity.set_animation
  local old_set_animation_speed=entity.set_animation_speed
  local old_head=entity.head_swivel
  local old_properties=type(obj.get_properties)=='function'
    and obj:get_properties() or {}
  local previous_mesh=old_properties and old_properties.mesh
  local previous_textures=old_properties and old_properties.textures
  local ok,result=pcall(obj.set_properties,obj,{mesh=A.model,textures={A.texture}})
  if not ok or result==false then return false end
  -- VoxeLibre looks up die_start/die_end to schedule corpse removal. A GLB
  -- clip alone would not trigger its native on_death code. This per-instance
  -- copy preserves every other zombie's default animation definition.
  local anim={}
  for k,v in pairs(entity.animation or {}) do anim[k]=v end
  -- Pending original Dremorn GLB verification: 1.6s is provisional.
  anim.die_start=0
  anim.die_end=1.6
  anim.die_speed=1
  entity.animation=anim
  entity.head_swivel=nil -- Original bone head.control does not exist in FBX.
  entity._dremorn_original_mesh=previous_mesh
  entity._dremorn_original_textures=previous_textures
  local last_played=nil
  local last_speed=nil
  local function play(state)
   local d=tracks[state] or tracks.stand
   if last_played==d.track and entity._current_animation==state then return true end
   if last_played then pcall(obj.stop_animation,obj,last_played) end
   local worked,played=pcall(obj.play_animation,obj,d.track,
       {speed=d.speed,loop=d.loop,blend=0.10})
   if not worked or played==false then return false end
   last_played=d.track
   last_speed=d.speed
   entity._current_animation=state
   entity._dremorn_animation=state
   return true
  end
  -- Override ONLY this entity's wrapper, retaining native combat and physics.
  entity.set_animation=function(self,state)
   if self.state=='die' and state~='die' and state~='stand' then return end
   if not play(state) and M.log then
    M.log('warning','[FIX57] Dremorn track error ('..tostring(state)..')')
   end
  end
  -- Critical: native VoxeLibre effects.lua:set_animation_speed() calls the
  -- legacy set_animation_frame_speed() each tick (track 1). That is not
  -- a safe way to drive named glTF tracks. Instead update their named track.
  entity.set_animation_speed=function(self)
   if not last_played or type(obj.update_animation)~='function'
    or type(obj.get_velocity)~='function' then return end
   local state=self._dremorn_animation
   local d=tracks[state]
   if not d or (state~='walk' and state~='run') then return end
   local v=obj:get_velocity()
   if not v then return end
   local horizontal=math.sqrt((v.x or 0)^2+(v.z or 0)^2)
   local nominal=state=='run' and (self.run_velocity or 1.8)
                       or (self.walk_velocity or 0.8)
   local desired=math.max(0.65,math.min(1.6,horizontal/math.max(.2,nominal)))
   if math.abs(desired-(last_speed or 1))<0.2 then return end
   local updated,value=pcall(obj.update_animation,obj,last_played,{speed=desired})
   if updated and value~=false then last_speed=desired end
  end
  if not play('stand') then
   -- Fully restore original object and per-instance methods on initial fail.
   if previous_mesh then pcall(obj.set_properties,obj,{mesh=previous_mesh,
     textures=previous_textures}) end
   entity.set_animation=old_set_animation
   entity.set_animation_speed=old_set_animation_speed
   entity.head_swivel=old_head
   entity._dremorn_animation=nil
   return false
  end
  return true
 end
 return A
end
