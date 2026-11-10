-- Xziel Zombies map authoring: per-wall weapon and price, per-door price.
-- Editing requires server or xz_map_builder privilege (or singleplayer).
local core = minetest
local api = xz_classic_props
local session = {}
local FORM_WEAPONS = "xzcp:choose_wall_weapon"
local FORM_WALL_PRICE = "xzcp:set_wall_price"
local FORM_DOOR_PRICE = "xzcp:set_door_price"
local MAX_PRICE = 50000

core.register_privilege("xz_map_builder", {
    description = "Build and configure Zombies map gameplay objects",
    give_to_singleplayer = true,
})

function api.can_build(p)
    if not p or not p:is_player() then return false end
    if core.is_singleplayer and core.is_singleplayer() then return true end
    local name = p:get_player_name()
    return core.check_player_privs(name, {server = true})
        or core.check_player_privs(name, {xz_map_builder = true})
end

local function valid_position(p, pos)
    if not pos then return false end
    local at = p:get_pos()
    if not at then return false end
    local x, y, z = at.x - pos.x, at.y - pos.y, at.z - pos.z
    return x*x + y*y + z*z < 100
end

local function alive_node(pos, name)
    local n = core.get_node_or_nil(pos)
    return n and n.name == "xz_classic_props:" .. name
end

local function price(value)
    if type(value) ~= "string" or not value:match("^%d+$") or #value > 7 then
        return nil
    end
    local n = tonumber(value)
    if not n or n > MAX_PRICE then return nil end
    return n
end

local function label(name)
    local item = core.registered_items[name]
    if not item then return name end
    return (item.description or name):gsub("\n.*", ""):sub(1, 65)
end

local function weapon_options()
    local items = api.weapon_pool()
    table.sort(items, function(a, b)
        return label(a):lower() < label(b):lower()
    end)
    return items
end

local function update_wall_label(pos)
    local m = core.get_meta(pos)
    local weapon = m:get_string("weapon")
    local desc = weapon ~= "" and label(weapon) or "Not configured"
    m:set_string("infotext", "Wall Buy: " .. desc .. " - "
        .. m:get_int("price") .. " points")
end
local function update_door_label(pos)
    local m = core.get_meta(pos)
    m:set_string("infotext", "Buyable Door - " .. m:get_int("price") .. " points")
end

local function show_wall_price(p)
    local s = session[p:get_player_name()]
    if not s or not s.weapon then return end
    local m = core.get_meta(s.pos)
    local pr = m:get_int("price")
    local fs = "formspec_version[4]size[10,5]"
        .. "label[0.5,0.45;WALL BUY - SET PRICE]"
        .. "label[0.5,1.25;" .. core.formspec_escape(label(s.weapon)) .. "]"
        .. "field[0.5,2.1;9,0.9;price;Points;" .. tostring(pr) .. "]"
        .. "button[0.5,3.4;4,0.95;save_wall;CONFIRM]"
        .. "button[5,3.4;4,0.95;back_wall;BACK]"
    core.show_formspec(p:get_player_name(), FORM_WALL_PRICE, fs)
end

function api.configure_wall(pos, p)
    if not api.can_build(p) or not api.is_editing() then return false end
    local pool = weapon_options()
    if #pool == 0 then
        api.tell(p, "No Arsenal weapons found. Install the Arsenal first.")
        return false
    end
    local s = {kind = "wall_buy", pos = vector.new(pos), weapons = pool}
    session[p:get_player_name()] = s
    local names = {}
    for i, id in ipairs(pool) do
        names[i] = core.formspec_escape(label(id))
    end
    local fs = "formspec_version[4]size[11,9]"
        .. "label[0.55,0.4;WALL BUY - CHOOSE ARSENAL WEAPON]"
        .. "textlist[0.5,1;10,6.6;weapons;" .. table.concat(names, ",")
        .. ";0;false]"
        .. "button_exit[3.5,7.8;4,0.8;cancel;CANCEL]"
    core.show_formspec(p:get_player_name(), FORM_WEAPONS, fs)
    return true
end

