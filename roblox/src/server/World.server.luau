-- Builds an original, lightweight flat arena at runtime.
local Lighting = game:GetService("Lighting")
local world = Instance.new("Folder")
world.Name = "XZWorld"
world.Parent = workspace

Lighting.ClockTime = 1
Lighting.Brightness = 1.5
Lighting.Ambient = Color3.fromRGB(38, 43, 55)
Lighting.FogEnd = 130

local function add(name, size, pos, color, material)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = pos
    p.Color = color
    p.Material = material or Enum.Material.Concrete
    p.Anchored = true
    p.Parent = world
    return p
end

local stone = Color3.fromRGB(60, 65, 72)
add("Ground", Vector3.new(128, 2, 128), Vector3.new(0, -1, 0), stone)
add("North Wall", Vector3.new(128, 17, 3), Vector3.new(0, 8.5, -64), stone, Enum.Material.Brick)
add("South Wall", Vector3.new(128, 17, 3), Vector3.new(0, 8.5, 64), stone, Enum.Material.Brick)
add("West Wall", Vector3.new(3, 17, 128), Vector3.new(-64, 8.5, 0), stone, Enum.Material.Brick)
add("East Wall", Vector3.new(3, 17, 128), Vector3.new(64, 8.5, 0), stone, Enum.Material.Brick)
for _, pos in ipairs({
    Vector3.new(-22, 3, -18), Vector3.new(22, 3, 18),
    Vector3.new(22, 3, -18), Vector3.new(-22, 3, 18)
}) do
    add("Cover", Vector3.new(8, 6, 7), pos, Color3.fromRGB(45, 52, 58), Enum.Material.Metal)
end
local spawn = Instance.new("SpawnLocation")
spawn.Name = "XZSpawn"
spawn.Size = Vector3.new(9, 1, 9)
spawn.Position = Vector3.new(0, 0.5, 0)
spawn.Anchored = true
spawn.Neutral = true
spawn.Material = Enum.Material.Neon
spawn.Color = Color3.fromRGB(43, 105, 89)
spawn.Parent = world
