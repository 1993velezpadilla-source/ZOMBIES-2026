-- FIX53 mobile multi-cell NZ:P v26 window + native VoxeLibre AI regression.
-- This uses ACTUAL v26_runtime + v26_sized_barricades, not a mock barricade.
local ROOT='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/'
local V=assert(loadfile(ROOT..'v26_rules.lua'))()
local world,metadata,registered,sounds={},{},{},{}
local time=0
local earned=0
local active=true
local round=1
local function key(p)return ('%d,%d,%d'):format(p.x,p.y,p.z)end
local function pos(x,y,z)return{x=x,y=y,z=z}end
local function node(p)return world[key(p)] or {name='air',param2=0}end
local function meta(p)
 local k=key(p)
 if not metadata[k] then metadata[k]={} end
 local fields=metadata[k]
 return {
  get_int=function(_,k)return fields[k] or 0 end,
  set_int=function(_,k,v)fields[k]=v end,
  get_string=function(_,k)return fields[k] or '' end,
  set_string=function(_,k,v)fields[k]=v end,
  get_float=function(_,k)return fields[k] or 0 end,
  set_float=function(_,k,v)fields[k]=v end
 }
end
local M={}
M.registered_nodes=registered
M.register_node=function(name,def)assert(name:sub(1,1)==':'); registered[name:sub(2)]=def end
M.get_node_or_nil=node
M.get_node=node
M.get_meta=meta
M.set_node=function(p,n)
 local old=node(p)
 if old.name~='air' then error('set_node would replace existing map block '..old.name)end
 world[key(p)]=n
 if registered[n.name] and registered[n.name].on_construct then
  registered[n.name].on_construct(p)
 end
end
M.swap_node=function(p,n)
 assert(world[key(p)],'swap_node without placed node')
 world[key(p)]=n
end
M.remove_node=function(p)
 local old=node(p)
 if registered[old.name] and registered[old.name].on_destruct then
  registered[old.name].on_destruct(p)
 end
 world[key(p)]={name='air',param2=0}
