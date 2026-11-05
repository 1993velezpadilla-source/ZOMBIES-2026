-- Voxel Sandbox V3: self-contained first-person AK-style prototype.
-- Code and model geometry are original. Only runs in Create Map worlds.
-- NO TaCZ assets or Project Aether models/animations are included.
local world = Settings(minetest.get_worldpath() .. "/world.mt")
if world:get("xz_map_template") ~= "true" then return end

local AK = "ak47dev:ak47"
local CAPACITY = 30
local FIRE_PERIOD = 0.10      -- 600 rpm
local RELOAD_SECONDS = 2.75
local MAX_DISTANCE = 76
local S = {}

local function is_weapon(player)
    return player and player:is_player()
        and player:get_wielded_item():get_name() == AK
end

local function state(player)
    local name = player:get_player_name()
    if not S[name] then
        S[name] = {ammo=CAPACITY, reserve=210, next_fire=0, reload_end=0,
            ads=false, ent=nil, hud=nil, last_item=false}
    end
    return S[name]
end

local function hud_text(p, s)
    if not s.hud then return end
    local msg = ("AK-47 | %02d / %d | %s"):format(s.ammo, s.reserve,
        s.reload_end > 0 and "RELOADING" or (s.ads and "ADS" or "HIP"))
    p:hud_change(s.hud, "text", msg)
end

local function make_viewmodel(player, s)
    if s.ent and s.ent:is_valid() then return end
    local obj = minetest.add_entity(player:get_pos(), "ak47dev:fp_model")
    if not obj then return end
    -- 'Head' bone on a VoxeLibre player is rotated by camera pitch. Always
    -- render for owning player: normal attachments are hidden in first-person.
    obj:set_attach(player, "Head",
        {x=3.3, y=-3.9, z=5.5}, {x=0, y=0, z=0}, true)
    obj:set_animation({x=0, y=0.18}, 1, 0, true)
    s.ent = obj
end

local function show_model(player, s)
    if is_weapon(player) then
        make_viewmodel(player, s)
        if s.ent and s.ent:is_valid() then
            s.ent:set_properties({is_visible=true})
        end
    elseif s.ent and s.ent:is_valid() then
        s.ent:remove()
        s.ent=nil
    end
end

local function play(s, sound, player, gain)
    minetest.sound_play(sound, {to_player=player:get_player_name(),
        gain=gain or 1.0, pitch=1.0}, true)
end

local function animate(s, a, b)
    if s.ent and s.ent:is_valid() then
        s.ent:set_animation({x=a,y=b}, 1.0, 0.0, false)
    end
end

local function idle_after(player, s, delay)
    local name = player:get_player_name()
    minetest.after(delay, function()
        local p=minetest.get_player_by_name(name)
        local st=S[name]
        if p and st==s and st.reload_end<=0 and is_weapon(p) then
            animate(st, 0, 0.18)
        end
    end)
end

local function reload(player, s)
    local now=minetest.get_us_time()/1000000
    if s.reload_end>0 or s.ammo>=CAPACITY or s.reserve==0 then return end
    s.reload_end=now+RELOAD_SECONDS
    s.ads=false
    animate(s, 1.0, 3.75)
    -- These are timed mechanical Foley events, aligned to magazine drop,
    -- magazine insertion, then bolt release in the glTF keyframe timeline.
    play(s, "ak47dev_reload", player, 0.90)
    play(s, "ak47dev_magout", player, 0.26)
    local name=player:get_player_name()
    minetest.after(1.20,function()
        if S[name]==s and minetest.get_player_by_name(name)
            and s.reload_end>0 then
            play(s,"ak47dev_magin",player,0.24)
        end
    end)
    minetest.after(2.20,function()
        if S[name]==s and minetest.get_player_by_name(name)
            and s.reload_end>0 then
            play(s,"ak47dev_bolt",player,0.22)
        end
    end)
    hud_text(player,s)
end

local function trace_shot(player)
    local eye=player:get_pos()
    eye.y=eye.y+(player:get_properties().eye_height or 1.47)
    local dir=player:get_look_dir()
    local dest=vector.add(eye,vector.multiply(dir,MAX_DISTANCE))
    for pt in minetest.raycast(eye,dest,true,false) do
        if pt.type=="object" and pt.ref and pt.ref~=player
            and pt.ref:is_valid() then
            pt.ref:punch(player, 1.0, {
                full_punch_interval=0.1,
                damage_groups={fleshy=6},
            },dir)
            return
        elseif pt.type=="node" then
            return -- stop at a block; never destroy terrain during testing
        end
    end
end

