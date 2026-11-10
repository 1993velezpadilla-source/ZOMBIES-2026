-- Xziel Classic Zombies props for Luanti/VoxeLibre.
-- Original game-agnostic machines and multiplayer-safe point accounting.
-- No COD/Activision models, marks, logos, music or weapon assets included.
local core = minetest
local store = core.get_mod_storage()
local api = {}
_G.xz_classic_props = api

local PREFIX = "xzcp:"
local INITIAL_POINTS = 500
local MAX_POINTS = 100000000
local POWER_KEY = "power_enabled"
local ROUND_KEY = "round"
local PERKS = {
    vitality = { name = "Iron Heart", cost = 2500, power = true },
    revive = { name = "Second Chance", cost = 1500, power = true },
    speed = { name = "Rapid Hands", cost = 3000, power = true },
    double = { name = "Double Impact", cost = 2000, power = true },
}

local function player_ok(p)
    return p and p.is_player and p:is_player()
end
local function note(p, msg)
    if player_ok(p) then
        core.chat_send_player(p:get_player_name(), "[Zombies] " .. msg)
    end
end
local function state(p)
    return p:get_meta()
end
local function points(p)
    return math.max(0, state(p):get_int(PREFIX .. "points"))
end
function api.get_points(p)
    if not player_ok(p) then return 0 end
    return points(p)
end
function api.add_points(p, amount)
    if not player_ok(p) or type(amount) ~= "number" or amount ~= amount then
        return false
    end
    amount = math.floor(amount)
    if amount <= 0 then return false end
    state(p):set_int(PREFIX .. "points", math.min(MAX_POINTS, points(p) + amount))
    return true
end
function api.award_kill(p, headshot)
    return api.add_points(p, headshot and 100 or 60)
end
local function pay(p, amount)
    local balance = points(p)
    if balance < amount then
        note(p, "Need " .. amount .. " points. You have " .. balance .. ".")
        return false
    end
    state(p):set_int(PREFIX .. "points", balance - amount)
    return true
end
function api.power_on()
    return store:get_int(POWER_KEY) == 1
end
function api.get_round()
    return math.max(0, store:get_int(ROUND_KEY))
end
function api.set_round(n)
    if type(n) ~= "number" or n ~= n then return false end
    n = math.floor(n)
    if n < 0 or n > 9999 then return false end
    store:set_int(ROUND_KEY, n)
    return true
end

local function perk_active(p, id)
    return player_ok(p) and state(p):get_int(PREFIX .. "perk_" .. id) == 1
end
function api.has_perk(p, id)
    return PERKS[id] ~= nil and perk_active(p, id)
end
-- Weapon mods can call these without changing their original models/animations.
function api.reload_time_multiplier(p)
    return perk_active(p, "speed") and 0.5 or 1
end
function api.fire_interval_multiplier(p)
    return perk_active(p, "double") and 0.85 or 1
end
function api.damage_multiplier(p, stack)
    local factor = perk_active(p, "double") and 1.25 or 1
    if stack and stack.get_meta and stack:get_meta():get_int(PREFIX .. "pap") > 0 then
        factor = factor * 2
    end
    return factor
end

local function base_hp(p)
    local meta = state(p)
    local original = meta:get_int(PREFIX .. "base_hp")
    if original > 0 then return original end
    local prop = p:get_properties()
    original = (prop and prop.hp_max) or 20
    original = math.max(1, math.floor(original))
    meta:set_int(PREFIX .. "base_hp", original)
    return original
end
local function update_vitality(p, refill)
    local target = base_hp(p) + (perk_active(p, "vitality") and 20 or 0)
    p:set_properties({hp_max = target})
    if refill then p:set_hp(target) end
end
local function buy_perk(p, id)
    if not player_ok(p) then return end
    local perk = PERKS[id]
    if perk.power and not api.power_on() then
        note(p, "Turn on the power first.")
        return
    end
    if perk_active(p, id) then
        note(p, perk.name .. " already active.")
        return
    end
    if not pay(p, perk.cost) then return end
    state(p):set_int(PREFIX .. "perk_" .. id, 1)
    if id == "vitality" then update_vitality(p, true) end
    note(p, perk.name .. " purchased! (-" .. perk.cost .. " points)")
end
local function reset_perks(p)
    if not player_ok(p) then return end
    for id in pairs(PERKS) do state(p):set_int(PREFIX .. "perk_" .. id, 0) end
    update_vitality(p, false)
end

