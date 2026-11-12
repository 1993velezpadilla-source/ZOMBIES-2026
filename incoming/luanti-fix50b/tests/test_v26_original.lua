-- Real NZ:P v26 QuakeC-derived rules, not a speculative Zombies scoring system.
local folder='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/'
local V=assert(loadfile(folder..'v26_rules.lua'))()
assert(V.max_planks==6 and V.repair_delay==0.75 and V.repair_points==10)
assert(V.barricade_frame(6)==0 and V.barricade_frame(5)==6)
assert(V.barricade_frame(4)==13 and V.barricade_frame(3)==20)
assert(V.barricade_frame(2)==27 and V.barricade_frame(1)==34)
assert(V.barricade_frame(0)==41)
assert(V.round_quota(1,1)==6 and V.round_quota(2,1)==8)
assert(V.round_quota(3,1)==13 and V.round_quota(4,1)==18)
assert(V.round_quota(1,2)==7 and V.round_quota(1,4)==10)
assert(V.zombie_hp(1)==150 and V.zombie_hp(10)==1050)
assert(math.floor(V.zombie_hp(11)+0.5)==1144)
assert(V.attack_damage==50 and V.attack_through_damage==60)
assert(V.attack_range_quake==64 and V.attack_trigger_range_quake==60)
assert(V.damage_score(false,'lowertorso')==10)
assert(V.damage_score(true,'lowertorso')==50)
assert(V.damage_score(true,'uppertorso')==60)
assert(V.damage_score(true,'headshot')==100)
assert(V.damage_score(true,'melee')==130)
assert(V.repair_cap(1)==50 and V.repair_cap(4)==200 and V.repair_cap(30)==500)
local st={planks=0,max=6}
local ok,reward=V.repair(st,1,1,0,false)
assert(ok and reward==10 and st.planks==1)
assert(V.repair(st,1.7,1,10,false)==false)
ok,reward=V.repair(st,1.75,1,50,true)
assert(ok and reward==0 and st.planks==2)
assert(V.damage_barrier(st) and st.planks==1)
assert(V.next_spawn_delay(2,1)>1.89 and V.next_spawn_delay(2,1)<1.91)
assert(V.next_spawn_delay(0.08,1)==0.08)
print('PASS original NZ:P 0.26 values: classic hit/kill points, 6 planks, round quotas/HP, cooldowns')

-- Run full v26 Luanti API translation with real node transitions and fake API.
local nodes={}
local world={}
local time=1
local points=500
local pmeta={}
local function poskey(pos)return ('%d,%d,%d'):format(pos.x,pos.y,pos.z)end
local function meta_for(pos)
 local key=poskey(pos)
 pmeta[key]=pmeta[key] or {}
 local t=pmeta[key]
 return {
  get_float=function(_,k)return t[k] or 0 end,set_float=function(_,k,v)t[k]=v end,
  get_int=function(_,k)return t[k] or 0 end,set_int=function(_,k,v)t[k]=v end,
  set_string=function(_,k,v)t[k]=v end,
 }
end
local player={hp=20,pos={x=2,y=0,z=0},score={}}
function player:get_player_name()return 'survivor' end
function player:is_player()return true end
function player:get_hp()return self.hp end
function player:set_hp(n)self.hp=n end
function player:get_pos()return self.pos end
function player:get_meta()
 return {get_int=function(_,k)return self.score[k] or 0 end,set_int=function(_,k,v)self.score[k]=v end}
end
function player:get_wielded_item()return {get_name=function()return 'ak47dev:ak47' end}end
local M={
 get_us_time=function()return time*1000000 end,
 get_connected_players=function()return {player} end,
 get_meta=meta_for,
 get_node=function(q)return world[poskey(q)] or {name='air'}end,
 get_node_or_nil=function(q)return world[poskey(q)] or {name='air'}end,
 swap_node=function(q,n)world[poskey(q)]=n end,
 register_node=function(name,def)assert(name:sub(1,1)==':');nodes[name:sub(2)]=def end,
 is_protected=function()return false end,
}
local active=true
local round=1
local A=assert(loadfile(folder..'v26_runtime.lua'))()(M,V,{
 active=function()return active end,
 get_round=function()return round end,
 add_points=function(_,n)points=points+n end,
})
local c=0;for _ in pairs(nodes)do c=c+1 end
assert(c==7,'Missing original seven plank states')
local full=nodes['xz_zombies:v26_barricade_6']
assert(full and full.drawtype=='mesh','Native v26 6-board node not registered')
assert(full.selection_box.fixed[1]<-1.4 and full.selection_box.fixed[4]>1.4,
 '3-node-wide original barricade selection not restored')