local function fire(player, s)
    local now=minetest.get_us_time()/1000000
    if s.reload_end>0 or now<s.next_fire then return end
    if s.ammo==0 then
        play(s,"ak47dev_dry",player,0.6)
        reload(player,s)
        return
    end
    s.next_fire=now+FIRE_PERIOD
    s.ammo=s.ammo-1
    animate(s,0.4,0.82)
    play(s,"ak47dev_fire",player,0.70)
    trace_shot(player)
    hud_text(player,s)
    idle_after(player,s,0.13)
end

local function set_ads(player,s,enabled)
    if s.reload_end>0 then return end
    s.ads=enabled
    if s.ent and s.ent:is_valid() then
        -- Aim down sights: the rifle's receiver is aligned under the reticle.
        -- No double-hand 'steering wheel' animation.
        local offset=enabled and {x=0,y=-2.9,z=5.0}
            or {x=3.3,y=-3.9,z=5.5}
        s.ent:set_attach(player,"Head",offset,{x=0,y=0,z=0},true)
    end
    -- ADS narrows field of view, restores cleanly when releasing the gun.
    if enabled then
        player:set_fov(0.80, true, 0.15)
    else
        player:set_fov(0, false, 0.15)
    end
    hud_text(player,s)
end

minetest.register_entity("ak47dev:fp_model",{
    initial_properties={
        visual="mesh",
        mesh="ak47dev_animated.glb",
        textures={"ak47dev_metal.png","ak47dev_black.png",
            "ak47dev_wood.png","ak47dev_skin.png"},
        visual_size={x=1,y=1,z=1},
        physical=false,
        collide_with_objects=false,
        pointable=false,
        static_save=false,
        is_visible=true,
        glow=1,
    },
})

minetest.register_tool(AK,{
    description="AK-47 Prototype | Tap fire | Tap place ADS | Sneak+fire reload",
    inventory_image="ak47dev_icon.png",
    wield_image="ak47dev_blank.png",
    range=0,
    groups={weapon=1,weapon_ranged=1},
    on_use=function(stack,player)
        if not player then return stack end
        local s=state(player)
        if player:get_player_control().sneak then reload(player,s)
        else fire(player,s) end
        return stack
    end,
    on_secondary_use=function(stack,player)
        if player then
            local s=state(player)
            set_ads(player,s,not s.ads)
        end
        return stack
    end,
    on_place=function(stack,player)
        if player then
            local s=state(player)
            set_ads(player,s,not s.ads)
        end
        return stack
    end,
})

minetest.register_chatcommand("akreload",{
    description="Reload the AK-47 prototype",
    func=function(name)
        local player=minetest.get_player_by_name(name)
        if player and is_weapon(player) then
            reload(player,state(player))
            return true,"AK-47 reload started"
        end
        return false,"Equip AK-47 first"
    end
})

minetest.register_on_joinplayer(function(player)
    local name=player:get_player_name()
    local s=state(player)
    s.hud=player:hud_add({
        hud_elem_type="text",position={x=0.5,y=0.94},
        alignment={x=0,y=0},scale={x=1,y=1},
        number=0xF3D496,text="AK-47",style=1,z_index=150,
    })
    minetest.after(1,function()
        local p=minetest.get_player_by_name(name)
        if not p then return end
        local meta=p:get_meta()
        if meta:get_int("ak47dev_given")==0 then
            local inv=p:get_inventory()
            if inv:room_for_item("main", AK) then
                inv:add_item("main",AK)
                meta:set_int("ak47dev_given",1)
                minetest.chat_send_player(name,
                  "AK-47 added to inventory. Shoot: tap fire | ADS: tap place | Reload: sneak+fire")
            end
        end
        hud_text(p,state(p))
    end)
end)
minetest.register_on_leaveplayer(function(p)
    local name=p:get_player_name()
    local s=S[name]
    if s and s.ent and s.ent:is_valid() then s.ent:remove() end
    S[name]=nil
end)

local tick=0
minetest.register_globalstep(function(dt)
    tick=tick+dt
    if tick<0.05 then return end
    tick=0
    local now=minetest.get_us_time()/1000000
    for _,p in ipairs(minetest.get_connected_players()) do
        local s=state(p)
        local equipped=is_weapon(p)
        show_model(p,s)
        if equipped then
            if s.reload_end>0 and now>=s.reload_end then
                local need=math.min(CAPACITY-s.ammo,s.reserve)
                s.ammo=s.ammo+need
                s.reserve=s.reserve-need
                s.reload_end=0
                animate(s,0,0.18)
                hud_text(p,s)
            end
            local controls=p:get_player_control()
            if controls.sneak and controls.dig then
                reload(p,s)
            elseif controls.dig then
                fire(p,s)
            end
            if controls.zoom and not s.ads then
                set_ads(p,s,true)
            end
        elseif s.ads then
            set_ads(p,s,false)
        end
    end
end)

minetest.log("action","[ak47dev] Original AK prototype enabled only for private Create Map worlds")
