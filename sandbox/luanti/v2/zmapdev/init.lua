-- Voxel Sandbox V2 private map construction mode.
-- Runs only in worlds explicitly created with "Create Map", leaving Survival
-- worlds untouched. Terrain is generated lazily around the player by mapchunk.
local settings = Settings(minetest.get_worldpath() .. "/world.mt")
local enabled = settings:get("xz_map_template") == "true"
local SIZE = tonumber(settings:get("xz_map_size"))
if not enabled or not SIZE then
    return
end

local valid = { [64]=true, [128]=true, [256]=true, [384]=true,
    [512]=true, [768]=true, [1024]=true }
if not valid[SIZE] then
    minetest.log("error", "[zmapdev] Invalid template width: " .. tostring(SIZE))
    return
end

-- For all sizes the interior has exactly SIZE * SIZE buildable cells.
local inner_min = -math.floor(SIZE / 2)
local inner_max = inner_min + SIZE - 1
local outer_min = inner_min - 1
local outer_max = inner_max + 1

local GROUND_TOP = 0
local GROUND_BOTTOM = -5
local WALL_HEIGHT = 48

minetest.register_node("zmapdev:red_boundary", {
    description = "Map Boundary (Developer Only)",
    drawtype = "glasslike",
    tiles = {"zmapdev_red_boundary.png"},
    use_texture_alpha = "blend",
    paramtype = "light",
    sunlight_propagates = true,
    walkable = true,
    pointable = false,
    diggable = false,
    drop = "",
    groups = {not_in_creative_inventory = 1, unbreakable = 1},
})

-- VoxeLibre's standard nodes are reused. New templates do not replace any
-- default survival assets or add zombies, spawning, weapons or map exports.
minetest.register_on_generated(function(minp, maxp)
    if maxp.y < GROUND_BOTTOM or minp.y > WALL_HEIGHT then return end
    if maxp.x < outer_min or minp.x > outer_max
        or maxp.z < outer_min or minp.z > outer_max then return end

    local minx, maxx = math.max(minp.x, outer_min), math.min(maxp.x, outer_max)
    local minz, maxz = math.max(minp.z, outer_min), math.min(maxp.z, outer_max)

    local vm, emin, emax = minetest.get_mapgen_object("voxelmanip")
    if not vm then
        minetest.log("error", "[zmapdev] on_generated: no VoxelManip object")
        return
    end
    local area = VoxelArea:new({MinEdge = emin, MaxEdge = emax})
    local data = vm:get_data()

    local c_grass = minetest.get_content_id("mcl_core:dirt_with_grass")
    local c_dirt = minetest.get_content_id("mcl_core:dirt")
    local c_bedrock = minetest.get_content_id("mcl_core:bedrock")
    local c_boundary = minetest.get_content_id("zmapdev:red_boundary")

    for z = minz, maxz do
        for x = minx, maxx do
            local on_edge = x == outer_min or x == outer_max
                or z == outer_min or z == outer_max
            if on_edge then
                -- A red physical wall from y=1 to 48, with server-side horizontal
                -- clamping so flying above it cannot escape the template.
                for y = math.max(1, minp.y), math.min(WALL_HEIGHT, maxp.y) do
                    data[area:index(x, y, z)] = c_boundary
                end
            else
                -- Four layers of dirt, grass surface and unbreakable bedrock.
                for y = math.max(GROUND_BOTTOM, minp.y), math.min(GROUND_TOP, maxp.y) do
                    local node = y == 0 and c_grass
                        or (y == GROUND_BOTTOM and c_bedrock or c_dirt)
                    data[area:index(x, y, z)] = node
                end
            end
        end
    end

    vm:set_data(data)
    vm:write_to_map()
end)

local function in_bounds(p)
    return p.x >= inner_min + 0.3 and p.x <= inner_max + 0.7
        and p.z >= inner_min + 0.3 and p.z <= inner_max + 0.7
end

local function clamp(v, low, high)
    return math.max(low, math.min(high, v))
end

-- A physical wall isn't enough when Creative flight can go over/under it.
-- Keep a cheap server-side horizontal fence, checking at 5 Hz.
local elapsed = 0
minetest.register_globalstep(function(dtime)
    elapsed = elapsed + dtime
    if elapsed < 0.2 then return end
    elapsed = 0
    for _, player in ipairs(minetest.get_connected_players()) do
        local p = player:get_pos()
        if p and not in_bounds(p) then
            p.x = clamp(p.x, inner_min + 0.3, inner_max + 0.7)
            p.z = clamp(p.z, inner_min + 0.3, inner_max + 0.7)
            player:set_pos(p)
        end
    end
end)

local function ensure_starting_area(player)
    -- Emerge before teleport so the player never falls into ungenerated air.
    local name = player:get_player_name()
    local once = false
    minetest.emerge_area({x=-8,y=-8,z=-8}, {x=8,y=8,z=8},
        function(_, _, remaining)
            if remaining ~= 0 or once then return end
            once = true
            minetest.after(0.1, function()
                local connected = minetest.get_player_by_name(name)
                if connected then
                    local pos = connected:get_pos()
                    if not pos or math.abs(pos.x) < 30 and math.abs(pos.z) < 30 then
                        connected:set_pos({x=0, y=3, z=0})
                    end
                end
            end)
        end)
end

minetest.register_on_newplayer(function(player)
    ensure_starting_area(player)
end)

minetest.register_on_joinplayer(function(player)
    local p = player:get_pos()
    if p and not in_bounds(p) then
        player:set_pos({x=0, y=3, z=0})
    end
end)

minetest.log("action", "[zmapdev] Creative map " .. SIZE .. "x" .. SIZE ..
    " loaded: red visible boundaries, flat ground, no editor spawns")
