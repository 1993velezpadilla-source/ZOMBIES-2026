-- FIX56: Actual VoxeLibre live combat owns navigation; no fixed trail.
local path='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/rotu_ai.lua'
local clock=0
local P={}
local function make(name,x)
 local p={name=name,pos={x=x,y=0,z=0},hp=20}
 function p:get_hp()return self.hp end
 function p:get_pos()return self.pos end
 function p:get_player_name()return self.name end
 return p
end
local blind=make('blind-near',2)
local visible=make('visible-far',11)
P[1],P[2]=blind,visible
local isvisible=true
local M={
 get_us_time=function()return clock*1000000 end,
 get_connected_players=function()return P end,
 line_of_sight=function(a,b) return isvisible and b.x>5 end
}
local rotu=assert(loadfile(path))()(M)
local record={obj={}}
function record.obj:get_pos()return {x=0,y=0,z=0} end
local selected,d=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==visible and d==11,'Original RotU must choose visible living target')
clock=1;visible.hp=0
selected=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==blind,'Original RotU must not chase dead player')
clock=2;visible.hp=20
selected=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==visible)
local legacy_gopath_calls=0
local entity={state='stand',reach=1.875,walk_velocity=.8,run_velocity=1.8,
 path={last_seen_target_pos={x=11,y=0,z=0},following=false}}
function entity:gopath()legacy_gopath_calls=legacy_gopath_calls+1 end
assert(rotu.think(record,entity,visible,11,0.25,3)==false)
assert(record.rotu_ai.status=='STALKING')
assert(entity.pathfinding==1 and entity.run_velocity>1.8)
assert(legacy_gopath_calls==0,'Never trigger static gopath trail')
-- LOST LOS: the actual native mob AI continues combat and receives updated goal.
clock=3.1;isvisible=false;visible.pos.x=18
entity.path.following=true
entity.path.way={{x=11,y=0,z=0}}
assert(rotu.think(record,entity,visible,18,0.25,3)==false)
assert(record.rotu_ai.status=='REACQUIRE_TARGET')
assert(entity.path.last_seen_target_pos.x==18,'Current player position, not breadcrumb')
assert(entity.path.following==false and entity.path.way==nil,'Outdated native route released')
assert(entity.target_time_lost==nil)
assert(legacy_gopath_calls==0,'No static gopath allowed')
-- Tiny movements must not recalculate path or cause thrashing.
clock=4.2;visible.pos.x=19
entity.path.following=true
entity.path.way={{x=18,y=0,z=0}}
rotu.think(record,entity,visible,19,0.25,3)
assert(entity.path.following==true and entity.path.way,
 'Less than 3 blocks goal drift must retain native path to avoid mobile A* storm')
-- More than 3 blocks away: abandon old route and let native smart_mobs recalc.
clock=5.4;visible.pos.x=25
rotu.think(record,entity,visible,25,0.25,3)
assert(entity.path.following==false and entity.path.way==nil)
assert(entity.path.last_seen_target_pos.x==25)
-- Compatibility: FIX55 existing gowp route cannot lock into former location.
entity.state='gowp';entity.waypoints={{pos={x=11,y=0,z=0}}}
entity.current_target={pos={x=11,y=0,z=0}}
entity._target={x=11,y=0,z=0}
entity.callback_arrived=function()error('stale callback must be removed') end
clock=6.4
rotu.think(record,entity,visible,25,0.25,3)
assert(entity.state=='stand' and entity.waypoints==nil and entity._target==nil
  and entity.current_target==nil and entity.callback_arrived==nil,
 'FIX55 fixed waypoint chain must be cleared before native do_attack')
-- On recovered LOS, use original per-step native combat to immediately turn.
clock=7.4;isvisible=true
rotu.think(record,entity,visible,7,0.25,3)
assert(record.rotu_ai.status=='PURSUING')
rotu.barrier(record)
assert(record.rotu_ai.status=='BARRICADE')
clock=8.5;blind.hp=0;visible.hp=0
selected=rotu.acquire(record,entity,record.obj:get_pos())
assert(selected==nil and record.rotu_ai.status=='SEARCHING')
print('PASS FIX56: live goal, no pencil trail, native A*, bounded invalidation, old-path cancellation, targets and barricades')
