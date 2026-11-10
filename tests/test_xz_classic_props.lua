-- Pure Lua 5.1 smoke test: no engine or assets needed.
local nodes, commands, callbacks, players, items = {}, {}, {}, {}, {}
local function meta()
    local data = {}
    return {
        get_int = function(_, k) return data[k] or 0 end,
        set_int = function(_, k, v) data[k] = v end,
        get_string = function(_, k) return data[k] or "" end,
        set_string = function(_, k, v) data[k] = v end,
    }
end
local storage = meta()
local node_meta = {}
local function newplayer(name)
    local p = {name=name, meta=meta(), health=20, props={hp_max=20}}
    local inv = {list={}}
    function inv:room_for_item() return true end
    function inv:add_item(_, thing) self.list[#self.list+1]=thing end
    function p:is_player() return true end
    function p:get_player_name() return self.name end
    function p:get_meta() return self.meta end
    function p:get_inventory() return inv end
    function p:get_properties() return self.props end
    function p:set_properties(props) self.props.hp_max=props.hp_max end
    function p:get_hp() return self.health end
    function p:set_hp(hp) self.health=hp end
    function p:get_wielded_item()
        if self.wield then return self.wield end
        local stack={name="arsenal:ak47", itemmeta=meta()}
        function stack:get_name() return self.name end
        function stack:get_meta() return self.itemmeta end
        self.wield=stack
        return stack
    end
    function p:set_wielded_item(item) self.wield=item end
    players[name]=p
    return p
end
minetest={
    get_mod_storage=function() return storage end,
    registered_items=items,
    registered_nodes=nodes,
    register_node=function(name, def) nodes[name]=def end,
    register_on_joinplayer=function(cb)
        callbacks.join=callbacks.join or {}
        table.insert(callbacks.join,cb)
    end,
    register_on_dieplayer=function(cb) callbacks.die=cb end,
    register_on_player_hpchange=function(cb, modifier) assert(modifier); callbacks.hp=cb end,
    register_on_placenode=function(cb) callbacks.place=cb end,
    register_chatcommand=function(name, def) commands[name]=def end,
    chat_send_player=function() end,
    get_player_by_name=function(name) return players[name] end,
    get_meta=function(pos)
        local k=pos.x..","..pos.y..","..pos.z
        if not node_meta[k] then node_meta[k]=meta() end
        return node_meta[k]
    end,
    get_node_or_nil=function() return {name="xz_classic_props:barricade"} end,
    remove_node=function() end,
    after=function(_,cb) cb() end,
    log=function() end,
    get_modpath=function() return "mods/xz_classic_props" end,
    register_privilege=function() end,
    override_item=function(name,def)
        assert(nodes[name], "Override missing node: "..name)
        for k,v in pairs(def) do nodes[name][k]=v end
    end,
    register_lbm=function() end,
    register_entity=function() end,
    register_globalstep=function() end,
    register_on_dignode=function() end,
    register_on_respawnplayer=function() end,
    register_on_player_receive_fields=function() end,
    register_on_leaveplayer=function() end,
    register_craftitem=function() end,
    register_on_placenode=function(cb) callbacks.place=cb end,
    get_connected_players=function() return {} end,
    check_player_privs=function() return false end,
    is_singleplayer=function() return true end,
    deserialize=function() return {} end,
    serialize=function() return "{}" end,
    formspec_escape=function(x) return x end,
    pos_to_string=function(p) return p.x..","..p.y..","..p.z end,
    string_to_pos=function() return nil end,
    show_formspec=function() end,
    swap_node=function() end,
    set_node=function() end,
}
dofile("mods/xz_classic_props/init.lua")
local count=0
for _ in pairs(nodes) do count=count+1 end
assert(count==24, "24 nodes required, got " .. count)
local player=newplayer("tester")
for _,cb in ipairs(callbacks.join) do cb(player) end
local api=xz_classic_props
assert(api.get_points(player)==500)
local pos={x=0,y=0,z=0}
local function click(id)
    nodes["xz_classic_props:"..id].on_rightclick(pos, {}, player, {})
end
click("perk_vitality")
assert(api.get_points(player)==500, "no power / insufficient points must not charge")
click("power_switch")
assert(api.power_on())
click("wall_buy")
assert(api.get_points(player)==500, "missing AK must not charge")
click("mystery_box")
assert(api.get_points(player)==500, "missing arsenal must not charge")
assert(api.add_points(player, 10000))
click("perk_vitality")
assert(api.has_perk(player,"vitality"))
assert(player:get_properties().hp_max==40)
assert(api.get_points(player)==8000)
click("perk_vitality")
assert(api.get_points(player)==8000, "duplicate perk must not charge")
items["arsenal:ak47"]={groups={weapon=1}}
click("mystery_box")
assert(api.get_points(player)==7050)
assert(#player:get_inventory().list==1)
click("pack_a_punch")
assert(api.get_points(player)==2050)
assert(api.damage_multiplier(player,player:get_wielded_item())==2)
callbacks.die(player)
assert(not api.has_perk(player,"vitality"))
assert(player:get_properties().hp_max==20)
assert(api.get_points(player)==2050, "points persist through death")
print("PASS: 13 nodes / economy / power / perks / weapon award / upgrade / reset")
