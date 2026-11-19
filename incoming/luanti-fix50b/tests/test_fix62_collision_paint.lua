-- Real node-based physical collision test, no native engine mocked physics.
-- Regression: open gate, solid walls, stairs, brush/eraser/bucket, persistence.
local mod=assert(arg[1],'pass source mod directory')
local M
local nodes,entitydefs,world,metas,objects={}, {}, {}, {}, {}
local operations=0
local function key(p)return p.x..','..p.y..','..p.z end
local function count(predicate)
 local n=0
 for k,v in pairs(world) do if predicate(k,v) then n=n+1 end end
 return n
end
M={
 registered_nodes=nodes,
 register_node=function(name,def)nodes[name:sub(2)]=def end,
 register_entity=function(name,def)entitydefs[name:sub(2)]=def end,
 get_node_or_nil=function(p) return world[key(p)] or {name='air'} end,
 get_meta=function(p)
  local k=key(p)
  metas[k]=metas[k] or {}
  return {
   get_string=function(_,name)return metas[k][name] or '' end,
   set_string=function(_,name,value)metas[k][name]=value end
  }
 end,
 set_node=function(p,n)
  operations=operations+1
  local k=key(p)
  world[k]={name=n.name}
  metas[k]={}
 end,
 get_us_time=function()return 9000 end,
 log=function()end,
}
function M.add_entity(p,name)
 local obj={at={x=p.x,y=p.y,z=p.z},name=name}
 function obj:get_pos()return self.at end
 function obj:remove()self.at=nil end
 objects[#objects+1]=obj
 return obj
end
local entries={
 {id='arch',label='castle gate',box={-.15,-.48,-.48,.15,.48,.48}},
 {id='stairs',label='stone stairway',box={-.48,-.48,-.25,.48,.48,.25}},
 {id='wall',label='thick stone wall',box={-.25,-.48,-.48,.25,.48,.48}}
}
local api=assert(loadfile(mod..'/fort_collision_paint.lua'))()(M,entries)
assert(type(api.paint)=='function' and type(api.update)=='function')
for i=1,8 do
 local d=assert(nodes['xz_zombies_classic:collision_paint_'..i])
 assert(d.drawtype=='airlike' and d.walkable==true)
 assert(d.pointable==false and d.diggable==false)
 assert(d.collision_box and d.collision_box.type=='fixed')
 assert(math.abs(d.collision_box.fixed[5] - (-.5+i/8))<1e-8)
end
local function obj(pos)
 local o={at=pos,properties={}}
 function o:get_pos()return self.at end
 function o:set_properties(p) for k,v in pairs(p) do self.properties[k]=v end end
 return o
end
local arch={object=obj({x=30,y=16,z=30}),scale=12,rotation={x=0,y=0,z=0}}
local gate=entries[1]
local n=api.update(arch,gate,arch.scale,arch.rotation,'auto')
assert(n>0 and n<2401,'open gate generated too few/many collision nodes')
assert(arch.object.properties.physical==false,'huge architecture owner must not block door')
local count_before=count(function(_,v) return v.name:match('^xz_zombies_classic:collision_paint_') end)
assert(count_before==n)
assert(M.get_node_or_nil({x=30,y=16,z=30}).name=='air','arch doorway center should be empty')
local pillar={x=30,y=16,z=35}
assert(M.get_node_or_nil(pillar).name~='air','gate sides must be solid physical nodes')
local old_op=operations
local rep=api.update(arch,gate,arch.scale,arch.rotation,'auto')
assert(rep==n)
assert(operations==old_op,'no-op paint redraw must not rebuild all collision blocks')
local amount=api.paint(arch,gate,'auto',{x=30,y=16,z=30},'brush',0)
assert(amount>=1)
assert(M.get_node_or_nil({x=30,y=16,z=30}).name~='air','paint adds real physical collision')
assert(operations-old_op<10,'brush changed many unnecessary map nodes')
local amount2=api.paint(arch,gate,'auto',{x=30,y=16,z=30},'erase',0)
assert(amount2>=0)
assert(M.get_node_or_nil({x=30,y=16,z=30}).name=='air','eraser must clear manually painted collision')
assert(M.get_node_or_nil(pillar).name~='air','erasing doorway must not remove wall supports')
-- Node belongs to the selected object only: never replace or remove terrain.
world[key({x=32,y=16,z=30})]={name='mcl_core:stone'}
api.paint(arch,gate,'auto',{x=32,y=16,z=30},'brush',0)
assert(M.get_node_or_nil({x=32,y=16,z=30}).name=='mcl_core:stone','stone was overwritten by collision painting')
-- Painting moves with object; only own nodes are removed.
local old_pos={x=30,y=16,z=35}
arch.object.at={x=50,y=16,z=50}
api.update(arch,gate,arch.scale,arch.rotation,'auto')
assert(M.get_node_or_nil(old_pos).name=='air','moving 3D architecture left invisible collision behind')
assert(M.get_node_or_nil({x=50,y=16,z=55}).name~='air','moved architecture has no physical walls')
-- Stair collision surfaces use physically walkable fractional node boxes,
-- not a single giant entity AABB the avatar clips through.
local stair={object=obj({x=-30,y=12,z=10}),scale=12,rotation={x=0,y=0,z=0}}
local st=api.update(stair,entries[2],12,stair.rotation,'auto')
assert(st>0)
assert(stair.object.properties.physical==false)
local heights={}
for _,p in ipairs(stair._paint_nodes) do
 local node=M.get_node_or_nil(p)
 local level=tonumber(node.name:match('collision_paint_(%d+)'))
 assert(level and level>=1 and level<=8)
 heights[p.x]=math.max(heights[p.x] or -999,p.y-.5+level/8)
end
local xs={}
for x in pairs(heights) do xs[#xs+1]=x end
table.sort(xs)
assert(#xs>=4,'stairs need multiple stepped surfaces')
assert(heights[xs[#xs]]>heights[xs[1]],'stairs were flat, no rise')
-- "Sin colision" deletes physics map entirely.
api.update(stair,entries[2],12,stair.rotation,'none')
assert(#stair._paint_nodes==0,'collision none has hidden blockers left behind')
-- Bucket: only a *closed* drawn ring may be filled. Never flood open world.
local empty={object=obj({x=0,y=0,z=0}),scale=1,rotation={x=0,y=0,z=0}}
for _,at in ipairs({{x=-1,y=0,z=0},{x=1,y=0,z=0},{x=0,y=0,z=-1},{x=0,y=0,z=1}}) do
 api.paint(empty,entries[3],'paint',at,'brush',0)
end
assert(M.get_node_or_nil({x=0,y=0,z=0}).name=='air')
local filled,result=api.paint(empty,entries[3],'paint',{x=0,y=0,z=0},'bucket',0,'xz')
assert(result=='filled' and filled==1,'bucket failed to fill the 4-neighbor enclosed area')
assert(M.get_node_or_nil({x=0,y=0,z=0}).name~='air')
api.clear(empty)
assert(#empty._paint_nodes==0)
assert(M.get_node_or_nil({x=0,y=0,z=0}).name=='air')
local orphan=api.paint(empty,entries[3],'paint',{x=0,y=0,z=0},'bucket',0,'xz')
assert(orphan==0,'open region bucket must refuse flooding')
print('PASS FIX62: walkable invisible native node slabs, arch opening, solid side posts, staircase physics, brush/erase/closed bucket, protected terrain, transform/cleanup and incremental updates')
