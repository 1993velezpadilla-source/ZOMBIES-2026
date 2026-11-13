-- FIX55 isolated original RotU targeting/path recovery test; no fake zombie engine.
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
function record.obj:get_pos()return {x=0,y=0,z=0}end
local selected,d=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==visible and d==11,'Original RotU bestTarget must choose closest visible living player')
assert(record.rotu_ai.target==visible)
clock=1;visible.hp=0
selected,d=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==blind,'RotU must reject dead player')
assert(record.rotu_ai.status=='SEARCHING' or record.rotu_ai.target==blind)
visible.hp=20
clock=2;isvisible=true
selected=rotu.acquire(record,{},record.obj:get_pos())
assert(selected==visible)
local entity={state='stand',reach=1.875,walk_velocity=.8,run_velocity=1.8,pathfinding=1}
local routecalls=0
function entity:gopath(pos,callback)
 routecalls=routecalls+1
 self.path={x=pos.x,y=pos.y,z=pos.z}
 self.callback=callback
 self.state='gowp'
 return true
end
function entity:do_attack(player)
 self.target=player
 self.state='attack'
end
assert(rotu.think(record,entity,visible,11,0.25,3)==false)
assert(record.rotu_ai.status=='STALKING','Original RotU state must be stalking from far')
assert(entity.run_velocity>1.8 and entity.pathfinding==1)
assert(routecalls==0,'Do not run expensive path when unobstructed')
clock=3.6;isvisible=false
assert(rotu.think(record,entity,visible,11,0.25,3)==true,'Lost-sight recovery must ask native pathfinder')
assert(record.rotu_ai.status=='REACQUIRE_TARGET')
assert(routecalls==1 and entity.path.x==11)
assert(rotu.think(record,entity,visible,11,0.25,3)==true and routecalls==1,
 'Do not reset native gopath movement at 4 Hz')
entity.callback(entity)
assert(entity.state=='attack' and entity.target==visible,
 'Native route callback must resume VoxeLibre dogfight')
clock=4.0
rotu.think(record,entity,visible,11,0.25,3)
assert(routecalls==1,'Mobile pathfinder must be rate-limited')
clock=5.0
rotu.barrier(record)
assert(record.rotu_ai.status=='BARRICADE' and record.rotu_ai.stuck_for==0)
-- If all candidates are dead the state returns to SEARCHING.
clock=6.0;blind.hp=0;visible.hp=0
selected=rotu.acquire(record,entity,record.obj:get_pos())
assert(selected==nil and record.rotu_ai.status=='SEARCHING')
print('PASS MIT RotU targeting, visibility priority, pursuit states, native pathfinding recovery, cooldown, barricade and no target')
