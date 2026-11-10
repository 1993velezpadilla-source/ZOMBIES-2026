-- Focused Lua 5.1 test of the editor, price saving and PLAY/STOP restoration.
local callbacks, nodes, items, players, node_meta = {}, {}, {}, {}, {}
local forms, messages, world, spawned, previews = {}, {}, {}, {}, {}
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
    register_on_joinplayer=function(f)
        callbacks.join=callbacks.join or {}
        table.insert(callbacks.join,f)
    end,
    register_on_dieplayer=function(f) callbacks.die=f end,
    register_on_player_hpchange=function(f)
        callbacks.hp=callbacks.hp or {}
        table.insert(callbacks.hp,f)
    end,
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
    register_entity=function(n,d)
        callbacks.entities=callbacks.entities or {}
        callbacks.entities[n]=d
    end,
    register_globalstep=function(f)
        callbacks.globalsteps=callbacks.globalsteps or {}
        table.insert(callbacks.globalsteps,f)
    end,
    add_entity=function(pos,id)
        assert(callbacks.entities[id],"unregistered test entity: "..id)
        local ref={pos=pos,valid=true,velocity={x=0,y=0,z=0}}
        function ref:is_valid() return self.valid end
        function ref:get_luaentity() return self.entity end
        function ref:set_yaw(v) self.yaw=v end
        function ref:set_properties(props) for k,v in pairs(props) do self[k]=v end end
        function ref:set_hp(h) self.hp=h end
        function ref:set_acceleration(accel) self.accel=accel end
        function ref:get_pos() return self.pos end
        function ref:get_velocity() return self.velocity end
        function ref:set_velocity(vel) self.velocity=vel end
        function ref:remove()
            if not self.valid then return end
            self.valid=false
            if self.entity.on_deactivate then self.entity:on_deactivate() end
        end
        local entity=setmetatable({object=ref,name=id},{__index=callbacks.entities[id]})
        ref.entity=entity
        entity:on_activate("")
        if id=="xz_classic_props:wall_weapon_preview" then
            previews[#previews+1]=ref
        else
            spawned[#spawned+1]=ref
        end
        return ref
    end,

    check_player_privs=function() return false end,
    facedir_to_dir=function() return {x=0,y=0,z=-1} end,
    dir_to_yaw=function() return 0 end,
    is_protected=function() return false end,
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
    get_node=function(p) return world[key(p)] or {name="air",param2=0} end,
    get_objects_inside_radius=function(pos,radius)
        local objects={}
        for _,obj in ipairs(previews) do
            if obj:is_valid() then
                local xyz=obj:get_pos()
                local dx,dy,dz=xyz.x-pos.x,xyz.y-pos.y,xyz.z-pos.z
                if dx*dx+dy*dy+dz*dz <=radius*radius then objects[#objects+1]=obj end
            end
        end
        return objects
    end,
    set_node=function(p,n)
        world[key(p)]={name=n.name,param2=n.param2 or 0}
        node_meta[key(p)]=meta()
        if nodes[n.name] and nodes[n.name].on_construct then nodes[n.name].on_construct(p) end
    end,
    swap_node=function(p,n) world[key(p)]={name=n.name,param2=n.param2 or 0} end,
    remove_node=function(p)
        local n=world[key(p)]
        if n and nodes[n.name] and nodes[n.name].on_destruct then
            nodes[n.name].on_destruct(p)
        end
        world[key(p)]=nil
    end,
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

items["air"]={buildable_to=true}
nodes["air"]=items["air"]
items["arsenal:ak47"]={description="AK-47",groups={weapon=1}}
items["arsenal:m9"]={description="M9",groups={weapon=1}}

dofile("mods/xz_classic_props/init.lua")
local api=xz_classic_props
for _,cb in ipairs(callbacks.join) do cb(p) end
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
assert(#previews==1 and previews[1]:is_valid(),"miniature floating weapon must appear")
assert(previews[1].textures[1]=="arsenal:m9","preview uses actual Arsenal item visual")
assert(api.get_points(p)==500,"editing must not charge points")
local door={x=2,y=1,z=0}
place(door,"buyable_door")
assert(forms.maker.name=="xzcp:set_door_price")
submit("xzcp:set_door_price",{save_door=true,price="750"})
assert(minetest.get_meta(door):get_int("price")==750)
assert(api.get_points(p)==500)
local box={x=-2,y=1,z=0}
place(box,"mystery_box")
local box2={x=-1,y=1,z=0}
assert(minetest.get_node(box2).name=="xz_classic_props:mystery_box_right",
    "Mystery Crate must occupy two wood blocks")
assert(minetest.get_meta(box2):get_string("origin")==key(box))

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
assert(api.wave_status().pending==6,"Round 1 should queue six zombies")
assert(bag.list[1]=="xz_classic_props:developer_tool","Developer touch hotbar tool granted in PLAY")
submit("xzcp:editor",{developer=true})
assert(forms.maker.name=="xzcp:developer","developer button should be visible in PLAY")
submit("xzcp:developer",{points_1000=true})
assert(api.get_points(p)==6000,"developer grants point money")
submit("xzcp:developer",{health=true})
assert(api.developer_flags(p).health,"infinite health toggle")
local damage=-10
for _,cb in ipairs(callbacks.hp) do
    local result=cb(p,damage)
    if type(result)=="number" then damage=result end
end
assert(damage==0,"god mode prevents damage")
submit("xzcp:developer",{ammo=true})
assert(api.developer_flags(p).ammo)
local gunstack=p:get_wielded_item()
for _,f in ipairs(callbacks.globalsteps) do f(0.3) end
assert(gunstack:get_meta():get_int("ar_clip")==999,"developer ammo refills Arsenal clip")
submit("xzcp:developer",{choose_weapon=true})
assert(forms.maker.name=="xzcp:developer_weapons","developer weapon selector opens")
submit("xzcp:developer_weapons",{weapons="CHG:1"})
assert(#bag.list>=2,"developer can choose weapon")
p.m:set_int("xzcp:points",5000) -- isolate original combat purchases

for _,f in ipairs(callbacks.globalsteps) do f(1.1) end
assert(#spawned==1,"marked zombie spawner must produce an enemy")
assert(api.wave_status().alive==1)
local beforeHit=api.get_points(p)
for _=1,3 do
    spawned[1].entity:on_punch(p,0,{damage_groups={fleshy=40}},nil,40)
end
assert(api.wave_status().alive==0,"zombie is killed by source weapon damage")
assert(api.get_points(p)>beforeHit,"hits and kill must award points")
p.m:set_int("xzcp:points",5000) -- isolate purchase calculations after combat

nodes["xz_classic_props:wall_buy"].on_rightclick(wall,{},p,{})
assert(api.get_points(p)==3550)
assert(bag.list[#bag.list]=="arsenal:m9","wall buy awards selected M9 weapon")
nodes["xz_classic_props:buyable_door"].on_rightclick(door,{},p,{})
assert(api.get_points(p)==2800 and minetest.get_node_or_nil(door).name=="air")
nodes["xz_classic_props:mystery_box_right"].on_rightclick(box2,{},p,{})
assert(api.get_points(p)==1850,"both halves of Mystery Crate must award a weapon for 950 points")

assert(api.stop_test(p))
assert(not api.wave_status().active)
assert(not api.developer_flags(p).health and not api.developer_flags(p).ammo,"developer flags OFF after STOP")
assert(api.is_editing())
assert(minetest.get_node_or_nil(zombieSpawn).name=="xz_classic_props:zombie_spawn_marker")
assert(minetest.get_node_or_nil(barrier).name=="xz_classic_props:utility_barrier")
assert(minetest.get_node_or_nil(door).name=="xz_classic_props:buyable_door")
assert(minetest.get_meta(door):get_int("price")==750)
assert(api.get_points(p)==initial,"STOP should restore points")
assert(#bag.list==0,"STOP should restore original inventory")
assert(p.pos.x==0 and p.pos.y==1,"STOP should restore original position")
items["xz_classic_props:map_editor"].on_use({},p)
assert(forms.maker.name=="xzcp:editor","editor item opens play/edit panel")
submit("xzcp:editor",{open_blocks=true})
assert(forms.maker.name=="xzcp:blocks","editor opens categorized block catalog")
submit("xzcp:blocks",{cat_purchases=true})
assert(forms.maker.text:find("WALL BUY") or forms.maker.text:find("Wall Buy"))
submit("xzcp:blocks",{give_wall_buy=true})
assert(bag.list[1]=="xz_classic_props:wall_buy","catalog should give requested block")
local catalog={schema_version=1,models={}}
local ids={"cod4:ak74u","cod4:barrett","cod4:colt45","cod4:deserteagle","cod4:deserteaglegold","cod4:dragunov","cod4:g36c","cod4:g3","cod4:m1014","cod4:m14","cod4:m16","cod4:m21","cod4:m40a3","cod4:m4","cod4:m60e4","cod4:mp44","cod4:mp5","cod4:p90","cod4:remington700","cod4:rpd","cod4:rpg","cod4:saw","cod4:skorpion","cod4:usp","cod4:uzi","cod4:winchester1200","ak47dev:ak47","ak47dev:m9"}
for _,name in ipairs(ids) do
    local id=name:match(":(.*)$")
    local tex=name:match("^cod4:") and "a_"..id.."_shared.png"
        or id=="ak47" and "ak47hd_rifle.png" or "m9hd_rifle.png"
    items[name]={description=name,groups={weapon=1}}
    catalog.models[name]={mesh="xz_wall_"..id..".glb",texture=tex}
end
assert(nodes["xz_classic_props:wall_buy"].walkable==false)
assert(nodes["xz_classic_props:wall_buy"].drawtype=="nodebox")
local all_models=api.catalog_wall_models(catalog,items)
local n=0
for _ in pairs(all_models) do n=n+1 end
assert(n==28,"Exactly 28 registered real gun-only 3D Wall Buy models")
api.wall_models=all_models
local pool=api.weapon_pool()
assert(#pool>=28,"Real cod4 weapons should appear in Wall Buy picker")
for _,name in ipairs(ids) do
    local id=name:match(":(.*)$")
    minetest.get_meta(wall):set_string("weapon",name)
    assert(api.refresh_wall_preview(wall,p),"3D mini must appear: "..name)
    local obj=previews[#previews]
    assert(obj:is_valid() and obj.visual=="mesh","not a 3D mesh: "..name)
    assert(obj.mesh=="xz_wall_"..id..".glb","wrong real gun mesh: "..name)
    assert(obj.textures[1]==catalog.models[name].texture,"wrong gun atlas: "..name)
    assert(obj.visual_size.x==1,"baked model needs normalized scale")
end
items["custom:gun"]={description="Custom gun",groups={weapon=1}}
minetest.get_meta(wall):set_string("weapon","custom:gun")
assert(api.refresh_wall_preview(wall,p))
assert(previews[#previews].visual=="wielditem" and previews[#previews].textures[1]=="custom:gun")
local fake={schema_version=1,models={["cod4:m4"]={mesh="xz_wall_ak47.glb",texture="a_m4_shared.png"}}}
assert(next(api.catalog_wall_models(fake,items))==nil,"Reject mismatched model")
print("PASS: 28 actual FIX43 gun-only mini meshes mapped to own weapon and texture")
print("PASS: maker wall selector, custom prices, player spawn, marker hiding, barrier collision and PLAY/STOP rollback")
