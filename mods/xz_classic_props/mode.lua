-- Xziel map EDIT / PLAY TEST.
-- The mode applies to the active world (not individual players).
-- Utility nodes retain position, lighting/collision and metadata while visuals are hidden.
local core = minetest
local api = xz_classic_props
local storage = core.get_mod_storage()
local MARKER_KEY = "editor:markers_v1"
local MODE_KEY = "editor:play_mode"
local marker_names = {
    player_spawn_marker = {walkable=false, light=0},
    zombie_spawn_marker = {walkable=false, light=0},
    utility_barrier = {walkable=true, light=0},
    utility_light_5 = {walkable=false, light=5},
    utility_light_10 = {walkable=false, light=10},
    utility_light_14 = {walkable=false, light=14},
}
local index = core.deserialize(storage:get_string(MARKER_KEY)) or {}
local history = {doors={}, players={}}
local playing = storage:get_int(MODE_KEY) == 1
local timer = 0

function api.is_editing() return not playing end
function api.is_playing() return playing end

local function save_index()
    storage:set_string(MARKER_KEY, core.serialize(index))
end
local function show_markers(visible)
    for key, id in pairs(index) do
        if marker_names[id] then
            local pos = core.string_to_pos(key)
            if pos then
                local n = core.get_node_or_nil(pos)
                if n then
                    local base = "xz_classic_props:" .. id
                    local expected = base .. "_hidden"
                    if n.name == base or n.name == expected then
                        local target = visible and base or expected
                        if n.name ~= target then
                            core.swap_node(pos, {name=target, param2=n.param2})
                        end
                    else
                        index[key] = nil
                    end
                end
            else
                index[key] = nil
            end
        else
            index[key] = nil
        end
    end
    save_index()
end

local function track(pos, id)
    local key = core.pos_to_string(pos)
    index[key] = id
    save_index()
end
local function untrack(pos)
    local key = core.pos_to_string(pos)
    if index[key] then
        index[key] = nil
        save_index()
    end
end
local function id_of(name)
    if type(name) ~= "string" then return nil end
    local id = name:match("^xz_classic_props:([a-z0-9_]+)$")
    if id and marker_names[id] then return id end
    local hidden = name:match("^xz_classic_props:([a-z0-9_]+)_hidden$")
    if hidden and marker_names[hidden] then return hidden end
    return nil
end

-- In the editor these are recognizable and selectable.
-- In PLAY / exported runtime variants are invisible, without losing their effects.
for id, def in pairs(marker_names) do
    local visible_name = "xz_classic_props:" .. id
    local hidden_name = visible_name .. "_hidden"
    local tint = def.walkable and "#C84444" or def.light > 0 and "#FFD044" or "#39AFFF"
    local editor_texture = "xzcp_marker.png^[colorize:" .. tint .. ":190"

    if id ~= "player_spawn_marker" and id ~= "zombie_spawn_marker" then
        core.register_node(visible_name, {
            description = id:gsub("_", " "):upper() .. " (EDITOR ONLY)",
            tiles = {editor_texture},
            drawtype = "glasslike",
            use_texture_alpha = "blend",
            paramtype = "light",
            light_source = def.light,
            walkable = def.walkable,
            pointable = true,
            sunlight_propagates = true,
            groups = {cracky=2, oddly_breakable_by_hand=2},
        })
    else
        core.override_item(visible_name, {
            tiles = {editor_texture},
            drawtype = "glasslike",
            use_texture_alpha = "blend",
            walkable = false,
            pointable = true,
            light_source = 0,
        })
    end
    core.register_node(hidden_name, {
        description = id .. " (INTERNAL; HIDDEN IN PLAY)",
        drawtype = "airlike",
        tiles = {"blank.png"},
        paramtype = "light",
        light_source = def.light,
        walkable = def.walkable,
        pointable = false,
        diggable = false,
        buildable_to = false,
        sunlight_propagates = true,
        groups = {not_in_creative_inventory=1},
    })
end

