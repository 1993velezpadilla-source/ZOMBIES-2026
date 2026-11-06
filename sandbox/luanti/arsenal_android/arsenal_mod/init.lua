-- Original Luanti Arsenal private source-render test (not a shipped Zombies game).
-- Register only guns whose actual gun+hands GLB files were verified in CI.
-- Original WeaponDef data gates all damage/ammo; no made-up magazine stats.
-- Classic Zombies deliberately has NO user Gunsmith attachments.
local path = minetest.get_modpath("arsenal")
local input = io.open(path .. "/arsenal_runtime.json", "rb")
if not input then error("[arsenal] missing private generated asset manifest") end
local manifest_raw = input:read("*a")
input:close()
local manifest = minetest.parse_json(manifest_raw)
if type(manifest) ~= "table" or manifest.schema_version ~= 1 or
    type(manifest.weapons) ~= "table" then
    error("[arsenal] unsupported real-asset source manifest")
end

local defs = {}
local players = {}
local function timestamp() return minetest.get_us_time() / 1000000 end
-- Only the AK has source-verified sound effects pre-baked by the separate
-- AK HD pipeline. Never assign the AK fire/reload sounds to other firearms.
local AK_SOUND={
    fire="ak47dev_fire",
    dry="ak47dev_dry",
    reload_normal="ak47dev_reload_normal",
    reload_empty="ak47dev_reload_empty"
}
local function source_audio(p,def,event)
    if def.id~="ak47" then return end
    local effect=AK_SOUND[event]
    if effect then
        minetest.sound_play(effect,{to_player=p:get_player_name(),gain=.75},true)
    end
end
local function state(player)
    local username = player:get_player_name()
    if not players[username] then
        players[username] = {
            weapon = "", seq = 0, last_action = "", next_fire = 0,
            reload_end = 0, reloading = false, ads = false,
            dig = false, aux = false, burst = 0, hud = nil
        }
    end
    return players[username]
end
local function valid_player(p) return p and p:is_player() end
local function is_weapon(stack)
    return stack and defs[stack:get_name()]
end
local function initialize(stack, def)
    local meta = stack:get_meta()
    if meta:get_string("ar_init") == "1" then return stack end
    meta:set_string("ar_init", "1")
    meta:set_int("ar_clip", def.gameplay_logic_enabled and def.magazine_capacity or 0)
    meta:set_int("ar_reserve", def.gameplay_logic_enabled and
        math.max(0, def.reserve_max - def.magazine_capacity) or 0)
    return stack
end
local function ammo(stack, def)
    initialize(stack, def)
    local meta=stack:get_meta()
    local clip=math.max(0,meta:get_int("ar_clip"))
    local reserve=math.max(0,meta:get_int("ar_reserve"))
    return clip,reserve
end
local function status(p, def, stack, s)
    if not s.hud then return end
    local label
    if def.gameplay_logic_enabled then
        local mag, reserve = ammo(stack,def)
        label=("%s | %d / %d | %s"):format(def.name,mag,reserve,
            s.reloading and "RELOAD" or s.ads and "ADS" or "HIP")
    else
        label=def.name.." | SOURCE MODEL PREVIEW ONLY"
    end
    p:hud_change(s.hud, "text", label)
end
local function send(p,stack,def,s,event)
    -- Initialize the actual ItemStack BEFORE set_wielded_item copies it into
    -- the inventory. Doing so in status() AFTER the copy lost all ammo data.
    initialize(stack,def)
    local meta=stack:get_meta()
    if event then
        s.seq=s.seq+1
        meta:set_string("xz_ar_anim",event..tostring(s.seq))
    end
    meta:set_string("xz_ar_ads",s.ads and "1" or "0")
    meta:set_string("xz_ar_empty",s.empty and "1" or "0")
    meta:set_string("xz_ar_fired",tostring(s.fired or 0))
    p:set_wielded_item(stack)
    status(p,def,stack,s)
    return stack
end
local function change(p, def, stack, s)
    if s.weapon == def.id then return end
    s.weapon=def.id
    s.last_action=""
    s.ads=false
    s.reloading=false
    s.reload_end=0
    s.empty=false
    s.next_fire=0
    s.burst=0
    p:set_fov(0,false,.18)
    send(p,stack,def,s,"E")
end
local function ads(p,def,stack,s)
    if s.reloading then return stack end
    s.ads=not s.ads
    -- The local first-person renderer performs model ADS animation.
    -- 0.80 is a preview-only camera FOV, NOT calibrated iron sights.
    p:set_fov(s.ads and .80 or 0,s.ads,.22)
    return send(p,stack,def,s)
