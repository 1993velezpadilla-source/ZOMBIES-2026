-- Smoke gate: real generated geometry and explicit creative nodes.
local path=assert(arg[1],"Expected mod directory")..'/'
local manifest=assert(loadfile(path..'polyhaven_fort_manifest.lua'))()
assert(#manifest>0 and #manifest<=64,'invalid CC0 architecture count')
local names={}
local stub={
 register_node=function(name,def)
  assert(not names[name],'duplicate node '..name)
  assert(def.drawtype=='mesh' and def.paramtype2=='facedir')
  assert(def.tiles[1]=='xz_fort_atlas.png')
  assert(def.walkable and def.selection_box and def.collision_box)
  assert(def.groups.building_block==1)
  names[name]=true
 end,
 log=function() end,
}
local count=assert(loadfile(path..'polyhaven_fort.lua'))()(stub,path:sub(1,-2))
assert(count==#manifest,'registered geometry mismatch')
for _,entry in ipairs(manifest) do
 local handle=assert(io.open(path..'models/'..entry.mesh,'rb'))
 assert(handle:read(2)=='# ','OBJ source header missing')
 handle:close()
 assert(names['xz_zombies:'..entry.id])
end
assert(io.open(path..'textures/xz_fort_atlas.png','rb'))
print('PASS: '..count..' Poly Haven meshes are placeable, textured, collision-enabled Lua nodes')