core.register_on_joinplayer(function(p)
    if not player_ok(p) then return end
    local m = state(p)
    if m:get_int(PREFIX .. "initialized") == 0 then
        m:set_int(PREFIX .. "initialized", 1)
        m:set_int(PREFIX .. "points", INITIAL_POINTS)
    end
    if perk_active(p, "vitality") then update_vitality(p, false) end
end)
core.register_on_dieplayer(function(p)
    reset_perks(p)
end)
-- One single-player "Second Chance" save; consumed on otherwise lethal damage.
-- For cooperative teammate revival, add a separate downed-state system later.
core.register_on_player_hpchange(function(p, delta)
    if not player_ok(p) or delta >= 0 or not perk_active(p, "revive") then
        return delta
    end
    if p:get_hp() + delta > 0 then return delta end
    state(p):set_int(PREFIX .. "perk_revive", 0)
    local name = p:get_player_name()
    core.after(0, function()
        local active = core.get_player_by_name(name)
        if active then
            active:set_hp(math.max(1, math.min(10, base_hp(active))))
            note(active, "Second Chance saved you! The perk was consumed.")
        end
    end)
    return 1 - p:get_hp()
end, true)

local function textured(id)
    return "xzcp_" .. id .. ".png"
end
local function register_prop(id, description, action, light)
    core.register_node("xz_classic_props:" .. id, {
        description = description,
        drawtype = "nodebox",
        node_box = {type = "fixed", fixed = {
            {-0.45, -0.5, -0.42, 0.45, 0.5, 0.42},
            {-0.28, 0.27, -0.5, 0.28, 0.45, -0.42},
        }},
        selection_box = {type="fixed", fixed={-0.5,-0.5,-0.5,0.5,0.5,0.5}},
        collision_box = {type="fixed", fixed={-0.45,-0.5,-0.42,0.45,0.5,0.42}},
        tiles = {textured(id)},
        paramtype = "light",
        paramtype2 = "facedir",
        light_source = light or 0,
        groups = {cracky = 2, oddly_breakable_by_hand = 2},
        on_construct = function(pos)
            core.get_meta(pos):set_string("infotext", description .. " (tap to use)")
        end,
        on_rightclick = function(pos, node, clicker, itemstack)
            if player_ok(clicker) and action then action(pos, clicker) end
            return itemstack
        end,
    })
end

register_prop("power_switch", "Power Switch", function(pos, p)
    if api.power_on() then
        note(p, "Power is already ON.")
        return
    end
    store:set_int(POWER_KEY, 1)
    note(p, "POWER ON! Perk machines and upgrade station are available.")
end, 2)

register_prop("perk_vitality", "Iron Heart - 2500 pts (Jugger-style)", function(_, p)
    buy_perk(p, "vitality")
end, 3)
register_prop("perk_revive", "Second Chance - 1500 pts (Revive-style)", function(_, p)
    buy_perk(p, "revive")
end, 3)
register_prop("perk_speed", "Rapid Hands - 3000 pts (Speed-style)", function(_, p)
    buy_perk(p, "speed")
end, 3)
register_prop("perk_double", "Double Impact - 2000 pts (Double Tap-style)", function(_, p)
    buy_perk(p, "double")
end, 3)

local function eligible_weapon(name, def)
    if not def or not def.groups or def.groups.weapon ~= 1 then return false end
    return name:match("^arsenal:[a-z0-9_]+$") ~= nil
        or name == "ak47dev:ak47" or name == "ak47dev:m9"