end
local function start_reload(p,def,stack,s)
    if not def.gameplay_logic_enabled or s.reloading then return stack end
    local mag,reserve=ammo(stack,def)
    if mag>=def.magazine_capacity or reserve==0 then return stack end
    if mag==0 and not def.distinct_empty_reload_animation then
        -- Do not fake an empty-mag reload with the normal animation.
        return stack
    end
    s.reloading=true
    s.empty=(mag==0)
    s.ads=false
    s.burst=0
    s.reload_end=timestamp()+
        (s.empty and def.reload_empty_seconds or def.reload_seconds)
    p:set_fov(0,false,.2)
    source_audio(p,def,s.empty and "reload_empty" or "reload_normal")
    return send(p,stack,def,s,"R")
end
local function hit(p,def)
    local eye=vector.add(p:get_pos(),
        {x=0,y=p:get_properties().eye_height or 1.47,z=0})
    local direction=p:get_look_dir()
    local finish=vector.add(eye,vector.multiply(direction,76))
    for target in minetest.raycast(eye,finish,true,false) do
        if target.type=="node" then break end
        if target.type=="object" and target.ref~=p and target.ref and
                target.ref:is_valid() then
            target.ref:punch(p,1,{
                full_punch_interval=def.fire_interval_seconds,
                damage_groups={fleshy=def.damage}},direction)
            break
        end
    end
end
local function shoot(p,def,stack,s)
    local t=timestamp()
    if s.reloading or t<s.next_fire then return stack end
    if not def.gameplay_logic_enabled then
        -- Preview event only: NEVER deal damage with a guessed WeaponDef.
        s.next_fire=t+.3
        return send(p,stack,def,s,"F")
    end
    local mag,reserve=ammo(stack,def)
    if mag==0 then
        -- No repeated spamming or fake dryfire audio.
        s.next_fire=t+.25
        source_audio(p,def,"dry")
        return stack
    end
    local meta=stack:get_meta()
    meta:set_int("ar_clip",mag-1)
    s.next_fire=t+def.fire_interval_seconds
    s.fired=(s.fired or 0)+1
    send(p,stack,def,s,"F")
    source_audio(p,def,"fire")
    hit(p,def)
    return stack
end
local function reload_completed(p,def,stack,s)
    if not s.reloading or timestamp()<s.reload_end then return stack end
    local mag,reserve=ammo(stack,def)
    local fill=math.min(def.magazine_capacity-mag,reserve)
    stack:get_meta():set_int("ar_clip",mag+fill)
    stack:get_meta():set_int("ar_reserve",reserve-fill)
    s.reloading=false
    s.reload_end=0
    return send(p,stack,def,s)
end

-- Crate refills inventory stacks, not just the currently held AK-47.
-- Preserve per-stack metadata for save/reload and when switching guns.
local function refill_all(p)
    if not valid_player(p) then return false end
    local inv=p:get_inventory()
    local changed=false
    for i=1,inv:get_size("main") do
        local item=inv:get_stack("main",i)
        local d=is_weapon(item)
        if d and d.gameplay_logic_enabled then
            initialize(item,d)
            item:get_meta():set_int("ar_clip",d.magazine_capacity)
            item:get_meta():set_int("ar_reserve",
                                   math.max(0,d.reserve_max-d.magazine_capacity))
            inv:set_stack("main",i,item)
            changed=true
        end
    end
    local s=state(p)
    if changed then
        s.reloading=false
        s.reload_end=0
        local current=p:get_wielded_item()
        local d=is_weapon(current)
        if d then send(p,current,d,s) end
    end
    return changed
end
local crate_timestamps={}
minetest.register_node("arsenal:ammo_box",{
    description="Arsenal universal ammo box (private test)",
    tiles={"arsenal_flat_metal.png"},
    groups={choppy=2,oddly_breakable_by_hand=2},
    on_rightclick=function(_,_,player,itemstack)
        if valid_player(player) then
            local who=player:get_player_name()
            if timestamp()>=(crate_timestamps[who] or 0) then
                crate_timestamps[who]=timestamp()+.4
                refill_all(player)
            end
        end
        return itemstack
    end,
    on_punch=function(_,_,player) if valid_player(player) then refill_all(player) end end,
})