function api.configure_door(pos, p)
    if not api.can_build(p) or not api.is_editing() then return false end
    session[p:get_player_name()] = {kind = "buyable_door", pos = vector.new(pos)}
    local fs = "formspec_version[4]size[10,4.8]"
        .. "label[0.5,0.45;DOOR BUY - SET PRICE]"
        .. "field[0.5,1.45;9,0.9;price;Points;"
        .. core.get_meta(pos):get_int("price") .. "]"
        .. "button[0.5,3;9,0.9;save_door;CONFIRM]"
    core.show_formspec(p:get_player_name(), FORM_DOOR_PRICE, fs)
    return true
end

local function setup_wall(pos)
    local m = core.get_meta(pos)
    if m:get_string("price_set") ~= "1" then
        m:set_int("price", 1200)
        m:set_string("price_set", "1")
    end
    update_wall_label(pos)
end
local function setup_door(pos)
    local m = core.get_meta(pos)
    if m:get_string("price_set") ~= "1" then
        m:set_int("price", 1000)
        m:set_string("price_set", "1")
    end
    update_door_label(pos)
end
core.override_item("xz_classic_props:wall_buy", {
    on_construct = setup_wall,
    after_place_node = function(pos, placer)
        if placer then api.configure_wall(pos, placer) end
    end,
    on_rightclick = function(pos, node, player, stack)
        if api.is_editing() then
            api.configure_wall(pos, player)
        else
            local m = core.get_meta(pos)
            local weapon = m:get_string("weapon")
            local cost = m:get_int("price")
            if weapon == "" then
                api.tell(player, "Wall Buy not configured by the map maker.")
            else
                api.purchase_weapon(player, weapon, cost)
            end
        end
        return stack
    end,
})
core.override_item("xz_classic_props:buyable_door", {
    on_construct = setup_door,
    after_place_node = function(pos, placer)
        if placer then api.configure_door(pos, placer) end
    end,
    on_rightclick = function(pos, node, player, stack)
        if api.is_editing() then
            api.configure_door(pos, player)
        else
            local cost = core.get_meta(pos):get_int("price")
            if api.spend_points(player, cost) then
                if api.snapshot_door then api.snapshot_door(pos) end
                core.remove_node(pos)
                api.tell(player, "Door opened (-" .. cost .. " points)")
            end
        end
        return stack
    end,
})

core.register_on_player_receive_fields(function(p, formname, fields)
    if not (formname == FORM_WEAPONS or formname == FORM_WALL_PRICE
        or formname == FORM_DOOR_PRICE) then return false end
    local name = p:get_player_name()
    local s = session[name]
    if not s or not api.can_build(p) or not api.is_editing()
        or not valid_position(p, s.pos) or not alive_node(s.pos, s.kind) then
        session[name] = nil
        return true
    end
    if fields.cancel or (fields.quit and not fields.weapons) then
        session[name] = nil
        return true
    end
    if formname == FORM_WEAPONS and fields.weapons then
        local evt = core.explode_textlist_event(fields.weapons)
        if (evt.type == "CHG" or evt.type == "DCL")
            and s.weapons[evt.index] then
            s.weapon = s.weapons[evt.index]
            show_wall_price(p)
        end
    elseif formname == FORM_WALL_PRICE then
        if fields.back_wall then
            api.configure_wall(s.pos, p)
        elseif fields.save_wall then
            local cost = price(fields.price)
            if not cost or not s.weapon or not core.registered_items[s.weapon] then
                api.tell(p, "Invalid price (0-50000) or weapon.")
                show_wall_price(p)
                return true
            end
            local m = core.get_meta(s.pos)
            m:set_string("weapon", s.weapon)
            m:set_int("price", cost)
            m:set_string("price_set", "1")
            update_wall_label(s.pos)
            if api.refresh_wall_preview then api.refresh_wall_preview(s.pos,p) end
            api.tell(p, "Wall Buy saved: " .. label(s.weapon) .. " / " .. cost)
            session[name] = nil
        end
    elseif formname == FORM_DOOR_PRICE and fields.save_door then
        local cost = price(fields.price)
        if not cost then
            api.tell(p, "Invalid door price (0-50000).")
            api.configure_door(s.pos, p)
            return true
        end
        local m = core.get_meta(s.pos)
        m:set_int("price", cost)
        m:set_string("price_set", "1")
        update_door_label(s.pos)
        api.tell(p, "Door price saved: " .. cost)
        session[name] = nil
    end
    return true
end)

core.register_on_leaveplayer(function(p) session[p:get_player_name()] = nil end)
