-- Genuine COD4 source-based attachments for the Android Arsenal test bridge.
-- This is a TOUCH UI, not a chat-only command. Only switch to GLB variants
-- extracted from real owner-supplied COD4 viewmodels with source animations.
local M={}
local IDS={"reflex","acog","silencer","gp25"}
local LABELS={
    reflex="Reflex / Red dot",acog="ACOG 4x",
    silencer="Suppressor",gp25="GP-25 / launcher mount"
}
local function part_set(variant)
    local parts={}
    for id in (variant or ""):gmatch("[a-z0-9]+") do
        if LABELS[id] then parts[id]=true end
    end
    return parts
end
local function encode(parts)
    local result={}
    for _,id in ipairs(IDS) do
        if parts[id] then result[#result+1]=id end
    end
    return table.concat(result,"_")
end
local function owns_source_variant(def,id)
    local available=def.source_attachment_models or {}
    for variant in pairs(available) do
        if part_set(variant)[id] then return true end
    end
    return false
end

function M.register(defs,state)
    local previous={}
    local function find_target(player)
        if not player or not player:is_player() then return nil,nil,nil end
        local inv=player:get_inventory()
        local equipped=player:get_wielded_item():get_name()
        local selected=state(player).last_weapon or ""
        if defs[equipped] then selected=defs[equipped].id end
        -- If the legacy AK was held, prefer the source-backed AK's original
        -- model variants. Never mutate the legacy AK V8 gun behind the scenes.
        if equipped=="ak47dev:ak47" and defs["arsenal:ak47"] then selected="ak47" end
        if selected=="" then
            for _,id in ipairs({"m9","ak47","m4"}) do
                if defs["arsenal:"..id] and
                   inv:contains_item("main","arsenal:"..id) then
                    selected=id;break
                end
            end
        end
        if not defs["arsenal:"..selected] then return nil,nil,nil end
        for i=1,inv:get_size("main") do
            local stack=inv:get_stack("main",i)
            if stack:get_name()=="arsenal:"..selected then
                return defs["arsenal:"..selected],stack,i
            end
        end
        return nil,nil,nil
    end
    local function form(player)
        local def,stack=find_target(player)
        local f={
            "formspec_version[4]size[11.0,7.9]",
            "bgcolor[#0C1420;true]",
            "label[.45,.35;COD4 ORIGINAL ATTACHMENTS]",
            "label[.45,.95;Only verified native source-model combinations are selectable.]",
        }
        if not def then
            f[#f+1]="label[.65,2;Equip an Arsenal weapon first, then tap ATTACH.]"
        else
            local esc=minetest.formspec_escape
            local selected=stack:get_meta():get_string("xz_ar_variant")
            local set=part_set(selected)
            f[#f+1]="label[.5,1.48;"..esc(def.name).."]"
            local y=2.05
            local count=0
            for _,id in ipairs(IDS) do
                if owns_source_variant(def,id) then
                    count=count+1
                    f[#f+1]=("checkbox[.7,%.2f;att_%s;%s;%s]"):format(
                        y,id,esc(LABELS[id]),tostring(set[id] or false))
                    y=y+.93
                end
            end
            if count==0 then
                f[#f+1]="label[.65,2.9;No original verified 3D attachments for this weapon.]"
            end
            f[#f+1]="label[.55,6.52;Optic + muzzle combinations need an original matching 3D model.]"
            f[#f+1]="button[.55,7.05;4,.57;reset;IRON SIGHTS / NONE]"
        end
        f[#f+1]="button_exit[7,7.05;3.5,.57;close;BACK]"
        local who=player:get_player_name()
        minetest.show_formspec(who,"arsenal:attachments",table.concat(f))
    end
    local function choose(player,fields)
        local def,stack,index=find_target(player)
        if not def then return false end
        local meta=stack:get_meta()
        local parts=part_set(meta:get_string("xz_ar_variant"))
        local wanted
        if fields.reset then wanted="" end
        for _,id in ipairs(IDS) do
            local value=fields["att_"..id]
            if value=="true" or value=="false" then
                if not owns_source_variant(def,id) then return false end
                if id=="acog" and value=="true" then parts.reflex=nil end
                if id=="reflex" and value=="true" then parts.acog=nil end
                parts[id]=value=="true" or nil
                wanted=encode(parts)
                break
            end
        end
        if wanted==nil then return false end
        if wanted~="" and not (def.source_attachment_models or {})[wanted] then
            minetest.chat_send_player(player:get_player_name(),
                "That combination has no original COD4 GLB. Keeping the previous attachments.")
            return false
        end
        meta:set_string("xz_ar_variant",wanted)
        player:get_inventory():set_stack("main",index,stack)
        previous[player:get_player_name()]=def.id
        return true
    end
    minetest.register_craftitem("arsenal:attach_tool",{
        description="ATTACH - ORIGINAL COD4 ACCESSORIES (TAP FIRE)",
        inventory_image="arsenal_attach.png",
        stack_max=1,
        on_use=function(itemstack,user)
            form(user)
            return itemstack
        end
    })
    minetest.register_on_player_receive_fields(function(player,name,fields)
        if name~="arsenal:attachments" or not player or
                not player:is_player() then return false end
        if not fields.quit and not fields.close then
            choose(player,fields)
            form(player)
        end
        return true
    end)
    return {open=form,choose=choose,find_target=find_target}
end
return M