for _,def in ipairs(manifest.weapons) do
    if type(def.id)=="string" and def.id:match("^[a-z0-9_]+$") and
        type(def.gun_model)=="string" and
        type(def.hands_model)=="string" then
        local gun=io.open(path.."/models/"..def.gun_model,"rb")
        local hands=io.open(path.."/models/"..def.hands_model,"rb")
        if gun and hands then
            gun:close();hands:close()
            defs["arsenal:"..def.id]=def
            minetest.register_tool("arsenal:"..def.id,{
                description=def.name..(def.gameplay_logic_enabled
                    and " | Original COD4 mechanics (private)" or " | Animated source preview"),
                inventory_image="arsenal_flat_metal.png",
                wield_image="arsenal_flat_metal.png",
                stack_max=1,range=0,
                groups={weapon=1,weapon_ranged=1},
                on_use=function(_,p)
                    if not valid_player(p) then return nil end
                    local stack=p:get_wielded_item()
                    local s=state(p)
                    change(p,def,stack,s)
                    if def.fire_mode=="burst" and def.gameplay_logic_enabled then
                        if s.burst==0 then s.burst=3 end
                    end
                    if def.fire_mode=="burst" and s.burst>0 then
                        s.burst=s.burst-1
                    end
                    return shoot(p,def,stack,s)
                end,
                on_place=function(_,p)
                    if not valid_player(p) then return nil end
                    local stack=p:get_wielded_item()
                    local s=state(p)
                    change(p,def,stack,s)
                    return ads(p,def,stack,s)
                end,
                on_secondary_use=function(_,p)
                    if not valid_player(p) then return nil end
                    local stack=p:get_wielded_item()
                    local s=state(p)
                    change(p,def,stack,s)
                    return ads(p,def,stack,s)
                end,
            })
        else
            if gun then gun:close() end
            if hands then hands:close() end
            minetest.log("error","[arsenal] absent real GLB, refusing tool "..def.id)
        end
    end
end

minetest.register_chatcommand("arsenal",{
    params="[weapon_id]",
    description="Private Arsenal: list or give a source-verified test weapon",
    func=function(who,param)
        local player=minetest.get_player_by_name(who)
        if not player then return false,"Player missing" end
        if not param or param=="" then
            local all={}
            for item in pairs(defs) do all[#all+1]=item:sub(9) end
            table.sort(all)
            return true,"Available REAL source previews: "..table.concat(all,", ")
        end
        if not param:match("^[a-z0-9_]+$") or not defs["arsenal:"..param] then
            return false,"Weapon GLB source not verified in this build"
        end
        local inv=player:get_inventory()
        local item="arsenal:"..param
        if not inv:contains_item("main",item) then
            inv:add_item("main",item.." 1")
        end
        return true,"Private Arsenal source test weapon added: "..param
    end
})
minetest.register_chatcommand("arsenalammo",{
    func=function(who)
        local player=minetest.get_player_by_name(who)
        if not player then return false,"Player missing" end
        if not player:get_inventory():contains_item("main","arsenal:ammo_box") then
            player:get_inventory():add_item("main","arsenal:ammo_box 1")
        end
        return true,"Universal ammo box added"
    end
})
minetest.register_on_joinplayer(function(player)
    local s=state(player)
    s.hud=player:hud_add({
        hud_elem_type="text",position={x=.5,y=.91},
        alignment={x=0,y=0},number=0xDDD7CD,
        text="Arsenal experimental source viewmodels",z_index=150})
end)
minetest.register_on_leaveplayer(function(player)
    local who=player:get_player_name()
    players[who]=nil
    crate_timestamps[who]=nil
end)
minetest.register_globalstep(function(_)
    for _,player in ipairs(minetest.get_connected_players()) do
        local stack=player:get_wielded_item()
        local def=is_weapon(stack)
        local s=state(player)
        if def then
            change(player,def,stack,s)
            if s.reloading then reload_completed(player,def,stack,s) end
            local c=player:get_player_control()
            if c.aux1 and not s.aux then
                start_reload(player,def,player:get_wielded_item(),s)
            end
            if c.dig then
                if def.fire_mode=="auto" then
                    shoot(player,def,player:get_wielded_item(),s)
                elseif def.fire_mode=="burst" and s.burst>0 then
                    s.burst=s.burst-1
                    shoot(player,def,player:get_wielded_item(),s)
                elseif not s.dig then
                    shoot(player,def,player:get_wielded_item(),s)
                end
            end
            s.dig=c.dig
            s.aux=c.aux1
        else
            if s.ads then player:set_fov(0,false,.18) end
            s.weapon=""
            s.reloading=false
            s.reload_end=0
            s.ads=false
            s.dig=false
            s.aux=false
            s.burst=0
        end
    end
end)
minetest.log("action","[arsenal] real source preview mod loaded; no custom attachments in Classic Zombies")
