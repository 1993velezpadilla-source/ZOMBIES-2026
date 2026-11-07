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
    local variant=p:get_wielded_item():get_meta():get_string("xz_ar_variant")
    if event=="fire" and variant:find("silencer",1,true) then
        -- No spoofing original loud AK Foley as a suppressed shot.
        return
    end
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
            dig = false, aux = false, burst = 0, burst_guard = false, hud = nil, last_weapon = ""
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
    local variant=stack:get_meta():get_string("xz_ar_variant")
    if variant~="" then label=label.." ["..variant.."]" end
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
    s.last_weapon=def.id
    s.last_action=""
    s.ads=false
    s.reloading=false
    s.reload_end=0
    s.empty=false
    s.next_fire=0
    s.burst=0
    s.burst_guard=false
    p:set_fov(0,false,.18)
    send(p,stack,def,s,"E")
end
local function ads(p,def,stack,s)
    if s.reloading then return stack end
    s.ads=not s.ads
    -- The local first-person renderer performs model ADS animation.
    -- 0.80 is a preview-only camera FOV, NOT calibrated iron sights.
    local variant=stack:get_meta():get_string("xz_ar_variant")
    local scale=variant:find("acog",1,true) and .52 or
        variant:find("reflex",1,true) and .76 or .80
    p:set_fov(s.ads and scale or 0,s.ads,.22)
    return send(p,stack,def,s)
end
local function start_reload(p,def,stack,s)
    if not def.gameplay_logic_enabled or s.reloading then return stack end
    local mag,reserve=ammo(stack,def)
    if mag>=def.magazine_capacity or reserve==0 then return stack end
    -- Fallback to the ORIGINAL normal-mag animation when the empty
    -- XANIM is absent. Preserve the original empty reload clock, so M9
    -- and M1911 are usable rather than dead preview guns.
    -- C++ will choose the only original reload clip available.
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
                inventory_image="arsenal_icon_"..def.id..".png",
                wield_image="arsenal_icon_"..def.id..".png",
                stack_max=1,range=0,
                groups={weapon=1,weapon_ranged=1},
                on_use=function(_,p)
                    if not valid_player(p) then return nil end
                    local stack=p:get_wielded_item()
                    local s=state(p)
                    change(p,def,stack,s)
                    if def.fire_mode=="burst" and def.gameplay_logic_enabled then
                        -- A trigger edge initiates exactly one three-round burst.
                        -- Never consume pending shots until a round actually fires.
                        if s.burst_guard or s.burst>0 then return stack end
                        s.burst_guard=true
                        local mag=ammo(stack,def)
                        if mag==0 then return shoot(p,def,stack,s) end
                        s.burst=3
                        local fired=s.fired or 0
                        stack=shoot(p,def,stack,s)
                        if (s.fired or 0)>fired then s.burst=s.burst-1 end
                        return stack
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

-- Android test/PvP attachment selector. Classic Zombies map will omit it.
local attachments=dofile(path.."/attachments.lua").register(defs,state)
-- Mobile-first Arsenal test picker; no custom Gunsmith in Classic Zombies.
-- Only actually present, source-verified GLB pairs become selectable.
local categories={
    {key="assault",label="Assault"},
    {key="smg",label="SMG"},
    {key="shotgun",label="Shotgun"},
    {key="sniper",label="Sniper"},
    {key="marksman",label="Marksman"},
    {key="lmg",label="LMG"},
    {key="pistol",label="Pistol"}
}
local active_category={}
local function visible_weapons(category)
    local found={}
    for key,def in pairs(defs) do
        if def.category==category then
            found[#found+1]={id=def.id,name=def.name,
                playable=def.gameplay_logic_enabled}
        end
    end
    table.sort(found,function(a,b) return a.name<b.name end)
    return found
