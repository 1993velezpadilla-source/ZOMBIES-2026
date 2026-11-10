-- Dynamic third-person Wall Buy models for EVERY registered Arsenal weapon.
-- Uses existing private gun-only GLBs, never duplicates model/texture bytes.
-- Weapon selection continues to come from xz_classic_props.weapon_pool().
local core=minetest
local api=xz_classic_props

-- Pure, testable manifest validation. Refuse guessed meshes, hands models and paths.
function api.catalog_wall_models(manifest, items)
    local catalog={}
    if type(manifest)~="table" or manifest.schema_version~=1
        or type(manifest.weapons)~="table" then return catalog end
    for _,info in ipairs(manifest.weapons) do
        if type(info)=="table" and type(info.id)=="string"
            and info.id:match("^[a-z0-9_]+$")
            and info.gun_model=="arsenal_"..info.id.."_gun.glb"
            and info.hands_model=="arsenal_"..info.id.."_hands.glb" then
            local weapon="arsenal:"..info.id
            local definition=items[weapon]
            if definition and definition.groups
                and definition.groups.weapon==1 then
                catalog[weapon]=info.gun_model
            end
        end
    end
    return catalog
end

-- In the private Android build, Arsenal loads the exact same runtime manifest
-- and registers tools ONLY after verifying model files exist.
local function load_catalog()
    if not core.get_modpath or not core.parse_json then return {} end
    local folder=core.get_modpath("arsenal")
    if type(folder)~="string" or folder=="" then return {} end
    local file=io.open(folder.."/arsenal_runtime.json","rb")
    if not file then return {} end
    local raw=file:read("*a")
    file:close()
    if type(raw)~="string" or #raw>2*1024*1024 then return {} end
    local success,manifest=pcall(core.parse_json,raw)
    if not success then return {} end
    return api.catalog_wall_models(manifest,core.registered_items)
end

api.wall_models=load_catalog()
function api.wall_model_for(weapon)
    if type(weapon)~="string" then return nil end
    return api.wall_models[weapon]
end

core.log("action","[xz_classic_props] Verified 3D Wall Buy models: "..
    tostring((function()
        local n=0
        for _ in pairs(api.wall_models) do n=n+1 end
        return n
    end)()))