end
M.dir_to_facedir=function()return 0 end
M.is_creative_enabled=function()return true end
M.is_protected=function()return false end
M.chat_send_player=function()end
M.sound_play=function(name) sounds[#sounds+1]=name end
M.get_us_time=function()return time*1000000 end
M.get_gametime=function()return math.floor(time) end
local player={hp=20,position=pos(0,0,8),score={}}
function player:get_player_name()return 'tester' end
function player:is_player()return true end
function player:get_hp()return self.hp end
function player:set_hp(v)self.hp=v end
function player:get_pos()return self.position end
function player:get_look_dir()return pos(0,0,1)end
function player:get_meta()
 return {get_int=function(_,k)return self.score[k] or 0 end,set_int=function(_,k,v)self.score[k]=v end}
end
function player:get_wielded_item()return {get_name=function()return 'ak47dev:ak47' end}end
M.get_connected_players=function()return {player} end
local A=assert(loadfile(ROOT..'v26_runtime.lua'))()(M,V,{
 active=function()return active end,
 get_round=function()return round end,
 add_points=function(_,n)earned=earned+n end
})
A=assert(loadfile(ROOT..'v26_sized_barricades.lua'))()(M,A)
local choices={'1x1','1x2','2x1','2x2','3x3'}
local expected_w={1,1,2,2,3}
local expected_h={1,2,1,2,3}
local function stage_nodes(w,h,n)
 if w==1 and h==1 then return 'xz_zombies:v26_barricade_'..n end
 return ('xz_zombies:v26_barricade_%d_%dx%d'):format(n,w,h)
end
local count=0;for _ in pairs(registered)do count=count+1 end
assert(count==37, 'Expected 7 original + 28 size variants + 2 companion cells, got '..count)
for i,choice in ipairs(choices) do
 local w,h=expected_w[i],expected_h[i]
 local origin=pos(10*i,0,0)
 local yes
 if choice=='1x1' then
  world[key(origin)]={name=stage_nodes(w,h,6),param2=0}
  registered[stage_nodes(w,h,6)].on_construct(origin)
  yes=true
 else
  yes=A.place_sized(origin,w,h,player)
 end
 assert(yes,'Failed placement '..choice)
 assert(A.get_stage(origin)==6)
 local parts=0
 for y=0,h-1 do for x=0,w-1 do
  if x~=0 or y~=0 then
   local q=pos(origin.x+x,y,origin.z)
   local n=node(q)
   assert(n.name=='xz_zombies:v26_barricade_part_solid','missing linked solid '..key(q))
   assert(A.get_stage(q)==6,'linked part must resolve to master')
   parts=parts+1
  end
 end end
 assert(parts==w*h-1)
 -- Original v26 QuakeC: one hit destroys only ONE of six planks in ALL sizes.
 for stage=5,0,-1 do
  time=time+2
  assert(A.zombie_break(origin),'failed original plank rip')
  assert(node(origin).name==stage_nodes(w,h,stage),'Incorrect stage '..choice)
  assert(A.get_stage(origin)==stage)
  for y=0,h-1 do for x=0,w-1 do
   if x~=0 or y~=0 then
    local n=node(pos(origin.x+x,y,origin.z))
    assert(n.name==(stage>0 and 'xz_zombies:v26_barricade_part_solid'
                               or 'xz_zombies:v26_barricade_part_open'),
       'Linked cells did not change collision with the master')
   end
  end end
 end
 assert(A.zombie_break(origin)==false,'Cannot damage empty original window')
 round=round+1
 A.reset_player_round(player,round)
 -- Repair through a linked cell is the same as rightclick on the anchor.
 local handle=h>1 and pos(origin.x,origin.y+1,origin.z) or
   w>1 and pos(origin.x+1,origin.y,origin.z) or origin
 for stage=1,6 do
  time=time+0.75
  assert(A.repair(handle,player),('Failed v26 one-plank USE %s:%d'):format(choice,stage))
  assert(A.get_stage(origin)==stage,'Repair did not restore original frame')
 end
 assert(A.get_stage(handle)==6,'part metadata must still resolve')
 if choice~='1x1' then
  local before=0
  for y=0,h-1 do for x=0,w-1 do
   local q=pos(origin.x+x,y,origin.z)
   if x~=0 or y~=0 then
    local n=node(q)
    assert(n.name=='xz_zombies:v26_barricade_part_solid')
    before=before+1
   end
  end end
  assert(before==w*h-1)
  M.remove_node(origin)
  for y=0,h-1 do for x=0,w-1 do
   assert(node(pos(origin.x+x,y,origin.z)).name=='air','Orphaned companion after dig')
  end end
 end
end
assert(#sounds>=60,'Original v26 repair/rip sounds were not triggered')
-- Validate atomic placement of occupied openings, not accidental map edits.
world[key(pos(51,1,0))]={name='mcl_core:stone'}
local ok=A.place_sized(pos(50,0,0),3,3,player)
assert(not ok,'Placement must refuse blocking walls')
assert(node(pos(50,0,0)).name=='air','Partial/corrupt large barricade placement')
world[key(pos(51,1,0))]=nil

-- Native mcl_mobs:do_attack() must own movement; NO competing raw velocity.
local mob={pos=pos(0,0,0),hp=150,velocity_writes=0}
local entity={state='stand',view_range=16,walk_velocity=.8,run_velocity=1.8}
function mob:get_luaentity()return entity end
function mob:get_pos()return self.pos end
function mob:get_hp()return self.hp end
function mob:set_velocity(v)self.velocity_writes=self.velocity_writes+1 end
function mob:get_velocity()return {x=0,y=0,z=0}end
function entity:do_attack(target)self.attack=target;self.state='attack';self.attack_calls=(self.attack_calls or 0)+1 end
function entity:set_velocity(speed)self.stopped=(self.stopped or 0)+1 end
local record={obj=mob}
assert(A.install_native_ai(record),'Must hook real mcl_mobs API instance')
assert(entity.force_attack and entity.type=='monster' and entity.damage==10)
assert(entity.view_range>=45,'Zombies must acquire player beyond vanilla 16-block range')
A.zombie_think(record,.25)
assert(entity.attack==player and entity.state=='attack' and entity.attack_calls==1,
 'Native VoxeLibre attack/pathfinding must receive player target')
assert(mob.velocity_writes==0,'Raw velocity competes with native mob do_states')
local barrier=pos(0,0,1)
assert(A.place_sized(barrier,2,2,player))
time=time+2
A.zombie_think(record,.25)
assert(A.get_stage(barrier)==5,'Native zombie must rip original plank once')
assert(entity:do_custom(.25)==false,'Native chase cannot skip intact barricades')
time=time+2
A.zombie_think(record,.25)
assert(A.get_stage(barrier)==4,'Second hit removes second plank only')
for i=1,4 do time=time+2;A.zombie_think(record,.25)end
assert(A.get_stage(barrier)==0,'Zombie must open barricade before pursuing')
entity.state='stand'
time=time+2
A.zombie_think(record,.25)
assert(entity.attack==player and entity.state=='attack',
 'Native chase must resume immediately when six boards are down')
assert(entity:do_custom(.25)~=false,'Native do_states must run once window is cleared')
print('PASS: five true block-size v26 barricades, atomic placement, 6 board stages, repair and native mob chase')