assert(full.selection_box.fixed[5]>2.5,'3-node-tall original barricade not selectable')
assert(full.collision_box.fixed[4]>1.4 and full.collision_box.fixed[5]>2.5,
 'Collision must extend over the full original window')
assert(not nodes['xz_zombies:v26_barricade_0'].walkable,
 'Fully broken barricade must let player/zombie walk through')
local spot={x=1,y=0,z=0}
world[poskey(spot)]={name=A.stage_name(6),param2=2}
assert(A.zombie_break(spot) and A.get_stage(spot)==5,'One zombie hit must break exactly one board')
assert(world[poskey(spot)].param2==2,'Preserve original placement orientation')
assert(A.repair(spot,player) and A.get_stage(spot)==6 and points==510,'USE must repair one board +10')
assert(not A.repair(spot,player),'Cannot repair an intact barricade')
for j=1,6 do assert(A.zombie_break(spot))end
assert(A.get_stage(spot)==0,'Zombies break each of the six original boards')
assert(not A.zombie_break(spot),'Empty barricade cannot lose imaginary boards')
for j=1,6 do time=time+0.75;assert(A.repair(spot,player))end
assert(A.get_stage(spot)==6,'Player rebuilds one board at a time')
assert(points==550,'Original round-1 repair score cap is 50 points')
time=time+1;round=2;A.reset_player_round(player,round)
assert(A.zombie_break(spot))
assert(A.repair(spot,player) and points==560,'Original points reset next round')
local zombie={hp=150,pos={x=0.5,y=0,z=0}}
function zombie:get_pos()return self.pos end
function zombie:get_hp()return self.hp end
function zombie:get_velocity()return {y=0}end
function zombie:set_velocity(v)self.vel=v end
local native_ai={state='stand',view_range=16}
function native_ai:do_attack(target)
 assert(self.force_attack==true,'Creative-world mob must force combat during PLAY')
 self.attack=target;self.state='attack'
 self.attack_calls=(self.attack_calls or 0)+1
end
function zombie:get_luaentity()return native_ai end
local record={obj=zombie}
time=10
A.zombie_think(record,0.3)
assert(native_ai.attack==player and native_ai.state=='attack',
 'Zombie must actually enter mcl_mobs native attack/chase state')
assert(native_ai.view_range>=45 and native_ai.attack_calls==1,
 'Mob AI must target player from original spawner range')
assert(zombie.vel==nil,'External velocity override would be reset by mcl_mobs:on_step')
assert(A.get_stage(spot)==5 and player:get_hp()==20,'Must break exactly one board before player damage')
time=10.2
A.zombie_think(record,0.3)
assert(native_ai.attack_calls==1,'Same target must not restart native pathfinding each tick')
assert(A.get_stage(spot)==5,'Original attack cooldown cannot break entire barricade')
time=12
A.zombie_think(record,0.3)
assert(A.get_stage(spot)==4,'Second rip removes only one board')
for j=1,4 do time=time+3;A.zombie_think(record,0.3) end
assert(A.get_stage(spot)==0,'Zombies eventually tear through original barrier')
time=time+3
A.zombie_think(record,0.3)
assert(player.hp==10,'Original 50 Quake zombie damage converted to 10/20 Luanti HP')
assert(not A.zombie_melee(record) and player.hp==10,
 'Native attack animation and globalstep cannot double-damage one frame')
A.zombie_on_punch(record,player,150,140)
assert(points==570,'Every nonlethal hit earns original +10')
A.zombie_on_punch(record,player,10,0)
assert(points==620 and record.v26_kill_awarded,'Original fatal bodyshot +50, no duplicate kill')
print('PASS v26 original model stages, USE, +10 repair cap, one-board zombie break, melee and per-hit credits')
