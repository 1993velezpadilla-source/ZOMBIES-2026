-- Voxel Sandbox V2, build-your-own-map selection dialog.
-- This file runs in the Luanti main menu only, not in Survival gameplay.
-- Sizes are WIDTH x WIDTH interior buildable blocks; red walls are outside.
local ZMAP_SIZES = {
    {id = "xs",  label = "X Small",   width = 64},
    {id = "s",   label = "Small",     width = 128},
    {id = "m",   label = "Medium",    width = 256},
    {id = "l",   label = "Large",     width = 384},
    {id = "xl",  label = "X Large",   width = 512},
    {id = "xxl", label = "XX Large",  width = 768},
    {id = "xxxl",label = "XXX Large", width = 1024},
}

local function zmap_formspec(this)
    local s = "formspec_version[3]size[11,8]" ..
        "label[0.5,0.35;Create Map - Flat map templates]" ..
        "label[0.5,0.82;Pick a size. Red transparent boundaries are always enabled.]"
    for i, option in ipairs(ZMAP_SIZES) do
        local y = 1.3 + (i - 1) * 0.78
        s = s .. string.format("button[1.0,%.2f;9.0,0.67;zmap_size_%s;%s - %d x %d blocks]",
            y, option.id, option.label, option.width, option.width)
    end
    return s .. "button[3.3,7.15;4.4,0.58;zmap_cancel;Back]"
end

local function zmap_start_world(this, option)
    local game = pkgmgr.find_by_gameid("voxelibre")
    if not game then
        gamedata.errormessage = "VoxeLibre is missing; cannot create a map."
        this:delete()
        return true
    end

    local prefix = "Map " .. option.label .. " "
    local number = 1
    local worldname = prefix .. number
    while menudata.worldlist:uid_exists_raw(worldname) do
        number = number + 1
        worldname = prefix .. number
    end

    local message = core.create_world(worldname, game.id, {
        mg_name = "singlenode",
        mg_flags = "nocaves,nodungeons,nodecorations",
        fixed_map_seed = "42",
    })
    if message then
        gamedata.errormessage = message
        this:delete()
        return true
    end

    menudata.worldlist:set_filtercriteria(game.id)
    menudata.worldlist:refresh()
    local world_index = menudata.worldlist:raw_index_by_uid(worldname)
    local world = world_index and menudata.worldlist:get_raw_element(world_index)
    if not world or not world.path then
        gamedata.errormessage = "Created world but could not find its config. Please reopen."
        this:delete()
        return true
    end

    local conf = Settings(world.path .. DIR_DELIM .. "world.mt")
    conf:set("xz_map_template", "true")
    conf:set("xz_map_size", tostring(option.width))
    conf:set("creative_mode", "true")
    conf:set("enable_damage", "false")
    conf:set("enable_server", "false")
    conf:set("mg_name", "singlenode")
    if not conf:write() then
        gamedata.errormessage = "Could not save map boundaries in world.mt."
        this:delete()
        return true
    end

    core.settings:set("menu_last_game", game.id)
    core.settings:set_bool("creative_mode", true)
    core.settings:set_bool("enable_damage", false)
    core.settings:set_bool("enable_server", false)
    core.settings:set("mainmenu_last_selected_world", tostring(world_index))
    gamedata.selected_world = world_index
    gamedata.mode = "singleplayer"
    this:delete()
    core.start()
    return true
end

local function zmap_on_fields(this, fields)
    if fields.zmap_cancel or fields.key_escape then
        this:delete()
        return true
    end
    for _, option in ipairs(ZMAP_SIZES) do
        if fields["zmap_size_" .. option.id] then
            return zmap_start_world(this, option)
        end
    end
    return false
end

function create_zmap_world_dlg()
    return dialog_create("zmap_create_world", zmap_formspec, zmap_on_fields, nil)
end