core.register_on_placenode(function(pos, node)
    local id = id_of(node.name)
    if not id then return end
    track(pos, id)
    if playing and node.name:sub(-7) ~= "_hidden" then
        core.swap_node(pos, {name="xz_classic_props:"..id.."_hidden",param2=node.param2})
    end
end)
core.register_on_dignode(function(pos, node)
    if id_of(node.name) then untrack(pos) end
end)
-- Imported / unloaded map blocks become correct automatically on load.
core.register_lbm({
    name = "xz_classic_props:marker_mode_sync",
    nodenames = (function()
        local out = {}
        for id in pairs(marker_names) do
            out[#out+1] = "xz_classic_props:" .. id
            out[#out+1] = "xz_classic_props:" .. id .. "_hidden"
        end
        return out
    end)(),
    run_at_every_load = true,
    action = function(pos, node)
        local id = id_of(node.name)
        if not id then return end
        local key = core.pos_to_string(pos)
        if index[key] ~= id then track(pos,id) end
        local target = "xz_classic_props:"..id..(playing and "_hidden" or "")
        if node.name ~= target then
            core.swap_node(pos, {name=target, param2=node.param2})
        end
    end,
})

local function player_spawn()
    local positions = {}
    for key, id in pairs(index) do
        if id == "player_spawn_marker" then
            local p = core.string_to_pos(key)
            if p then positions[#positions+1] = p end
        end
    end
    table.sort(positions, function(a,b)
        return core.pos_to_string(a) < core.pos_to_string(b)
    end)
    return positions[1]
end
local function move_to_spawn(p)
    local pos = player_spawn()
    if not pos then return false end
    p:set_pos({x=pos.x, y=pos.y + 1.5, z=pos.z})
    return true
end
core.register_on_respawnplayer(function(p)
    if not playing then return false end
    return move_to_spawn(p)
end)

local function snapshot_players()
    history.players = {}
    for _, p in ipairs(core.get_connected_players()) do
        local m = p:get_meta()
        local inv = p:get_inventory()
        local main = {}
        for i, s in ipairs(inv:get_list("main") or {}) do
            main[i] = s:to_string()
        end
        local flags = {}
        for _, id in ipairs({"vitality","revive","speed","double"}) do
            flags[id] = m:get_int("xzcp:perk_" .. id)
        end
        history.players[p:get_player_name()] = {
            pos=p:get_pos(), hp=p:get_hp(), hp_max=p:get_properties().hp_max,
            points=m:get_int("xzcp:points"), flags=flags, inventory=main
        }
    end
end
local function restore_players()
    for name, snap in pairs(history.players) do
        local p = core.get_player_by_name(name)
        if p then
            local meta = p:get_meta()
            meta:set_int("xzcp:points", snap.points)
            for id, value in pairs(snap.flags) do
                meta:set_int("xzcp:perk_" .. id, value)
            end
            if snap.hp_max then p:set_properties({hp_max=snap.hp_max}) end
            if snap.hp then p:set_hp(snap.hp) end
            local inv = p:get_inventory()
            if inv then inv:set_list("main", snap.inventory) end
            if snap.pos then p:set_pos(snap.pos) end
        end
    end
    history.players = {}
end
function api.snapshot_door(pos)
    if not playing then return end
    local key=core.pos_to_string(pos)
    if history.doors[key] then return end
    local node=core.get_node_or_nil(pos)
    if not node then return end
    history.doors[key] = {
        name=node.name, param2=node.param2,
        metadata=core.get_meta(pos):to_table()
    }
end
local function restore_doors()
    for key, snapshot in pairs(history.doors) do
        local pos=core.string_to_pos(key)
        if pos then
            core.set_node(pos, {name=snapshot.name,param2=snapshot.param2})
            core.get_meta(pos):from_table(snapshot.metadata)
        end
    end
    history.doors = {}
end

local initial_power, initial_round
function api.start_test(p)
    if not api.can_build(p) or playing then return false end
    initial_power=storage:get_int("power_enabled")
    initial_round=storage:get_int("round")
    snapshot_players()
    playing=true
    storage:set_int(MODE_KEY,1)
    storage:set_int("round",1)
    storage:set_int("power_enabled",0)
    history.doors={}
    show_markers(false)
    for _, player in ipairs(core.get_connected_players()) do
        move_to_spawn(player)
    end
    api.tell(p, "PLAY TEST started. Markers invisible; barriers and lights still work.")
    if not player_spawn() then
        api.tell(p, "No Player Spawner found. Place one in EDIT.")
    end
    if api.waves_start then api.waves_start() end
    return true
end
function api.stop_test(p)
    if not api.can_build(p) or not playing then return false end
    if api.waves_stop then api.waves_stop() end
    playing=false
    storage:set_int(MODE_KEY,0)
    restore_doors()
    if initial_power then storage:set_int("power_enabled",initial_power) end
    if initial_round then storage:set_int("round",initial_round) end
    show_markers(true)
    restore_players()
    api.tell(p, "EDIT MODE restored. Test purchases and opened doors rolled back.")
    return true
end

local function open_editor(p)
    if not api.can_build(p) then
        api.tell(p, "Map builder permission required.")
        return
    end
    local count=0
    for _ in pairs(index) do count=count+1 end
    local label = playing and "PLAY TEST ACTIVE" or "EDIT MODE"
    local button = playing and "STOP_TEST" or "PLAY_TEST"
    core.show_formspec(p:get_player_name(),"xzcp:editor",
        "formspec_version[4]size[9.5,5]"
        .. "label[0.5,0.5;XZIEL ZOMBIES - MAP EDITOR]"
        .. "label[0.5,1.25;" .. label .. "]"
        .. "label[0.5,1.85;Utility markers: " .. count .. "]"
        .. "button[0.5,2.65;8.5,1.2;toggle;" .. button .. "]"
        .. "button_exit[2.5,4.1;4.5,0.65;close;CLOSE]")
end
core.register_craftitem("xz_classic_props:map_editor", {
    description = "XZIEL Map Editor - PLAY / STOP",
    inventory_image = "xzcp_map_editor.png",
    stack_max = 1,
    on_use = function(stack, p) open_editor(p); return stack end,
    on_secondary_use = function(stack, p) open_editor(p); return stack end,
})
core.register_chatcommand("xz_editor", {
    description = "Open map editor PLAY/STOP controls",
    func = function(name)
        local p = core.get_player_by_name(name)
        if not p then return false, "Player not connected" end
        open_editor(p)
        return true
    end
})
core.register_on_player_receive_fields(function(p, formname, fields)
    if formname ~= "xzcp:editor" then return false end
    if fields.toggle and api.can_build(p) then
        if playing then api.stop_test(p) else api.start_test(p) end
        open_editor(p)
    end
    return true
end)

-- Keep import/export coordinate data independent of marker visibility.
function api.get_markers(kind)
    local result = {}
    if not marker_names[kind] then return result end
    for key, id in pairs(index) do
        if id == kind then
            local pos = core.string_to_pos(key)
            if pos then result[#result + 1] = pos end
        end
    end
    return result
end
core.register_on_joinplayer(function(p)
    if playing then
        local name=p:get_player_name()
        core.after(0.5,function()
            local player=core.get_player_by_name(name)
            if player and playing then move_to_spawn(player) end
        end)
    end
end)
