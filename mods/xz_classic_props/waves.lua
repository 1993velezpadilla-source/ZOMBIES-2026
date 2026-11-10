-- Xziel Zombies: original, small-map round controller and placeholder enemy.
-- Simple steering, not pathfinding. Intended for first mobile validation only.
local core = minetest
local api = xz_classic_props
local MAX_ALIVE = 12
local active, pending, alive, tick, wave_wait = false, 0, 0, 0, 0
local entities = {}
local no_spawn_warned = false

local function online()
    local players = {}
    for _,p in ipairs(core.get_connected_players()) do
        if p:get_hp() > 0 then players[#players+1] = p end
    end
    return players
end
local function inform(msg)
    for _,p in ipairs(core.get_connected_players()) do
        api.tell(p,msg)
    end
end
local function round_count()
    return api.get_round()
end
local function next_wave()
    local round = math.max(1, round_count())
    pending = math.min(40, 4 + round * 2)
    wave_wait = 0
    inform("ROUND " .. round .. " - " .. pending .. " zombies incoming.")
end

local enemy_def = {
    static_save = false,
    initial_properties = {
        hp_max=100,
        physical=true,
        collide_with_objects=true,
        collisionbox={-0.34, 0, -0.34, 0.34, 1.78, 0.34},
        visual="cube",
        visual_size={x=0.68,y=1.78,z=0.68},
        textures={
            "xzcp_zombie_spawn_marker.png","xzcp_zombie_spawn_marker.png",
            "xzcp_zombie_spawn_marker.png","xzcp_zombie_spawn_marker.png",
            "xzcp_zombie_spawn_marker.png","xzcp_zombie_spawn_marker.png",
        },
        makes_footstep_sound=false,
    },
    on_activate = function(self)
        self.health = math.min(2000, math.floor(100 * 1.18 ^ (round_count() - 1)))
        self.last_attack = 0
        self.ai_clock = 0
        self.object:set_properties({hp_max=self.health})
        self.object:set_hp(self.health)
        self.object:set_acceleration({x=0,y=-9.81,z=0})
        entities[self.object] = true
        alive = alive + 1
    end,
    on_step = function(self, dtime)
        if not active or not api.is_playing() then
            if self.object and self.object:is_valid() then self.object:remove() end
            return
        end
        self.ai_clock = self.ai_clock + dtime
        if self.ai_clock < 0.2 then return end
        local dt = math.min(self.ai_clock,0.3)
        self.ai_clock = 0
        local here = self.object:get_pos()
        if not here then return end
        local target, distance, dx_best, dz_best = nil, math.huge, 0, 0
        for _,p in ipairs(online()) do
            local dest = p:get_pos()
            local dx,dz=dest.x-here.x,dest.z-here.z
            local d=math.sqrt(dx*dx+dz*dz)
            if d < distance then
                distance,target,dx_best,dz_best=d,p,dx,dz
            end
        end
        if not target then
            self.object:set_velocity({x=0,y=self.object:get_velocity().y,z=0})
            return
        end
        if distance > 1.45 and distance < 80 then
            local speed = math.min(6.8, 2.2 + round_count() * 0.22)
            local vy = self.object:get_velocity().y
            self.object:set_velocity({
                x=dx_best / distance * speed,
                y=vy,
                z=dz_best / distance * speed,
            })
        else
            self.object:set_velocity({x=0,y=self.object:get_velocity().y,z=0})
            if distance <= 1.45 then
                self.last_attack = self.last_attack + dt
                if self.last_attack >= 1.15 then
                    self.last_attack=0
                    if target:get_hp()>0 then
                        target:set_hp(math.max(0,target:get_hp()-4))
                    end
                end
            end
        end
    end,
    on_punch = function(self,puncher,_,tool_caps,__,damage)
        if not active or not api.is_playing() then return end
        if not puncher or not puncher.is_player or not puncher:is_player() then return end
        local amount = tonumber(damage) or
            (tool_caps and tool_caps.damage_groups and tonumber(tool_caps.damage_groups.fleshy)) or 0
        if amount <= 0 then return end
        amount = math.max(1,math.min(1000, amount))
        local scale = api.damage_multiplier(puncher,puncher:get_wielded_item())
        amount = amount * scale
        self.health = self.health - amount
        api.add_points(puncher,10)
        if self.health <= 0 then
            api.award_kill(puncher,false)
            if self.object and self.object:is_valid() then self.object:remove() end
        else
            -- Keep the engine HP state in sync with our source-weapon damage.
            self.object:set_hp(math.max(1,math.ceil(self.health)))
        end
    end,
    on_deactivate = function(self)
        if entities[self.object] then
            entities[self.object]=nil
            alive=math.max(0,alive-1)
        end
    end,
}
core.register_entity("xz_classic_props:test_zombie",enemy_def)

function api.waves_start()
    active = true
    no_spawn_warned = false
    pending = 0
    alive = 0
    tick = 0
    wave_wait = 0
    for obj in pairs(entities) do
        if obj:is_valid() then obj:remove() end
    end
    entities = {}
    next_wave()
end

function api.waves_stop()
    active = false
    pending = 0
    tick = 0
    wave_wait = 0
    for obj in pairs(entities) do
        if obj:is_valid() then obj:remove() end
    end
    entities = {}
    alive = 0
end

function api.wave_status()
    return {
        active=active, round=round_count(),
        alive=alive, pending=pending,
    }
end

core.register_globalstep(function(dtime)
    if not active or not api.is_playing() then return end
    tick = tick + dtime
    if tick < 1.0 then return end
    tick = math.min(tick,2)
    local step=tick
    tick=0

    if #online()==0 then return end
    if pending > 0 and alive < MAX_ALIVE then
        local markers=api.get_markers("zombie_spawn_marker")
        if #markers == 0 then
            if not no_spawn_warned then
                inform("No Zombie Spawn Markers on this map. Place one in EDIT.")
                no_spawn_warned = true
            end
            return
        end
        no_spawn_warned = false
        local idx=math.random(#markers)
        local pos=markers[idx]
        local n=core.get_node_or_nil(pos)
        if n then
            local obj=core.add_entity({x=pos.x,y=pos.y+1,z=pos.z},
                "xz_classic_props:test_zombie")
            if obj then pending=pending-1 end
        end
    end
    if pending == 0 and alive == 0 then
        wave_wait = wave_wait + step
        if wave_wait >= 6 then
            api.set_round(round_count()+1)
            next_wave()
        end
    end
end)