end
local function display_picker(player,requested)
    if not valid_player(player) then return end
    local who=player:get_player_name()
    local cat=requested or active_category[who] or "assault"
    local valid=false
    for _,c in ipairs(categories) do if c.key==cat then valid=true end end
    if not valid then cat="assault" end
    active_category[who]=cat
    local esc=minetest.formspec_escape
    local ui={
        "formspec_version[4]",
        "size[15,10.5]",
        "bgcolor[#0D1019;true]",
        "label[.45,.35;COD4 ARSENAL  |  PRIVATE SOURCE PREVIEW]",
        "label[.45,.9;Select an original model. Preview-only = no invented weapon stats.]"
    }
    for i,c in ipairs(categories) do
        local x=.45+(i-1)*2.05
        ui[#ui+1]=("button[%.2f,1.45;1.94,.68;cat_%s;%s]"):format(
            x,c.key,esc(c.label))
    end
    local list=visible_weapons(cat)
    if #list==0 then
        ui[#ui+1]="label[.7,3;No verified source model available in this category.]"
    end
    for i,item in ipairs(list) do
        local col=(i-1)%3
        local row=math.floor((i-1)/3)
        if row<5 then
            local x=.5+col*4.85
            local y=2.45+row*1.36
            ui[#ui+1]=("button[%.2f,%.2f;4.62,1.1;weapon_%s;%s]"):format(
                x,y,item.id,esc(item.name)..(item.playable and " | SOURCE STATS" or " | PREVIEW"))
        end
    end
    ui[#ui+1]="button_exit[10.6,9.65;3.8,.65;exit;Close]"
    minetest.show_formspec(who,"arsenal:picker",table.concat(ui))
end
local function grant_weapon(player,id)
    local def=defs["arsenal:"..id]
    if not def or not valid_player(player) then return false end
    local inv=player:get_inventory()
    if not inv:contains_item("main","arsenal:"..id) then
        local left=inv:add_item("main","arsenal:"..id.." 1")
        if not left:is_empty() then
            minetest.chat_send_player(player:get_player_name(),
                "Inventory full: clear one slot to receive "..def.name)
            return false
        end
    end
    -- Touch selection must equip immediately, not silently add a weapon to
    -- an invisible inventory slot. Mobile users have no keyboard.
    local selected=nil
    for i=1,inv:get_size("main") do
        if inv:get_stack("main",i):get_name()=="arsenal:"..id then
            selected=i
            break
        end
    end
    if selected and player.set_wield_index then
        player:set_wield_index(selected)
    end
    minetest.chat_send_player(player:get_player_name(),
        def.name.." selected. FIRE / ADS / R. Tap ARSENAL to switch.")
    return true
end
minetest.register_on_player_receive_fields(function(player,formname,fields)
    if formname~="arsenal:picker" or not valid_player(player) then return false end
    for _,c in ipairs(categories) do
        if fields["cat_"..c.key] then
            display_picker(player,c.key)
            return true
        end
    end
    for key in pairs(fields) do
        local id=key:match("^weapon_([a-z0-9_]+)$")
        if id and defs["arsenal:"..id] then
            grant_weapon(player,id)
            display_picker(player,active_category[player:get_player_name()])
            return true
        end
    end
    return true
end)
minetest.register_craftitem("arsenal:tablet",{
    description="ARSENAL - OPEN WEAPON SELECTOR (TAP FIRE)",
    inventory_image="arsenal_menu.png",
    stack_max=1,
    on_use=function(itemstack,user)
        display_picker(user)
        return itemstack
    end
})
minetest.register_chatcommand("arsenalmenu",{
    description="Open mobile touch category and gun picker",
    func=function(who)
        local player=minetest.get_player_by_name(who)
        if not player then return false,"Player unavailable" end
        display_picker(player)
        return true,"Arsenal weapon picker opened"
    end
})
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
-- Boot usable HOTBAR shortcuts, not console-only debug commands.
-- Legacy AK initializes first; NEVER overwrite an existing item or quickslot.
local function give_if_missing(p,item)
    local inventory=p:get_inventory()
    if inventory:contains_item("main",item) then return false end
    local size=inventory:get_size("main")
    for i=2,math.min(size,8) do
        local slot=inventory:get_stack("main",i)
        if slot:is_empty() then
            inventory:set_stack("main",i,ItemStack(item))
            return true
        end
    end
    -- Never discard saved items or clobber a user's selected weapon.
    local rem=inventory:add_item("main",item)
    return rem:is_empty()
end
minetest.register_on_joinplayer(function(player)
    local s=state(player)
    s.hud=player:hud_add({
        hud_elem_type="text",position={x=.025,y=.14},
        alignment={x=1,y=0},number=0xDDD7CD,
        text="",z_index=150})
    local who=player:get_player_name()
    minetest.after(2,function()
        local p=minetest.get_player_by_name(who)
        if not p then return end
        -- First hotbar slots are reachable on phones; avoid silent
        -- inventory insertion behind a full desktop-style hotbar.
        give_if_missing(p,"arsenal:tablet")
        if defs["arsenal:m9"] then give_if_missing(p,"arsenal:m9") end
        if defs["arsenal:ak47"] then give_if_missing(p,"arsenal:ak47") end
        if defs["arsenal:m4"] then give_if_missing(p,"arsenal:m4") end
        give_if_missing(p,"arsenal:attach_tool")
        give_if_missing(p,"arsenal:ammo_box")
    end)
end)
minetest.register_on_leaveplayer(function(player)
    local who=player:get_player_name()
    players[who]=nil
    crate_timestamps[who]=nil
    active_category[who]=nil
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
            if def.fire_mode=="burst" then
                if s.burst>0 and not s.reloading and
                    timestamp()>=s.next_fire then
                    local before=s.fired or 0
                    shoot(player,def,player:get_wielded_item(),s)
                    if (s.fired or 0)>before then
                        s.burst=s.burst-1
                    else
                        -- No ammo/invalid source: do not retry endless fake shots.
                        s.burst=0
                    end
                end
                -- All three rounds continue on the original fire clock,
                -- even if the user releases early, until reload or empty.
                if not c.dig then s.burst_guard=false end
            elseif c.dig then
                if def.fire_mode=="auto" then
                    shoot(player,def,player:get_wielded_item(),s)
                elseif not s.dig then
                    shoot(player,def,player:get_wielded_item(),s)
                end
            end
            s.dig=c.dig
            s.aux=c.aux1
        else
            if s.weapon~="" and s.hud then
                player:hud_change(s.hud,"text","")
            end
            if s.ads then player:set_fov(0,false,.18) end
            s.weapon=""
            s.reloading=false
            s.reload_end=0
            s.ads=false
            s.dig=false
            s.aux=false
            s.burst=0
            s.burst_guard=false
        end
    end
end)
minetest.log("action","[arsenal] real source preview mod loaded; no custom attachments in Classic Zombies")