end
local function weapon_pool()
    local pool = {}
    for name, def in pairs(core.registered_items or {}) do
        if eligible_weapon(name, def) then pool[#pool + 1] = name end
    end
    table.sort(pool)
    return pool
end
local function give_weapon(p, name, cost)
    if not core.registered_items[name] then
        note(p, "Weapon " .. name .. " is unavailable in this build.")
        return false
    end
    local inv = p:get_inventory()
    if not inv or not inv:room_for_item("main", name) then
        note(p, "Inventory full.")
        return false
    end
    if not pay(p, cost) then return false end
    inv:add_item("main", name)
    note(p, "Received " .. name .. " (-" .. cost .. " points)")
    return true
end
register_prop("mystery_box", "Mystery Box - 950 pts", function(_, p)
    local pool = weapon_pool()
    if #pool == 0 then
        note(p, "No compatible Arsenal weapons installed; no points charged.")
        return
    end
    local selected = pool[math.random(#pool)]
    give_weapon(p, selected, 950)
end, 2)
register_prop("wall_buy", "AK-47 Wall Buy - 1200 pts", function(_, p)
    local weapon = core.registered_items["arsenal:ak47"] and "arsenal:ak47"
        or core.registered_items["ak47dev:ak47"] and "ak47dev:ak47"
    if not weapon then
        note(p, "AK-47 not installed; no points charged.")
        return
    end
    give_weapon(p, weapon, 1200)
end)

register_prop("pack_a_punch", "Weapon Upgrade Station - 5000 pts", function(_, p)
    if not api.power_on() then note(p, "Turn on the power first."); return end
    local held = p:get_wielded_item()
    local name = held:get_name()
    if not eligible_weapon(name, core.registered_items[name]) then
        note(p, "Hold a compatible Arsenal weapon.")
        return
    end
    if held:get_meta():get_int(PREFIX .. "pap") >= 1 then
        note(p, "This weapon is already upgraded.")
        return
    end
    if not pay(p, 5000) then return end
    held:get_meta():set_int(PREFIX .. "pap", 1)
    p:set_wielded_item(held)
    note(p, "Weapon upgraded! Damage bonus activates when Arsenal uses the props API.")
end, 3)

register_prop("buyable_door", "Buyable Door - 1000 pts", function(pos, p)
    if not pay(p, 1000) then return end
    core.remove_node(pos)
    note(p, "Door opened (-1000 points)")
end)

local function boards_text(n)
    return "Repairable Barricade (" .. n .. "/3 boards)"
end
register_prop("barricade", "Repairable Barricade", function(pos, p)
    local meta = core.get_meta(pos)
    local n = math.max(0, math.min(3, meta:get_int("boards")))
    if n >= 3 then note(p, "Barricade is already repaired."); return end
    meta:set_int("boards", n + 1)
    meta:set_string("infotext", boards_text(n + 1))
    api.add_points(p, 10)
    note(p, "Board repaired (+10 points)")
end)
-- Called by future zombie attack AI. Does not perform periodic map scans.
function api.damage_barricade(pos)
    local node = core.get_node_or_nil(pos)
    if not node or node.name ~= "xz_classic_props:barricade" then return false end
    local meta = core.get_meta(pos)
    local n = math.max(0, math.min(3, meta:get_int("boards")))
    if n <= 1 then core.remove_node(pos); return true end
    meta:set_int("boards", n - 1)
    meta:set_string("infotext", boards_text(n - 1))
    return true
end
-- Map markers are inert until the wave/spawn module consumes their positions.
register_prop("zombie_spawn_marker", "Zombie Spawn Marker (map builder)", function(_, p)
    note(p, "Spawn marker: awaiting future wave AI.")
end)
register_prop("player_spawn_marker", "Player Spawn Marker (map builder)", function(_, p)
    note(p, "Player spawn marker: awaiting mode controller.")
end)
register_prop("round_display", "Round Counter", function(_, p)
    note(p, "ROUND " .. api.get_round() .. " | POINTS " .. points(p))
end, 1)

-- On first placement, barricades start fully repaired (right-click is for repairs).
core.register_on_placenode(function(pos, node)
    if node.name == "xz_classic_props:barricade" then
        local meta = core.get_meta(pos)
        meta:set_int("boards", 3)
        meta:set_string("infotext", boards_text(3))
    end
end)

core.register_chatcommand("xzcp_points", {
    params = "<player> <amount>",
    description = "Admin testing only: grant points for the new interactables.",
    privs = {server = true},
    func = function(_, params)
        local who, amount = params:match("^(%S+)%s+(%-?%d+)$")
        local target = who and core.get_player_by_name(who)
        if not target then return false, "Player not online." end
        if not api.add_points(target, tonumber(amount)) then
            return false, "Use a positive integer."
        end
        return true, who .. " now has " .. points(target) .. " points."
    end
})

-- Public bridge for map components, without changing original Arsenal assets.
api.tell = note
api.weapon_pool = weapon_pool
function api.spend_points(p, amount)
    if not player_ok(p) or type(amount) ~= "number" or amount ~= amount
        or amount < 0 or amount > 50000 or amount ~= math.floor(amount) then
        return false
    end
    if amount == 0 then return true end
    return pay(p, amount)
end
function api.purchase_weapon(p, weapon, amount)
    if type(weapon) ~= "string"
        or not eligible_weapon(weapon, core.registered_items[weapon])
        or type(amount) ~= "number" or amount < 0 or amount > 50000
        or amount ~= math.floor(amount) then
        note(p, "Invalid map weapon or price.")
        return false
    end
    return give_weapon(p, weapon, amount)
end
local modpath = core.get_modpath("xz_classic_props")
dofile(modpath .. "/mode.lua")
dofile(modpath .. "/builder.lua")

core.log("action", "[xz_classic_props] 17 visible core and 6 hidden utility Zombies props registered")
