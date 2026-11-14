-- FIX58 CC0 Poly Haven Modular Fort 01 architecture.
-- Placeable 3D mesh nodes, NOT cubic terrain; never touches combat/AI/rounds.
return function(M, modpath)
 local manifest_path=modpath..'/polyhaven_fort_manifest.lua'
 local handle=io.open(manifest_path,'rb')
 if not handle then
  M.log('action','[XZ Fort] Art package not installed; skipping architecture registration')
  return 0
 end
 handle:close()
 local entries=assert(loadfile(manifest_path))()
 local count=0
 for _,entry in ipairs(entries) do
  local model=modpath..'/models/'..entry.mesh
  local exists=io.open(model,'rb')
  if not exists then
   M.log('warning','[XZ Fort] Missing geometry: '..tostring(entry.mesh))
  else
   exists:close()
   local bounds=entry.box or {-.48,-.48,-.48,.48,.48,.48}
   local fixed={
    math.max(-.49,math.min(.49,bounds[1])),
    math.max(-.49,math.min(.49,bounds[2])),
    math.max(-.49,math.min(.49,bounds[3])),
    math.max(-.49,math.min(.49,bounds[4])),
    math.max(-.49,math.min(.49,bounds[5])),
    math.max(-.49,math.min(.49,bounds[6])),
   }
   for axis=1,3 do
    if fixed[axis+3]-fixed[axis]<.10 then
      local mid=(fixed[axis+3]+fixed[axis])*.5
      fixed[axis]=math.max(-.49,mid-.05)
      fixed[axis+3]=math.min(.49,mid+.05)
    end
   end
   M.register_node(':xz_zombies:'..entry.id,{
    description=entry.label,
    drawtype='mesh',
    mesh=entry.mesh,
    tiles={'xz_fort_atlas.png'},
    paramtype='light',
    paramtype2='facedir',
    sunlight_propagates=false,
    walkable=true,
    pointable=true,
    is_ground_content=false,
    buildable_to=false,
    groups={pickaxey=2,cracky=2,building_block=1,stone=1},
    selection_box={type='fixed',fixed=fixed},
    collision_box={type='fixed',fixed=fixed},
    _doc_items_longdesc='CC0 Poly Haven Modular Fort 01 architecture. Independent rotatable mesh for Zombies map building.',
   })
   count=count+1
  end
 end
 M.log('action','[XZ Fort] Loaded '..count..' CC0 3D architecture modules')
 return count
end
