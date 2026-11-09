-- Original Roblox touch HUD and first-person controls.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ContextActionService = game:GetService("ContextActionService")

local player = Players.LocalPlayer
local events = ReplicatedStorage:WaitForChild("XZRemotes")
local fire = events:WaitForChild("Fire")
local reload = events:WaitForChild("Reload")
local update = events:WaitForChild("State")

local gui = Instance.new("ScreenGui")
gui.Name = "XzielZombiesHUD"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.Parent = player:WaitForChild("PlayerGui")

local function label(name, content, size, position, anchor, alignment)
    local l = Instance.new("TextLabel")
    l.Name = name
    l.Text = content
    l.Size = size
    l.Position = position
    l.AnchorPoint = anchor or Vector2.zero
    l.TextXAlignment = alignment or Enum.TextXAlignment.Left
    l.TextColor3 = Color3.fromRGB(237, 244, 237)
    l.TextStrokeTransparency = 0.4
    l.BackgroundTransparency = 1
    l.TextSize = 23
    l.Font = Enum.Font.GothamBold
    l.Parent = gui
    return l
end

local round = label("Round", "XZIEL ZOMBIES — ROUND 1", UDim2.new(0.9, 0, 0, 36), UDim2.new(0.06, 0, 0.04, 0))
local score = label("Points", "0 POINTS   0 KILLS", UDim2.fromOffset(310, 36), UDim2.new(0.06, 0, 0.1, 0))
local ammo = label("Ammo", "24 / 120", UDim2.fromOffset(230, 48), UDim2.new(0.97, 0, 0.9, 0), Vector2.new(1, 0), Enum.TextXAlignment.Right)
ammo.TextSize = 30
local sight = label("Crosshair", "+", UDim2.fromOffset(48, 48), UDim2.fromScale(0.5, 0.5), Vector2.new(0.5, 0.5), Enum.TextXAlignment.Center)
sight.TextSize = 32

local function enforceFirstPerson()
    player.CameraMode = Enum.CameraMode.LockFirstPerson
end
enforceFirstPerson()
player.CharacterAdded:Connect(enforceFirstPerson)

update.OnClientEvent:Connect(function(s)
    round.Text = string.format("XZIEL ZOMBIES  |  ROUND %d  |  %d LEFT", s.wave, s.active + s.pending)
    score.Text = string.format("%d POINTS  |  %d KILLS", s.points, s.kills)
    ammo.Text = s.reloading and "RELOADING..." or string.format("%d / %d", s.ammo, s.reserve)
end)

local function shoot(_, input)
    if input ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Pass end
    local camera = workspace.CurrentCamera
    if camera then
        fire:FireServer(camera.CFrame.Position, camera.CFrame.LookVector)
    end
    return Enum.ContextActionResult.Sink
end
local function reloadWeapon(_, input)
    if input == Enum.UserInputState.Begin then reload:FireServer() end
    return Enum.ContextActionResult.Sink
end

ContextActionService:BindAction("XZShoot", shoot, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
ContextActionService:SetTitle("XZShoot", "FIRE")
ContextActionService:SetPosition("XZShoot", UDim2.new(0.82, 0, 0.66, 0))
ContextActionService:BindAction("XZReload", reloadWeapon, true, Enum.KeyCode.R, Enum.KeyCode.ButtonX)
ContextActionService:SetTitle("XZReload", "RELOAD")
ContextActionService:SetPosition("XZReload", UDim2.new(0.73, 0, 0.82, 0))
