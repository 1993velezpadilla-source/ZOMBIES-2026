-- PLAY-only developer controls for authorized map makers.
-- Never available to public players without build permission.
local core=minetest
local api=xz_classic_props
local options={}
local forms={main="xzcp:developer",weapon="xzcp:developer_weapons"}
local selected={}
local clock=0
local function allowed(p)
    return p and p:is_player() and api.is_playing() and api.can_build(p)
end
local function flags(p)
    local name=p:get_player_name()
    if not options[name] then options[name]={health=false,ammo=false} end
    return options[name]
end
local function notify(p,msg) api.tell(p,"[DEV] "..msg) end

local function label(id)
    local def=core.registered_items[id] or {}
    return (def.description or id):gsub("\n.*",""):sub(1,55)
end

function api.open_developer(p)
    if not allowed(p) then return false end
    local d=flags(p)
    local fs="formspec_version[4]size[10.7,8.6]"
      .. "label[0.5,0.5;DEVELOPER - PLAY TEST ONLY]"
      .. "label[0.5,1.1;POINTS]"
      .. "button[0.5,1.45;3,0.8;points_1000;+1000]"
      .. "button[3.7,1.45;3,0.8;points_10000;+10000]"
      .. "button[6.9,1.45;3,0.8;points_50000;+50000]"
      .. "button[0.5,2.7;9.4,0.95;health;INFINITE HEALTH: "
          .. (d.health and "ON" or "OFF") .. "]"
      .. "button[0.5,3.85;9.4,0.95;ammo;INFINITE AMMO: "
          .. (d.ammo and "ON" or "OFF") .. "]"
      .. "button[0.5,5.0;9.4,0.95;choose_weapon;OPEN ALL WEAPONS]"
      .. "label[0.5,6.2;Only the map creator can use this panel.]"
      .. "button[0.5,7.45;9.4,0.65;back;BACK TO PLAY]"
    core.show_formspec(p:get_player_name(),forms.main,fs)
    return true
end

function api.developer_flags(p)
    if not allowed(p) then return {health=false,ammo=false} end
    local f=flags(p)
    return {health=f.health,ammo=f.ammo}
end

function api.reset_developer()
    for n in pairs(options) do options[n]=nil end
    for n in pairs(selected) do selected[n]=nil end
end

function api.open_developer_weapons(p)
    if not allowed(p) then return false end
    local pool=api.weapon_pool()
    table.sort(pool,function(a,b) return label(a)<label(b) end)
    selected[p:get_player_name()]=pool
    local entries={}
    for i,id in ipairs(pool) do entries[i]=core.formspec_escape(label(id)) end
    local fs="formspec_version[4]size[11.5,9]"
        .. "label[0.5,0.4;DEVELOPER ARSENAL - TAP TO RECEIVE]"
        .. "textlist[0.5,1;10.5,6.75;weapons;"
        .. table.concat(entries,",") .. ";0;false]"
        .. "button[0.5,8;10.5,0.65;back;BACK]"
    core.show_formspec(p:get_player_name(),forms.weapon,fs)
    return true
end

core.register_on_player_receive_fields(function(p,formname,fields)
    if formname~=forms.main and formname~=forms.weapon then return false end
    if not allowed(p) then return true end
    if fields.back then
        if formname==forms.weapon then api.open_developer(p)
        else api.open_editor(p) end
        return true
    end
    if formname==forms.weapon then
        if fields.weapons then
            local ev=core.explode_textlist_event(fields.weapons)
            if (ev.type=="CHG" or ev.type=="DCL") then
                local pool=selected[p:get_player_name()] or {}
                local name=pool[ev.index]
                if name and core.registered_items[name] then
                    local inv=p:get_inventory()
                    if inv and inv:room_for_item("main",name) then
                        inv:add_item("main",name)
                        notify(p,"Added "..label(name))
                    else
                        notify(p,"Inventory full.")
                    end
                    api.open_developer_weapons(p)
                end
            end
        end
    else
        local amount = fields.points_1000 and 1000
            or fields.points_10000 and 10000
            or fields.points_50000 and 50000
        if amount then api.add_points(p,amount)
            notify(p,"+"..amount.." points")
        elseif fields.health then
            local f=flags(p)
            f.health=not f.health
            notify(p,"Infinite health "..(f.health and "ON" or "OFF"))
        elseif fields.ammo then
            local f=flags(p)
            f.ammo=not f.ammo
            notify(p,"Infinite ammo "..(f.ammo and "ON" or "OFF"))
        elseif fields.choose_weapon then
            api.open_developer_weapons(p)
            return true
        end
        api.open_developer(p)
    end
    return true
end)

-- Do not allow damage to kill an authorized developer during a PLAY test.
core.register_on_player_hpchange(function(p,delta)
    if delta < 0 and allowed(p) and flags(p).health then return 0 end
    return delta
end,true)

-- Arsenal source currently uses ar_clip / ar_reserve metadata.
-- Only test mode; original values restored by map editor's inventory snapshot.
core.register_globalstep(function(dt)
    clock=clock+dt
    if clock<0.25 then return end
    clock=0
    if not api.is_playing() then return end
    for _,p in ipairs(core.get_connected_players()) do
        if allowed(p) then
            local f=flags(p)
            if f.health then
                local hp_max=p:get_properties().hp_max or 20
                if p:get_hp()<hp_max then p:set_hp(hp_max) end
            end
            if f.ammo then
                local stack=p:get_wielded_item()
                local id=stack:get_name()
                if core.registered_items[id] and
                    core.registered_items[id].groups and
                    core.registered_items[id].groups.weapon == 1 and
                    (id:match("^arsenal:") or id:match("^ak47dev:")) then
                    local meta=stack:get_meta()
                    meta:set_int("ar_clip",999)
                    meta:set_int("ar_reserve",9999)
                    -- No other weapon metadata changed.
                    p:set_wielded_item(stack)
                end
            end
        end
    end
end)

core.register_chatcommand("xz_dev",{
    description="Open developer cheats (map maker during PLAY only)",
    func=function(name)
        local p=core.get_player_by_name(name)
        if not p or not allowed(p) then return false,"Not available." end
        api.open_developer(p)
        return true
    end
})
core.register_on_leaveplayer(function(p)
    options[p:get_player_name()]=nil
    selected[p:get_player_name()]=nil
end)
