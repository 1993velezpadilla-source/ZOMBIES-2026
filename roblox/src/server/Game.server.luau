-- Xziel Zombies prototype: authoritative hit detection and phone-friendly zombie waves.
-- Original placeholder geometry only. No COD4 intellectual property.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Config = require(ReplicatedStorage:WaitForChild("Config"))
local world = workspace:WaitForChild("XZWorld")

local folder = Instance.new("Folder")
folder.Name = "XZRemotes"
folder.Parent = ReplicatedStorage
local fire = Instance.new("RemoteEvent")
fire.Name = "Fire"
fire.Parent = folder
local reload = Instance.new("RemoteEvent")
reload.Name = "Reload"
reload.Parent = folder
local stateEvent = Instance.new("RemoteEvent")
stateEvent.Name = "State"
stateEvent.Parent = folder

local profiles = {}
local zombies = {}
local wave = 0
local active = 0
local pending = 0
local points = {
    Vector3.new(48, 3, 48), Vector3.new(-48, 3, 48),
    Vector3.new(48, 3, -48), Vector3.new(-48, 3, -48),
    Vector3.new(0, 3, -50), Vector3.new(0, 3, 50)
}
local rng = Random.new()

local function report(player)
    local p = profiles[player]
    if not p then return end
    stateEvent:FireClient(player, {
        wave = wave, active = active, pending = pending,
        ammo = p.ammo, reserve = p.reserve, reloading = p.reloading,
        points = p.score.Value, kills = p.kills.Value
    })
end
local function reportAll()
    for _, p in ipairs(Players:GetPlayers()) do report(p) end
end

Players.PlayerAdded:Connect(function(player)
    local stats = Instance.new("Folder")
    stats.Name = "leaderstats"
    stats.Parent = player
    local score = Instance.new("IntValue")
    score.Name = "Points"
    score.Parent = stats
    local kills = Instance.new("IntValue")
    kills.Name = "Kills"
    kills.Parent = stats
    profiles[player] = {
        score = score, kills = kills,
        ammo = Config.Ammo, reserve = Config.Reserve,
        lastFire = -100, reloading = false
    }
    player.CharacterAdded:Connect(function()
        task.delay(1, function() if player.Parent then report(player) end end)
    end)
    task.delay(1, function() if player.Parent then report(player) end end)
end)
Players.PlayerRemoving:Connect(function(p) profiles[p] = nil end)

local function component(model, name, size, base, offset, color)
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.CFrame = base * CFrame.new(offset)
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.Color = color
    part.Parent = model
    return part
end
local function spawnZombie()
    local model = Instance.new("Model")
    model.Name = "XZ Zombie"
    local base = CFrame.new(points[rng:NextInteger(1, #points)])
    local body = component(model, "Body", Vector3.new(2, 2.2, 1.3), base, Vector3.zero, Color3.fromRGB(64, 89, 58))
    component(model, "Head", Vector3.new(1.4, 1.5, 1.4), base, Vector3.new(0, 1.8, 0), Color3.fromRGB(93, 120, 76))
    component(model, "ArmL", Vector3.new(0.7, 2, 0.8), base, Vector3.new(-1.45, 0, 0), Color3.fromRGB(84, 109, 70))
    component(model, "ArmR", Vector3.new(0.7, 2, 0.8), base, Vector3.new(1.45, 0, 0), Color3.fromRGB(84, 109, 70))
    model.PrimaryPart = body
    model.Parent = world
    zombies[model] = {hp = Config.ZombieHealth, lastHit = 0}
    active += 1
end

fire.OnServerEvent:Connect(function(player, origin, direction)
    local p = profiles[player]
    if not p or p.reloading then return end
    if typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then return end
    if direction.Magnitude < 0.95 or direction.Magnitude > 1.05 then return end
    local char = player.Character
    local head = char and char:FindFirstChild("Head")
    local humanoid = char and char:FindFirstChildOfClass("Humanoid")
    if not head or not humanoid or humanoid.Health <= 0 then return end
    if (origin - head.Position).Magnitude > 10 then return end
    local now = os.clock()
    if now - p.lastFire < Config.FireInterval then return end
    p.lastFire = now
    if p.ammo == 0 then report(player) return end
    p.ammo -= 1
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = { char }
    local hit = workspace:Raycast(origin, direction.Unit * 170, params)
    if hit then
        local model = hit.Instance:FindFirstAncestorOfClass("Model")
        local zombie = model and zombies[model]
        if zombie then
            zombie.hp -= Config.Damage
            p.score.Value += 10
            if zombie.hp <= 0 then
                zombies[model] = nil
                active -= 1
                p.score.Value += 90
                p.kills.Value += 1
                model:Destroy()
                reportAll()
            end
        end
    end
    report(player)
end)

reload.OnServerEvent:Connect(function(player)
    local p = profiles[player]
    if not p or p.reloading or p.reserve <= 0 or p.ammo >= Config.Ammo then return end
    p.reloading = true
    report(player)
    task.delay(Config.ReloadTime, function()
        if profiles[player] ~= p then return end
        local quantity = math.min(Config.Ammo - p.ammo, p.reserve)
        p.ammo += quantity
        p.reserve -= quantity
        p.reloading = false
        report(player)
    end)
end)

local elapsed = 0
RunService.Heartbeat:Connect(function(dt)
    elapsed += dt
    if elapsed < 0.14 then return end
    local step = math.min(elapsed, 0.3)
    elapsed = 0
    local now = os.clock()
    for model, zombie in pairs(zombies) do
        local root = model.PrimaryPart
        if not root then continue end
        local target, nearest = nil, math.huge
        for _, player in ipairs(Players:GetPlayers()) do
            local char = player.Character
            local hrp = char and char:FindFirstChild("HumanoidRootPart")
            local hum = char and char:FindFirstChildOfClass("Humanoid")
            if hrp and hum and hum.Health > 0 then
                local delta = hrp.Position - root.Position
                local dist = Vector3.new(delta.X, 0, delta.Z).Magnitude
                if dist < nearest then
                    target, nearest = hrp, dist
                end
            end
        end
        if target then
            local delta = target.Position - root.Position
            local flat = Vector3.new(delta.X, 0, delta.Z)
            if nearest > 3.4 and flat.Magnitude > 0.01 then
                local nextPos = root.Position + flat.Unit * math.min(Config.ZombieSpeed * step, nearest - 3.4)
                model:PivotTo(CFrame.lookAt(nextPos, nextPos + flat.Unit))
            elseif nearest <= 3.4 and now - zombie.lastHit >= 1.2 then
                zombie.lastHit = now
                local hum = target.Parent and target.Parent:FindFirstChildOfClass("Humanoid")
                if hum then hum:TakeDamage(Config.ZombieDamage) end
            end
        end
    end
end)

task.spawn(function()
    while true do
        if #Players:GetPlayers() == 0 then
            task.wait(1)
        else
            wave += 1
            pending = math.min(3 + 3 * wave, 30)
            reportAll()
            while pending > 0 or active > 0 do
                if #Players:GetPlayers() == 0 then
                    for model in pairs(zombies) do model:Destroy() end
                    table.clear(zombies)
                    active, pending = 0, 0
                    break
                end
                if pending > 0 and active < Config.MaxZombies then
                    spawnZombie()
                    pending -= 1
                    reportAll()
                end
                task.wait(1.25)
            end
            task.wait(6)
        end
    end
end)
