-- FIX52B: authentic VoxeLibre play state and COD hit-float regression tests.
local root='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/'
local modes={}
local players={}
local us=0
local game={
 get_us_time=function()return us end,
 get_gametime=function()return math.floor(us/1000000) end,
 get_player_by_name=function(name)return players[name] end,
 is_creative_enabled=function(name)return (modes[name] or 'creative')=='creative' end,
}
_G.mcl_gamemode={
 get_gamemode=function(p)return modes[p:get_player_name()] or 'creative' end,
 set_gamemode=function(p,x)assert(x=='creative' or x=='survival');modes[p:get_player_name()]=x end
}
local draws={}
local p={}
function p:get_player_name()return 'survivor' end
function p:hud_add(def)
 assert(def.position.y>=0.60,'HUD text must not overlap pause/debug chat at top')
 local id=#draws+1
 draws[id]={def=def,text=def.text or '',position=def.position,color=def.number}
 return id
end
function p:hud_change(id,attr,value)
 assert(draws[id],'Unknown HUD ID')
 if attr=='text' then draws[id].text=value
 elseif attr=='position' then draws[id].position=value
 elseif attr=='number' then draws[id].color=value end
end
function p:hud_remove(id) draws[id].removed=true end
players.survivor=p
local G=assert(loadfile(root..'v26_modes.lua'))()(game)
assert(G.join(p,false) and modes.survivor=='creative')
assert(G.play(p) and modes.survivor=='survival' and not game.is_creative_enabled('survivor'))
assert(G.stop(p) and modes.survivor=='creative' and game.is_creative_enabled('survivor'))
assert(G.join(p,true) and modes.survivor=='survival')
local H=assert(loadfile(root..'v26_hud.lua'))()(game)
H.attach(p)
assert(#draws==3,'Expected only 3 primary HUD elements')
H.mode(p,true)
H.points(p,500)
H.wave(p,1,6,true)
assert(draws[1].text=='RONDA 01' and draws[2].text=='6 RESTANTES')
assert(draws[3].text=='500')
H.award(p,10)
H.points(p,510)
assert(#draws==4,'First hit should allocate one visual reward slot')
assert(draws[4].text=='+10','Hit must generate +10')
local original=draws[4].position.y
us=300000
H.step(0.3)
assert(draws[4].position.y<original,'Hit score must cascade upward')
H.award(p,50)
H.points(p,560)
assert(draws[3].text=='560','Score should update with kill points')
local found=false
for _,x in ipairs(draws)do if x.text=='+50' then found=true end end
assert(found,'Kill must generate +50')
us=1700000
H.step(1.4)
for _,x in ipairs(draws) do if x.text:sub(1,1)=='+' then error('Expired floating score still visible')end end
H.mode(p,false)
assert(draws[1].text=='' and draws[2].text=='' and draws[3].text=='','STOP must hide gameplay HUD')
H.detach(p)
for _,x in ipairs(draws) do assert(x.removed,'HUD ID leaked after leave')end
print('PASS: VoxeLibre survival/creative; compact bottom HUD; +10 and +50 rising cascades; cleanup')
