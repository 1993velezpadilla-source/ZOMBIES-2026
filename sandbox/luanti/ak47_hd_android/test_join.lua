-- Reproduce the delayed join callback using only real Luanti player methods.
-- Inventory stacks are copies, as returned by InvRef, with metadata preserved.
local AK="ak47dev:ak47"
local function stack(name,tag)
    local s={name=name or "",tag=tag or "",values={}}
    function s:get_name() return self.name end
    function s:get_meta()
        return {set_string=function(_,k,v) self.values[k]=v end}
    end
    return s
end
local function copy(s)
    local result=stack(s.name,s.tag)
    for k,v in pairs(s.values) do result.values[k]=v end
    return result
end
local function scenario(items,selected,connected)
    local callbacks,inventory={},{}
    for i,item in ipairs(items) do inventory[i]=copy(item) end
    local inv={}
    function inv:get_size(list) assert(list=="main");return #inventory end
    function inv:get_stack(list,i) assert(list=="main");return copy(assert(inventory[i])) end
    function inv:set_stack(list,i,s) assert(list=="main");assert(inventory[i]);inventory[i]=copy(s) end
    function inv:contains_item(list,name)
        assert(list=="main")
        for _,s in ipairs(inventory) do if s.name==name then return true end end
        return false
    end
    function inv:add_item(list,name)
        assert(list=="main")
        for i,s in ipairs(inventory) do
            if s.name=="" then inventory[i]=stack(name);return stack() end
        end
        return stack(name)
    end
    local player={}
    function player:is_player() return true end
    function player:get_player_name() return "join_test" end
    function player:get_inventory() return inv end
    function player:get_wield_index() return selected end
    function player:get_wielded_item() return copy(inventory[selected]) end
    function player:set_wielded_item(s) inventory[selected]=copy(s);return true end
    function player:hud_add() return 1 end
    function player:hud_change() end
    -- No set_wield_index stub: that method does not exist in the engine.
    minetest={
        get_us_time=function() return 1000000 end,
        register_tool=function() end,
        register_on_joinplayer=function(f) callbacks.join=f end,
        register_on_leaveplayer=function() end,
        register_globalstep=function() end,
        register_chatcommand=function() end,
        after=function(_,f) callbacks.after=f end,
        get_player_by_name=function() if connected~=false then return player end end,
        chat_send_player=function() end,log=function() end,
    }
    dofile("sandbox/luanti/ak47_hd_android/init.lua")
    callbacks.join(player)
    callbacks.after()
    return inventory,player
end

local items,p=scenario({stack("stone","held"),stack(AK,"existing"),stack()},1)
assert(p:get_wielded_item().name==AK and items[1].tag=="existing","existing AK must be equipped")
assert(items[2].name=="stone" and items[2].tag=="held","held item must be preserved")
assert(items[3].name=="","existing AK must not be duplicated")

items,p=scenario({stack(),stack("torch","held"),stack()},2)
assert(p:get_wield_index()==2 and items[2].name==AK,"new AK uses the selected slot")
assert(items[1].name=="torch" and items[1].tag=="held","new AK must preserve the held item")
assert(items[3].name=="","new AK must be given exactly once")

items,p=scenario({stack(AK,"selected"),stack("stone","other")},1)
assert(items[1].tag=="selected" and items[2].tag=="other","already selected AK must stay in place")
assert(items[1].values.xz_ak_anim:sub(1,1)=="E","equip animation metadata must be synchronized")

items,p=scenario({stack("stone","one"),stack("torch","two")},2)
assert(items[1].tag=="one" and items[2].tag=="two","full inventory must not lose an item")

items,p=scenario({stack(),stack()},1,false)
assert(items[1].name=="" and items[2].name=="","disconnected player must not receive an item")
print("JOIN_TESTS_PASS: existing/new/already equipped AK, selected slot, item preservation, full inventory and disconnect")
