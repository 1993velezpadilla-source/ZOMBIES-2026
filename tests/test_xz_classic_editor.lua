-- Focused Lua 5.1 test of the editor, price saving and PLAY/STOP restoration.
local callbacks, nodes, items, players, node_meta = {}, {}, {}, {}, {}
local forms, messages, world = {}, {}, {}
local function key(p) return p.x..","..p.y..","..p.z end
local function meta()
    local ints, strings = {}, {}
    return {
        get_int=function(_,k) return ints[k] or 0 end,
        set_int=function(_,k,v) ints[k]=v end,
        get_string=function(_,k) return strings[k] or "" end,
        set_string=function(_,k,v) strings[k]=v end,
        to_table=function() return {fields={ints=ints,strings=strings}} end,
        from_table=function(_, t)
            ints=t.fields.ints
            strings=t.fields.strings
        end,
    }
end
local storage=meta()
local function node_meta_for(pos)
    local k=key(pos)
    if not node_meta[k] then node_meta[k]=meta() end
    return node_meta[k]
end
vector={new=function(p) return {x=p.x,y=p.y,z=p.z} end}
local function connected()
    local a={}
    for _,p in pairs(players) do a[#a+1]=p end
    return a
end
minetest={
    registered_items=items, registered_nodes=nodes,
    get_mod_storage=function() return storage end,
    get_modpath=function() return "mods/xz_classic_props" end,
    register_node=function(n,d) nodes[n]=d;items[n]=d end,
    register_craftitem=function(n,d) items[n]=d end,
    override_item=function(n,d)
        assert(nodes[n],n)
        for k,v in pairs(d) do nodes[n][k]=v end
    end,
    register_privilege=function() end,
    register_chatcommand=function() end,
    register_on_joinplayer=function(f) callbacks.join=f end,
    register_on_dieplayer=function(f) callbacks.die=f end,
    register_on_player_hpchange=function() end,
    register_on_placenode=function(f)
        callbacks.placed=callbacks.placed or {}
        table.insert(callbacks.placed,f)
    end,
    register_on_dignode=function() end,
    register_on_respawnplayer=function(f) callbacks.respawn=f end,
    register_on_player_receive_fields=function(f)
        callbacks.forms=callbacks.forms or {}
        table.insert(callbacks.forms,f)
    end,
    register_on_leaveplayer=function() end,
    register_lbm=function() end,
    register_entity=function(n,d) callbacks.entity=d end,
    register_globalstep=function(f) callbacks.globalstep=f end,
    check_player_privs=function() return false end,
    is_singleplayer=function() return true end,
    formspec_escape=function(s) return s end,
    show_formspec=function(n,f,s) forms[n]={name=f,text=s} end,
    explode_textlist_event=function(s)
        local a,b=s:match("^(%u+):(%d+)$")
        return {type=a,index=tonumber(b)}
    end,
    get_meta=node_meta_for,
    get_player_by_name=function(n) return players[n] end,
    get_connected_players=connected,
    get_node_or_nil=function(p) return world[key(p)] or {name="air",param2=0} end,
    set_node=function(p,n)
        world[key(p)]={name=n.name,param2=n.param2 or 0}
        node_meta[key(p)]=meta()
        if nodes[n.name] and nodes[n.name].on_construct then nodes[n.name].on_construct(p) end
    end,
    swap_node=function(p,n) world[key(p)]={name=n.name,param2=n.param2 or 0} end,
    remove_node=function(p) world[key(p)]=nil end,
    pos_to_string=key,
    string_to_pos=function(s)
        local x,y,z=s:match("^(-?%d+),(-?%d+),(-?%d+)$")
        if not x then return nil end
        return {x=tonumber(x),y=tonumber(y),z=tonumber(z)}
    end,
    deserialize=function() return {} end,
    serialize=function() return "serialized" end,
    chat_send_player=function(_,txt) messages[#messages+1]=txt end,
    after=function(_,f) f() end,
    log=function() end,
}
local p={name="maker",pos={x=0,y=1,z=0},hp=20,prop={hp_max=20},m=meta()}
local bag={list={}}
function bag:room_for_item() return true end
function bag:add_item(_,s) self.list[#self.list+1]=s end
function bag:get_list() return self.list end
function bag:set_list(_,v) self.list=v end
function p:is_player() return true end
function p:get_player_name() return self.name end
function p:get_meta() return self.m end
function p:get_inventory() return bag end
function p:get_pos() return self.pos end
function p:set_pos(pos) self.pos=pos end
function p:get_properties() return self.prop end
function p:set_properties(prop) self.prop.hp_max=prop.hp_max end
function p:get_hp() return self.hp end
function p:set_hp(v) self.hp=v end
function p:get_wielded_item()
    if not self.wield then
        self.wield={name="arsenal:ak47",m=meta()}
        function self.wield:get_name() return self.name end
        function self.wield:get_meta() return self.m end
    end
    return self.wield
end
function p:set_wielded_item(v) self.wield=v end
players[p.name]=p

items["arsenal:ak47"]={description="AK-47",groups={weapon=1}}
items["arsenal:m9"]={description="M9",groups={weapon=1}}

dofile("mods/xz_classic_props/init.lua")
local api=xz_classic_props
callbacks.join(p)
assert(api.get_points(p)==500)
local function place(pos,id)
    minetest.set_node(pos,{name="xz_classic_props:"..id})
    for _,f in ipairs(callbacks.placed or {}) do
        f(pos,{name="xz_classic_props:"..id})
    end
    local def=nodes["xz_classic_props:"..id]
    if def.after_place_node then def.after_place_node(pos,p) end
end
local function submit(name,fields)
    for _,f in ipairs(callbacks.forms) do f(p,name,fields) end
end
local wall={x=1,y=1,z=0}
place(wall,"wall_buy")
assert(forms.maker.name=="xzcp:choose_wall_weapon","placing wall opens weapon selector")
submit("xzcp:choose_wall_weapon",{weapons="CHG:2"})
assert(forms.maker.name=="xzcp:set_wall_price","choose weapon triggers price dialog")
submit("xzcp:set_wall_price",{save_wall=true,price="1450"})
assert(minetest.get_meta(wall):get_int("price")==1450)
assert(minetest.get_meta(wall):get_string("weapon")=="arsenal:m9")
assert(api.get_points(p)==500,"editing must not charge points")
local door={x=2,y=1,z=0}
place(door,"buyable_door")
assert(forms.maker.name=="xzcp:set_door_price")
submit("xzcp:set_door_price",{save_door=true,price="750"})
assert(minetest.get_meta(door):get_int("price")==750)
assert(api.get_points(p)==500)

local playerSpawn={x=3,y=0,z=1}
local zombieSpawn={x=-3,y=0,z=1}
local barrier={x=5,y=1,z=0}
local light={x=6,y=1,z=0}
place(playerSpawn,"player_spawn_marker")
place(zombieSpawn,"zombie_spawn_marker")
place(barrier,"utility_barrier")
place(light,"utility_light_14")
assert(api.add_points(p,4500))
local initial=api.get_points(p)
assert(initial==5000)
assert(api.start_test(p))
assert(not api.is_editing())
assert(minetest.get_node_or_nil(zombieSpawn).name=="xz_classic_props:zombie_spawn_marker_hidden")
assert(minetest.get_node_or_nil(playerSpawn).name=="xz_classic_props:player_spawn_marker_hidden")
assert(minetest.get_node_or_nil(barrier).name=="xz_classic_props:utility_barrier_hidden")
assert(nodes["xz_classic_props:utility_barrier_hidden"].walkable==true)
assert(nodes["xz_classic_props:utility_light_14_hidden"].light_source==14)
assert(p.pos.x==3 and p.pos.y==1.5,"PLAY should move player to selected marker")
nodes["xz_classic_props:wall_buy"].on_rightclick(wall,{},p,{})
assert(api.get_points(p)==3550)
assert(#bag.list==1 and bag.list[1]=="arsenal:m9")
nodes["xz_classic_props:buyable_door"].on_rightclick(door,{},p,{})
assert(api.get_points(p)==2800 and minetest.get_node_or_nil(door).name=="air")
assert(api.stop_test(p))
assert(api.is_editing())
assert(minetest.get_node_or_nil(zombieSpawn).name=="xz_classic_props:zombie_spawn_marker")
assert(minetest.get_node_or_nil(barrier).name=="xz_classic_props:utility_barrier")
assert(minetest.get_node_or_nil(door).name=="xz_classic_props:buyable_door")
assert(minetest.get_meta(door):get_int("price")==750)
assert(api.get_points(p)==initial,"STOP should restore points")
assert(#bag.list==0,"STOP should restore original inventory")
assert(p.pos.x==0 and p.pos.y==1,"STOP should restore original position")
print("PASS: maker wall selector, custom prices, player spawn, marker hiding, barrier collision and PLAY/STOP rollback")
