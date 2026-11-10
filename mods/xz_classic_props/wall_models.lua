-- Genuine FIX43 wall miniatures for all 28 installed weapons.
-- Generated gun-only GLBs (no first-person hands) are privately staged by the
-- Android build, never committed to the public repository.
local core=minetest
local api=xz_classic_props
local FIX43_IDS={
    ak74u=true,barrett=true,colt45=true,deserteagle=true,
    deserteaglegold=true,dragunov=true,g36c=true,g3=true,m1014=true,
    m14=true,m16=true,m21=true,m40a3=true,m4=true,m60e4=true,mp44=true,
    mp5=true,p90=true,remington700=true,rpd=true,rpg=true,saw=true,
    skorpion=true,usp=true,uzi=true,winchester1200=true,
}
local function expected(id)
    if id=="ak47dev:ak47" then return "ak47","ak47hd_rifle.png" end
    if id=="ak47dev:m9" then return "m9","m9hd_rifle.png" end
    local suffix=id:match("^cod4:([a-z0-9_]+)$")
    if suffix and FIX43_IDS[suffix] then
        return suffix,"a_"..suffix.."_shared.png"
    end
end

-- Pure validation used by Lua CI; never substitute a similarly named gun.
function api.catalog_wall_models(catalog,items)
    local verified={}
    if type(catalog)~="table" or catalog.schema_version~=1
        or type(catalog.models)~="table" then return verified end
    local used={}
    for item,record in pairs(catalog.models) do
        local id,texture=expected(item)
        local def=items[item]
        if id and type(record)=="table" and def and def.groups
            and def.groups.weapon==1
            and record.mesh=="xz_wall_"..id..".glb"
            and record.texture==texture
            and not used[record.mesh] then
            used[record.mesh]=true
            verified[item]={mesh=record.mesh,texture=texture}
        end
    end
    return verified
end

local function from_pack()
    if not core.get_modpath or not core.parse_json then return {} end
    local root=core.get_modpath("xz_classic_props")
    if type(root)~="string" or root=="" then return {} end
    local file=io.open(root.."/wall_models.json","rb")
    if not file then return {} end
    local raw=file:read("*a");file:close()
    if type(raw)~="string" or #raw>65536 then return {} end
    local ok,catalog=pcall(core.parse_json,raw)
    if not ok then return {} end
    local verified=api.catalog_wall_models(catalog,core.registered_items)
    local available={}
    for item,record in pairs(verified) do
        -- Require the exact model file to be physically shipped in the mod.
        local bin=io.open(root.."/models/"..record.mesh,"rb")
        if bin then
            local magic=bin:read(4);bin:close()
            if magic=="glTF" then available[item]=record end
        end
    end
    return available
end
api.wall_models=from_pack()
function api.wall_model_for(item)
    return type(item)=="string" and api.wall_models[item] or nil
end
local n=0
for _ in pairs(api.wall_models) do n=n+1 end
core.log("action","[xz_classic_props] Ready gun-only 3D Wall Buys: "..n.."/28")
