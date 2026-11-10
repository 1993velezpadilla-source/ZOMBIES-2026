-- Original Zombies world decorations. Gun-only GLB wall previews are dynamically
-- selected from the registered Arsenal manifest. Never copy or substitute AK meshes.
local core=minetest
local api=xz_classic_props
local preview_name="xz_classic_props:wall_weapon_preview"
local left_name="xz_classic_props:mystery_box"
local right_name="xz_classic_props:mystery_box_right"

core.register_entity(preview_name,{
    initial_properties={
        physical=false,
        pointable=false,
        collide_with_objects=false,
        visual="wielditem",
        textures={"air"},
        visual_size={x=0.48,y=0.48},
        static_save=false,
    },
    on_activate=function(self, static)
        self.wall_key=static or ""
        -- Per-instance display data is set by the owning Wall Buy node.
    end,
})

local function find_preview(pos)
    if not core.get_objects_inside_radius then return {} end
    local found={}
    for _,obj in ipairs(core.get_objects_inside_radius(pos,1.2)) do
        local lua=obj.get_luaentity and obj:get_luaentity()
        if lua and lua.name==preview_name and lua.wall_key==core.pos_to_string(pos) then
            found[#found+1]=obj
        end
    end
    return found
end
local function offset(node,player)
    local facing
    if core.facedir_to_dir then facing=core.facedir_to_dir(node.param2 or 0) end
    if not facing or math.abs(facing.y or 0)>0.4 then
        facing=player and player.get_look_dir and player:get_look_dir() or {x=0,y=0,z=-1}
    end
    local x,z=facing.x or 0,facing.z or 0
    local d=math.sqrt(x*x+z*z)
    if d<0.1 then return 0, -1 end
    return x/d,z/d
end

-- Rebuild only on configuration/placement or node load; no per-frame map scanning.
function api.refresh_wall_preview(pos,player)
    for _,obj in ipairs(find_preview(pos)) do obj:remove() end
    local n=core.get_node_or_nil(pos)
    if not n or n.name~="xz_classic_props:wall_buy" then return false end
    local id=core.get_meta(pos):get_string("weapon")
    local def=core.registered_items[id]
    if not def or not def.groups or def.groups.weapon~=1 then return false end
    local dx,dz=offset(n,player)
    local at={x=pos.x+dx*0.69,y=pos.y+0.12,z=pos.z+dz*0.69}
    local obj=core.add_entity(at,preview_name)
    if not obj then return false end
    local lua=obj:get_luaentity()
    if lua then lua.wall_key=core.pos_to_string(pos) end
    local mesh = api.wall_model_for and api.wall_model_for(id)
    if mesh then
        -- The already-installed Arsenal mod provides one unique gun-only GLB
        -- per weapon (no FPS arms). The native client GLB loader handles it.
        -- Source guns can contain many separate mesh/material buffers.
        -- The verified Arsenal supplies this material for every gun buffer.
        local materials={}
        for i=1,64 do materials[i]="arsenal_flat_metal.png" end
        obj:set_properties({
            visual="mesh", mesh=mesh,
            textures=materials,
            visual_size={x=0.10,y=0.10,z=0.10},
            physical=false,pointable=false,collide_with_objects=false,
            makes_footstep_sound=false,
        })
        -- Display an unmoving source mesh; avoid playing full FPS animations.
        if obj.set_animation then
            obj:set_animation({x=0,y=0},0,0,false)
        end
    else
        -- Never use a different gun (especially the AK) as a substitute.
        -- A legacy item with no source model retains its OWN icon as fallback.
        obj:set_properties({
            visual="wielditem",textures={id},visual_size={x=0.44,y=0.44},
            physical=false,pointable=false,collide_with_objects=false,
        })
    end
    if core.dir_to_yaw then obj:set_yaw(core.dir_to_yaw({x=dx,y=0,z=dz}) + math.pi/2) end
    return true
end
core.override_item("xz_classic_props:wall_buy",{
    -- A thin non-solid mount instead of a giant machine block.
    -- The entity is the visible gun, the mount is the click target.
    drawtype="nodebox",
    node_box={type="fixed",fixed={-0.41,-0.23,0.435,0.41,0.23,0.49}},
    selection_box={type="fixed",fixed={-0.49,-0.38,-0.5,0.49,0.38,0.5}},
    collision_box={type="fixed",fixed={0,0,0,0,0,0}},
    walkable=false,
    pointable=true,
    sunlight_propagates=true,
    tiles={"xzcp_wall_buy.png"},
    inventory_image="xzcp_wall_buy.png",
    wield_image="xzcp_wall_buy.png",
    on_destruct=function(pos)
        for _,obj in ipairs(find_preview(pos)) do obj:remove() end
    end,
})
core.register_lbm({
    name="xz_classic_props:wall_preview_restore",
    nodenames={"xz_classic_props:wall_buy"},
    run_at_every_load=true,
    action=function(pos)
        -- A static_save=false entity is recreated every time the map loads.
        api.refresh_wall_preview(pos)
    end,
})

-- Original two-block mystery crate, NOT a VoxeLibre storage chest.
-- It charges 950 points and delivers a random weapon, with no inventory GUI.
core.register_node(right_name,{
    description="Mystery Crate - Right Half (INTERNAL)",
    drawtype="normal",
    tiles={"xzcp_crate_wood.png"},
    paramtype="light",
    paramtype2="facedir",
    groups={not_in_creative_inventory=1},
    diggable=false,
    drop="",
    on_rightclick=function(pos,node,player,stack)
        local link=core.get_meta(pos):get_string("origin")
        local other=core.string_to_pos(link or "")
        if other and core.get_node_or_nil(other)
            and core.get_node_or_nil(other).name==left_name then
            local def=core.registered_nodes[left_name]
            if def and def.on_rightclick then
                return def.on_rightclick(other,core.get_node(other),player,stack)
            end
        end
        api.tell(player,"Mystery Crate is missing its main half.")
        return stack
    end,
})

local function mate(pos,node)
    -- Four horizontal rotations; adjacent half sits on the right side of the chest.
    local sides={{x=1,z=0},{x=0,z=-1},{x=-1,z=0},{x=0,z=1}}
    local side=sides[((node.param2 or 0)%4)+1]
    return {x=pos.x+side.x,y=pos.y,z=pos.z+side.z}
end

core.override_item(left_name,{
    drawtype="normal",
    tiles={"xzcp_crate_wood.png","xzcp_crate_wood.png",
        "xzcp_crate_wood.png","xzcp_crate_wood.png",
        "xzcp_crate_wood.png","xzcp_mystery_box.png"},
    paramtype2="facedir",
    after_place_node=function(pos,player)
        local n=core.get_node_or_nil(pos)
        if not n then return end
        local second=mate(pos,n)
        local node=core.get_node_or_nil(second)
        if not node or not core.registered_nodes[node.name]
            or not core.registered_nodes[node.name].buildable_to
            or (core.is_protected and player
                and core.is_protected(second,player:get_player_name())) then
            api.tell(player,"Need one free adjacent block for the double Mystery Crate.")
            return
        end
        core.set_node(second,{name=right_name,param2=n.param2})
        core.get_meta(second):set_string("origin",core.pos_to_string(pos))
    end,
    on_destruct=function(pos)
        local n=core.get_node_or_nil(pos)
        if not n then return end
        local other=mate(pos,n)
        local node=core.get_node_or_nil(other)
        if node and node.name==right_name and
            core.get_meta(other):get_string("origin")==core.pos_to_string(pos) then
            core.remove_node(other)
        end
    end,
})

-- Reuse the game's existing mob spawner cage texture for the EDIT marker only.
-- Do not use the built-in spawner's independent mob spawning timer.
if core.registered_nodes["xz_classic_props:zombie_spawn_marker"] then
    core.override_item("xz_classic_props:zombie_spawn_marker",{
        tiles={"mob_spawner.png"},
        description="Zombie Spawn (EDITOR - disappears in PLAY)",
    })
end
