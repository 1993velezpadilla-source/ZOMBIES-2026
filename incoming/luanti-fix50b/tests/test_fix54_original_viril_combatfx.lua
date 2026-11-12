-- Same values as original config-old-3/scripts/patch_vril_combatfx.py.
-- White body hit, yellow headshot, 24 slots, 7 lanes, .62s lifetime.
local root='incoming/luanti-fix50b/games/voxelibre/mods/xz_zombies_classic/'
local clock=0
local elems={}
local player={}
function player:get_player_name()return 'tester' end
function player:hud_add(def)
 assert(def.position.x==0.5 and def.position.y==0.455)
 elems[#elems+1]={text=def.text,offset=def.offset,number=def.number}
 return #elems
end
function player:hud_change(id,kind,value)elems[id][kind]=value end
function player:hud_remove(id)elems[id].removed=true end
local M={
 get_us_time=function() return clock*1000000 end,
 get_player_by_name=function(n)if n=='tester' then return player end end
}
local fx=assert(loadfile(root..'v26_viril_combatfx.lua'))()(M)
assert(fx.hit(player,18,false),'White BODY hit must show number immediately')
assert(elems[1].text=='18' and elems[1].number==0xf5f5f5)
assert(elems[1].offset.x==-28 and elems[1].offset.y==-8)
clock=0.31;fx.step()
assert(elems[1].offset.y< -8,'Original Xziel C HUD moves damage text UP')
clock=0.36
assert(fx.hit(player,42,true),'Yellow HEADSHOT hit must show actual damage')
assert(elems[2].number==0xffd726,'Original gold headshot RGB 255,215,38')
clock=0.70;fx.step()
assert(elems[1].text=='' and elems[2].text=='42')
clock=1.0;fx.step()
assert(elems[2].text=='','Original hit numbers must expire after .62s')
-- Bounded buffer on long sessions: cannot allocate more than 24 HUD elements.
for i=1,80 do clock=clock+.025;assert(fx.hit(player,i,false))end
assert(#elems==24,'Original v26 C display uses exactly 24 reused damage slots')
fx.stop(player)
for _,e in ipairs(elems)do assert(e.text=='')end
fx.detach(player)
for _,e in ipairs(elems)do assert(e.removed)end
print('PASS: original Xziel Viril 24-slot white/yellow combat HUD, .62s upward cascade and no leaks')
