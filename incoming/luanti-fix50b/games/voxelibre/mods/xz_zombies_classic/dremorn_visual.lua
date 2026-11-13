-- FIX57: optional visual-only model swap for a legally obtained Dremorn asset.
-- NO third-party model/texture is shipped with the public repository.
-- Enabled only when BOTH generated asset files exist in this mod's media dirs.
-- Requires Luanti 5.17+ named glTF animation track interface.
return function(M, modpath)
 local A={enabled=false, model='xz_dremorn_zombie.glb', texture='xz_dremorn_body.png'}
 local function contains(directory,name)
  if type(M.get_dir_list)~='function' then return false end
  local ok,list=pcall(M.get_dir_list,directory,false)
  if not ok or type(list)~='table' then return false end
  for _,candidate in ipairs(list) do if candidate==name then return true end end
  return false
 end
 A.enabled=contains(modpath..'/models',A.model)
       and contains(modpath..'/textures',A.texture)
 local tracks={
  stand={track='idle1',speed=1.0,loop=true},
  walk ={track='walk',speed=1.0,loop=true},
  run  ={track='run',speed=1.0,loop=true},
  punch={track='atack1',speed=1.0,loop=false},
  punch2={track='atack2',speed=1.0,loop=false},
  die={track='death1',speed=1.0,loop=false},
 }
 function A.apply(entity,obj)
  if not A.enabled or not entity or not obj
   or type(obj.play_animation)~='function'
   or type(obj.stop_animation)~='function'
   or type(obj.set_properties)~='function' then return false end
  -- Original target registration and collision hitboxes remain VoxeLibre native.
  -- Dremorn glb MUST be exported to Luanti scale (10 mesh units = 1 node).
  local old_mesh=entity.mesh
  local old_texture=entity.textures
  local ok=pcall(obj.set_properties,obj,{mesh=A.model,textures={A.texture}})
  if not ok then return false end
  entity._dremorn_original_mesh=old_mesh
  entity._dremorn_original_textures=old_texture
  entity.head_swivel=nil -- Native zombie's bone 'head.control' is absent in FBX.
  local original=entity.set_animation
  entity._dremorn_animation=nil
  entity.set_animation=function(self,name,fixed_frame)
   local desc=tracks[name]
   if not desc then
    if original then return original(self,name,fixed_frame) end
    return
   end
   if self._dremorn_animation==name then return end
   if self._dremorn_animation then
    local prev=tracks[self._dremorn_animation]
    if prev then pcall(obj.stop_animation,obj,prev.track) end
   end
   self._dremorn_animation=name
   self._current_animation=name
   local played=pcall(obj.play_animation,obj,desc.track,{
    speed=desc.speed,loop=desc.loop,blend=0.1
   })
   if not played and original then
    self._dremorn_animation=nil
    return original(self,name,fixed_frame)
   end
  end
  entity:set_animation('stand')
  return true
 end
 return A
end
