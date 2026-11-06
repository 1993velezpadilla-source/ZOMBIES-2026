-- Private AK47 HD playtest. Geometry and animation are supplied at build time.
local AK="ak47dev:ak47"
local S={}
local CAPACITY=30
local function now() return minetest.get_us_time()/1000000 end
local function equipped(p) return p and p:is_player() and p:get_wielded_item():get_name()==AK end
local function state(p)
    local name=p:get_player_name()
    if not S[name] then S[name]={ammo=30,reserve=210,ads=false,seq=0,fired=0,next_fire=0,reload_end=0,pending=0,aux=false} end
    return S[name]
end
local function sync(p,s,event)
    if not equipped(p) then return end
    local stack=p:get_wielded_item();local meta=stack:get_meta()
    if event then s.seq=s.seq+1;meta:set_string("xz_ak_anim",event..s.seq) end
    meta:set_string("xz_ak_ads",s.ads and "1" or "0")
    meta:set_string("xz_ak_empty",s.empty_reload and "1" or "0")
    meta:set_string("xz_ak_fired",tostring(s.fired))
    p:set_wielded_item(stack)
    if s.hud then
        p:hud_change(s.hud,"text",("AK47 HD | %02d / %d | %s"):format(s.ammo,s.reserve,
            s.reload_end>0 and "RECARGANDO" or s.pending>0 and "BAJANDO MIRA" or s.ads and "ADS" or "HIP FIRE"))
    end
end
local function sound(p,name,gain) minetest.sound_play(name,{to_player=p:get_player_name(),gain=gain or .7},true) end
local function ads(p,s,on)
    if s.reload_end>0 or s.pending>0 then return end
    s.ads=on;sync(p,s)
    p:set_fov(on and .80 or 0,on,.25)
end
local function start_reload(p,s)
    s.pending=0;s.empty_reload=s.ammo==0
    s.reload_end=now()+(s.empty_reload and 106/30 or 83/30)
    s.ads=false;p:set_fov(0,false,.25);sync(p,s,"R")
    sound(p,"ak47dev_reload",.8)
end
local function reload(p,s)
    if s.reload_end>0 or s.pending>0 or s.ammo>=CAPACITY or s.reserve<=0 then return end
    if s.ads then
        s.ads=false;s.pending=now()+.25;p:set_fov(0,false,.25);sync(p,s)
    else start_reload(p,s) end
end
local function fire(p,s)
    local time=now()
    if s.reload_end>0 or s.pending>0 or time<s.next_fire then return end
    if s.ammo==0 then sound(p,"ak47dev_dry",.5);reload(p,s);return end
    s.next_fire=time+.10;s.ammo=s.ammo-1;s.fired=s.fired+1;sync(p,s,"F");sound(p,"ak47dev_fire",.65)
    local eye=vector.add(p:get_pos(),{x=0,y=p:get_properties().eye_height or 1.47,z=0})
    local direction=p:get_look_dir();local stop=vector.add(eye,vector.multiply(direction,76))
    for hit in minetest.raycast(eye,stop,true,false) do
        if hit.type=="node" then break end
        if hit.type=="object" and hit.ref~=p and hit.ref and hit.ref:is_valid() then
            hit.ref:punch(p,1,{full_punch_interval=.1,damage_groups={fleshy=6}},direction);break
        end
    end
end
local function toggle_ads(p)
    if not equipped(p) then return end
    local s=state(p);if now()<(s.toggle_after or 0) then return end
    s.toggle_after=now()+.18;ads(p,s,not s.ads)
end
minetest.register_tool(AK,{
    description="AK47 HD | FIRE: disparar | ADS: apuntar | R: recargar",
    inventory_image="ak47dev_icon.png",wield_image="ak47dev_icon.png",
    wield_scale={x=1,y=1,z=1},stack_max=1,range=0,
    groups={weapon=1,weapon_ranged=1,not_in_creative_inventory=1},
    on_use=function(stack,p)
        if equipped(p) then
            local s=state(p)
            if p:get_player_control().sneak then reload(p,s) else fire(p,s) end
        end
        return p and p:get_wielded_item() or stack
    end,
    on_secondary_use=function(stack,p) toggle_ads(p);return p and p:get_wielded_item() or stack end,
    on_place=function(stack,p) toggle_ads(p);return p and p:get_wielded_item() or stack end,
})
minetest.register_on_joinplayer(function(p)
    local s=state(p);local name=p:get_player_name()
    s.hud=p:hud_add({hud_elem_type="text",position={x=.5,y=.92},alignment={x=0,y=0},
        number=0xEEE4CE,text="AK47 HD",style=1,z_index=150})
    minetest.after(1,function()
        local player=minetest.get_player_by_name(name);if not player then return end
        local inv=player:get_inventory()
        if not inv:contains_item("main",AK) then inv:add_item("main",AK) end
        for i=1,inv:get_size("main") do
            local weapon=inv:get_stack("main",i)
            if weapon:get_name()==AK then
                -- Luanti exposes get_wield_index(), but no server-side setter.
                -- Move the weapon into the selected slot and preserve its item.
                local selected=player:get_wield_index()
                if i~=selected then
                    local previous=inv:get_stack("main",selected)
                    inv:set_stack("main",selected,weapon)
                    inv:set_stack("main",i,previous)
                end
                break
            end
        end
        sync(player,state(player),"E")
        minetest.chat_send_player(name,"FIRE: disparar | ADS: apuntar | R: recargar")
    end)
end)
minetest.register_on_leaveplayer(function(p) S[p:get_player_name()]=nil end)
minetest.register_chatcommand("akreload",{func=function(name)
    local p=minetest.get_player_by_name(name)
    if not equipped(p) then return false,"Equipa la AK47" end
    reload(p,state(p));return true,"Recarga"
end})
minetest.register_globalstep(function(dt)
    local time=now()
    for _,p in ipairs(minetest.get_connected_players()) do
        local s=state(p)
        if equipped(p) then
            if s.pending>0 and time>=s.pending then start_reload(p,s) end
            if s.reload_end>0 and time>=s.reload_end then
                local n=math.min(CAPACITY-s.ammo,s.reserve)
                s.ammo=s.ammo+n;s.reserve=s.reserve-n;s.reload_end=0;sync(p,s)
            end
            local c=p:get_player_control()
            if c.aux1 and not s.aux then reload(p,s) end
            s.aux=c.aux1
            if c.sneak and c.dig then reload(p,s) elseif c.dig then fire(p,s) end
        else
            if s.ads then s.ads=false;p:set_fov(0,false,.25) end
            s.pending=0;s.reload_end=0;s.aux=false
        end
    end
end)
minetest.log("action","[ak47hd] private HD model controls loaded")
