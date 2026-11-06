-- Real Luanti mod callback behavior test, not just luac syntax.
-- FAKE ENGINE. Exercises inventory, ammo, ADS, reload, source-preview and crate.
local clock = 1
ItemStack=function(name) return make_stack(name) end
local function clone_table(t)
    local r={}
    for k,v in pairs(t) do
        if type(v)=="table" then r[k]=clone_table(v) else r[k]=v end
    end
    return r
end

local function make_stack(name)
    local self={name=name or "", meta={}}
    function self:get_name() return self.name end
    function self:is_empty() return self.name=="" end
    function self:get_meta()
        local m=self.meta
        return {
            get_string=function(_,key) return tostring(m[key] or "") end,
            set_string=function(_,key,val) m[key]=tostring(val) end,
            get_int=function(_,key) return tonumber(m[key]) or 0 end,
            set_int=function(_,key,val) m[key]=math.floor(val) end
        }
    end
    return self
end
local function duplicate(item)
    local x=make_stack(item.name)
    x.meta=clone_table(item.meta)
    return x
end

local slots={}
for n=1,8 do slots[n]=make_stack() end
local inventory={
    get_size=function(_,list) assert(list=="main");return #slots end,
    get_stack=function(_,list,index) assert(list=="main");return duplicate(slots[index]) end,
    set_stack=function(_,list,index,item) assert(list=="main");slots[index]=duplicate(item) end,
    contains_item=function(_,list,item)
        assert(list=="main")
        for _,s in ipairs(slots) do if s.name==item then return true end end
        return false
    end,
    add_item=function(_,list,item)
        assert(list=="main")
        local name=item:match("^[^ ]+")
        for n,slot in ipairs(slots) do
            if slot.name=="" then slots[n]=make_stack(name); return make_stack() end
        end
        return make_stack(item)
    end
}
local wield_index=1
local control={dig=false,aux1=false}
local fov=0
local hud_text=""
local player={
    is_player=function() return true end,
    get_player_name=function() return "Tester" end,
    get_inventory=function() return inventory end,
    get_wielded_item=function() return inventory:get_stack("main",wield_index) end,
    set_wield_index=function(_,i) assert(i>=1 and i<=#slots);wield_index=i end,
    set_wielded_item=function(_,item) inventory:set_stack("main",wield_index,item) end,
    get_player_control=function() return control end,
    get_properties=function() return {eye_height=1.47} end,
    get_pos=function() return {x=0,y=0,z=0} end,
    get_look_dir=function() return {x=0,y=0,z=1} end,
    set_fov=function(_,v) fov=v end,
    hud_add=function() return 1 end,
    hud_change=function(_,_,_,text) hud_text=text end,
}
local catalog={
    schema_version=1,
    weapons={
        {id="ak47",name="AK-47",category="assault",
         gun_model="arsenal_ak47_gun.glb",hands_model="arsenal_ak47_hands.glb",
         gameplay_logic_enabled=true,magazine_capacity=30,reserve_max=180,
         fire_interval_seconds=.085,reload_seconds=2.5,reload_empty_seconds=3.25,
         damage=40,distinct_empty_reload_animation=true,fire_mode="auto"},
        {id="m4",name="M4",category="assault",
         gun_model="arsenal_m4_gun.glb",hands_model="arsenal_m4_hands.glb",
         gameplay_logic_enabled=true,magazine_capacity=30,reserve_max=180,
         fire_interval_seconds=.09,reload_seconds=2.5,reload_empty_seconds=3.25,
         damage=30,distinct_empty_reload_animation=true,fire_mode="auto"},
        {id="m16",name="M16A4",category="assault",
         gun_model="arsenal_m16_gun.glb",hands_model="arsenal_m16_hands.glb",
         gameplay_logic_enabled=true,magazine_capacity=30,reserve_max=180,
         fire_interval_seconds=.064,reload_seconds=2.0,reload_empty_seconds=2.365,
         damage=30,distinct_empty_reload_animation=true,fire_mode="burst"},
        {id="m9",name="M9 BERETTA",category="pistol",
         gun_model="arsenal_m9_gun.glb",hands_model="arsenal_m9_hands.glb",
         gameplay_logic_enabled=true,magazine_capacity=15,reserve_max=90,
         fire_interval_seconds=.05,reload_seconds=1.629,reload_empty_seconds=1.917,
         damage=40,distinct_empty_reload_animation=false,fire_mode="semi"},
        {id="usp",name="USP PREVIEW",category="pistol",
         gun_model="arsenal_usp_gun.glb",hands_model="arsenal_usp_hands.glb",
         gameplay_logic_enabled=false,distinct_empty_reload_animation=false,
         fire_mode="semi"}
    }
}
local fake_mod_root="/fake/source/arsenal"
local original_open=io.open
io.open=function(path,mode)
    if path==fake_mod_root.."/arsenal_runtime.json" then
        return {read=function() return "{}" end,close=function() end}
    end
    if path:find("/models/arsenal_",1,true) and path:match("%.glb$") then
        return {read=function() return "SOURCE" end,close=function() end}
    end
    return original_open(path,mode)
end
local methods={}
local hit_count=0
local played={}
local formshown={}
local messages={}
local form_callback
local function has_audio(name)
    for _,effect in ipairs(played) do if effect==name then return true end end
    return false
end
_G.vector={
    add=function(a,b) return {x=a.x+b.x,y=a.y+b.y,z=a.z+b.z} end,
    multiply=function(a,v) return {x=a.x*v,y=a.y*v,z=a.z*v} end
}
_G.minetest={
    get_modpath=function(name) assert(name=="arsenal");return fake_mod_root end,
    parse_json=function(text) assert(text=="{}");return catalog end,
    register_tool=function(name,t) methods[name]=t end,
    register_node=function(name,t) methods[name]=t end,
    register_chatcommand=function(name,t) methods["/"..name]=t end,
    register_craftitem=function(name,t) methods[name]=t end,
    register_on_player_receive_fields=function(fn) form_callback=fn end,
    formspec_escape=function(s)
        return tostring(s):gsub("\\","\\\\"):gsub("%]","\\]"):gsub("%[","\\[")
    end,
    show_formspec=function(who,name,body)
        assert(who=="Tester" and name=="arsenal:picker")
        formshown[#formshown+1]=body
    end,
    chat_send_player=function(who,msg)
        assert(who=="Tester")
        messages[#messages+1]=msg
    end,
    register_on_joinplayer=function(fn) methods.join=fn end,
    register_on_leaveplayer=function(fn) methods.leave=fn end,
    register_globalstep=function(fn) methods.step=fn end,
    get_us_time=function() return math.floor(clock*1000000) end,
    get_connected_players=function() return {player} end,
    get_player_by_name=function(name) return name=="Tester" and player or nil end,
    after=function(delay,fn) assert(delay>=0);fn() end,
    raycast=function() return function() return nil end end,
    log=function() end,
    sound_play=function(name,params,ephemeral)
        assert(params.to_player=="Tester" and ephemeral==true)
        played[#played+1]=name
    end,
}
local mod="sandbox/luanti/arsenal_android/arsenal_mod/init.lua"
dofile(mod)
assert(methods["arsenal:ak47"] and methods["arsenal:m4"] and
       methods["arsenal:m9"] and
       methods["arsenal:m16"] and methods["arsenal:usp"])
assert(methods["arsenal:ammo_box"] and methods["/arsenalammo"])
assert(methods["/arsenal"])
assert(methods["/arsenalmenu"] and methods["arsenal:tablet"])
assert(type(form_callback)=="function")
methods.join(player)
assert(inventory:contains_item("main","arsenal:m9"),
    "Regression: M9 pistol missing from mobile hotbar")
assert(inventory:contains_item("main","arsenal:tablet"),
    "Regression: no visible way to open weapon selector")
assert(inventory:contains_item("main","arsenal:m4"))
assert(inventory:contains_item("main","arsenal:ammo_box"))

local function equip(name, slot)
    slots[slot]=make_stack(name);wield_index=slot
    methods.step(.02)
end
local function ammo(slot)
    local m=slots[slot]:get_meta()
    return m:get_int("ar_clip"),m:get_int("ar_reserve")
end
equip("arsenal:ak47",1)
assert(ammo(1)==30)
local get=methods["arsenal:ak47"]
get.on_use(player:get_wielded_item(),player)
assert(ammo(1)==29,"AK fire must consume one real bullet")
assert(hud_text:find("29 / 150"),"Real source ammo HUD wrong")
assert(has_audio("ak47dev_fire"),"AK must use actual original fire sound")
clock=clock+.11
get.on_secondary_use(player:get_wielded_item(),player)
assert(player:get_wielded_item():get_meta():get_string("xz_ar_ads")=="1","ADS metadata")
assert(fov>0,"ADS FOV")
-- A tactical reload with a remaining bullet preserves its unique state.
clock=clock+.11
control.aux1=true
methods.step(.02)
local meta=player:get_wielded_item():get_meta()
assert(meta:get_string("xz_ar_empty")=="0","Tactical reload selected empty sequence")
assert(meta:get_string("xz_ar_anim"):sub(1,1)=="R")
assert(ammo(1)==29,"Clip must not refill before actual reload duration")
assert(has_audio("ak47dev_reload_normal"),"Tactical mag sound must be original")
control.aux1=false
clock=clock+2.51
methods.step(.01)
local a,b=ammo(1);assert(a==30 and b==149,"Tactical reload accounting")

-- Exhaust the magazine using SOURCE fire interval.
for i=1,30 do
    clock=clock+.11
    get.on_use(player:get_wielded_item(),player)
end
a,b=ammo(1);assert(a==0 and b==149,"Magazine must empty exactly")
clock=clock+.11
get.on_use(player:get_wielded_item(),player)
assert(has_audio("ak47dev_dry"),"AK original dry-fire click required at zero")
a,b=ammo(1);assert(a==0 and b==149,"Dry-fire cannot consume reserve")
clock=clock+.3
control.aux1=true;methods.step(.01);control.aux1=false
meta=player:get_wielded_item():get_meta()
assert(meta:get_string("xz_ar_empty")=="1","Empty magazine needs original empty animation")
assert(has_audio("ak47dev_reload_empty"),"Empty mag sound must remain distinct")
clock=clock+3.26;methods.step(.01)
a,b=ammo(1);assert(a==30 and b==119,"Empty-mag refill accounting")

-- Validate M9: usable source stats and normal animation fallback on empty.
equip("arsenal:m9",5)
local m9=methods["arsenal:m9"]
clock=clock+.3
m9.on_use(player:get_wielded_item(),player)
assert(ammo(5)==14,"M9 must fire and consume ammo")
for _=1,14 do
    clock=clock+.06
    m9.on_use(player:get_wielded_item(),player)
end
assert(ammo(5)==0,"M9 magazine must reach empty")
clock=clock+.06
control.aux1=true
methods.step(.01)
assert(player:get_wielded_item():get_meta():get_string("xz_ar_empty")=="1",
    "Empty M9 must trigger fallback reload")
control.aux1=false
clock=clock+1.92
methods.step(.01)
assert(ammo(5)==15,"M9 reload must refill source mag even without separate empty clip")

-- Universal ammo crate refills both owned arms, not only AK.
equip("arsenal:m4",2)
local m4=methods["arsenal:m4"]
local audio_count_before_other_weapon=#played
clock=clock+.2
m4.on_use(player:get_wielded_item(),player)
assert(ammo(2)==29)
assert(#played==audio_count_before_other_weapon,
    "Other guns may NOT reuse original AK47 fire sound")
methods["arsenal:ammo_box"].on_rightclick(nil,nil,player,nil)
a,b=ammo(1);assert(a==30 and b==150,"AK crate reserve")
a,b=ammo(2);assert(a==30 and b==150,"M4 universal refill")
-- On-phone players can also punch the box to interact.
clock=clock+1
m4.on_use(player:get_wielded_item(),player)
methods["arsenal:ammo_box"].on_punch(nil,nil,player)
assert(ammo(2)==30,"Touch-compatible on_punch universal refill")
-- Preview-only weapons are registered but never grant guessed real damage.
equip("arsenal:usp",3)
local preview=methods["arsenal:usp"]
clock=clock+.1
preview.on_use(player:get_wielded_item(),player)
assert(ammo(3)==0,"Preview gun must not get fabricated clip count")
assert(player:get_wielded_item():get_meta():get_string("xz_ar_anim"):sub(1,1)=="F")
assert(#played==audio_count_before_other_weapon,
    "Preview pistols must not emit the AK sound")

-- COD4 M16 genuine three-round burst: 3 shots, 3 bullets, never fake rounds.
equip("arsenal:m16",4)
local m16=methods["arsenal:m16"]
clock=clock+.6
control.dig=true
m16.on_use(player:get_wielded_item(),player)
assert(ammo(4)==29,"M16 initial burst fire")
for _=1,2 do
    clock=clock+.075
    methods.step(.075)
end
assert(ammo(4)==27,"Exactly three rounds fired, not one or an early consumed burst")
-- Continued button hold must not schedule a second three-round burst.
clock=clock+.15
m16.on_use(player:get_wielded_item(),player)
methods.step(.01)
assert(ammo(4)==27,"Holding trigger must not repeat M16 burst")
control.dig=false
methods.step(.02)
clock=clock+.15
control.dig=true
m16.on_use(player:get_wielded_item(),player)
assert(ammo(4)==26,"New burst begins only after trigger released")
for _=1,2 do
    clock=clock+.075
    methods.step(.075)
end
assert(ammo(4)==24,"Second three-round burst must consume exactly 3 rounds")
control.dig=false
methods.step(.01)
local ok,msg=methods["/arsenal"].func("Tester","not_a_real_gun")
assert(not ok and msg:find("not verified"),"No nonexistent tool")
ok,msg=methods["/arsenal"].func("Tester","m4")
assert(ok)
ok,msg=methods["/arsenalammo"].func("Tester")
assert(ok)
assert(inventory:contains_item("main","arsenal:ammo_box"))
-- Mobile formspec can switch categories and select only real GLB-backed guns.
local before=#formshown
ok,msg=methods["/arsenalmenu"].func("Tester")
assert(ok and #formshown==before+1 and formshown[#formshown]:find("cat_assault"))
assert(formshown[#formshown]:find("weapon_ak47") and formshown[#formshown]:find("weapon_m4"))
assert(not formshown[#formshown]:find("weapon_usp"),
    "Category list must not leak guns from other categories")
form_callback(player,"arsenal:picker",{cat_pistol="true"})
assert(formshown[#formshown]:find("weapon_usp"),"Touch pistol category")
assert(not formshown[#formshown]:find("weapon_ak47"),"Pistol filter")
-- This is the same tablet UI entry used by Android touchscreen users.
methods["arsenal:tablet"].on_use(make_stack("arsenal:tablet"),player)
assert(#formshown==before+3)
local oldmessages=#messages
form_callback(player,"arsenal:picker",{weapon_usp="true"})
assert(#messages==oldmessages+1,"Choosing a GLB-backed gun shows equip confirmation")
assert(inventory:contains_item("main","arsenal:usp"))
assert(player:get_wielded_item():get_name()=="arsenal:usp",
    "Touch gun selection must immediately EQUIP, not just grant inventory item")
local previous=#messages
form_callback(player,"arsenal:picker",{weapon_fake="true"})
assert(#messages==previous,"Unknown button cannot issue arbitrary inventory item")
methods.leave(player)
io.open=original_open
print("ARSENAL_LUA_REAL_CALLBACK_GAUNTLET=PASS; weapons=3, magazine/dry/ADS/reload/crate/touch")
