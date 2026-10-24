param(
  [Parameter(Mandatory=$true)][string]$GameRoot,
  [Parameter(Mandatory=$true)][string]$Executable,
  [Parameter(Mandatory=$true)][string]$ReportDir,
  [string]$DXNative
)

# Offline KisakCOD-sp level smoke: no multiplayer server, UDP socket or Steam
# login. Gameplay is only verified by distinct native SP code-stage markers.
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
$root=(Resolve-Path $GameRoot).Path
$trace=Join-Path $root 'z2026-sp-level-trace.txt'
$combatTrace=Join-Path $root 'z2026-sp-combat-trace.txt'
$reportPath=Join-Path $ReportDir 'offline-sp-runtime.json'
$report=[ordered]@{
  test='Windows source-built offline KisakCOD-sp level simulation smoke'
  mode='single-player offline only'
  local_game_data_used_only_temporarily=$true
  native_sp_executable_detected=$false
  sp_process_launched=$false
  source_built_game_process_alive_at_40s=$false
  exit_code=$null
  map_requested='killhouse'
  game_init_entered=$false
  spawn_entities_returned=$false
  game_frame_started=$false
  second_game_frame_started=$false
  player_entity_active=$false
  player_weapon_equipped=$false
  test_loadout_bootstrap_attempted=$false
  test_valid_registered_bullet_weapon_found=$false
  test_weapon_granted=$false
  test_ammo_initialized=$false
  test_weapon_switch_requested=$false
  test_no_compatible_registered_weapon=$false
  sp_actor_present=$false
  actual_weapon_fire_callback=$false
  bullet_fire_dispatched=$false
  actor_ai_think_executed=$false
  actor_damage_callback=$false
  actor_pain_callback=$false
  actor_death_callback=$false
  g_damage_callback=$false
  offline_sp_level_loop_verified=$false
  actual_graphics_verified=$false
  weapon_fired_verified=$false
  zombie_spawned_verified=$false
  multiplayer_connection_attempted=$false
  steam_login_attempted_by_test=$false
  raw_game_assets_in_report=$false
  stage_trace=@()
  combat_trace=@()
  attack_command_requested=$false
  runtime_error=$null
}
$proc=$null
try {
  if (!(Test-Path $Executable)) { throw 'KisakCOD-sp executable not found' }
  $exe=Join-Path $root 'KisakCOD-sp.exe'
  Copy-Item $Executable $exe -Force
  $report.native_sp_executable_detected=$true
  $deps='third_party/KisakCOD/deps'
  foreach($src in @(
    "$deps/binklib/binkw32.dll",
    "$deps/msslib/dlls/mss32.dll",
    "$deps/steamsdk/steam_api.dll"
  )){
    if (!(Test-Path $src)) { throw "Required runtime DLL missing from KisakCOD deps" }
    Copy-Item $src $root -Force
  }
  $dxBin=Join-Path $DXNative 'Release/bin/x86'
  if (!(Test-Path (Join-Path $dxBin 'D3DX9_43.dll'))){
    throw 'Missing Win32 DirectX9 runtime'
  }
  foreach($dll in @('D3DX9_43.dll','D3DCompiler_43.dll','d3dx10_43.dll','d3dx11_43.dll')){
    $path=Join-Path $dxBin $dll
    if (Test-Path $path) { Copy-Item $path $root -Force }
  }
  $miles=Join-Path $root 'miles'
  New-Item -ItemType Directory -Path $miles -Force | Out-Null
  Get-ChildItem "$deps/msslib/dlls/miles" -File -ErrorAction SilentlyContinue |
    ForEach-Object { Copy-Item $_.FullName $miles -Force }
  $profiles=Join-Path $root 'players/profiles'
  New-Item -ItemType Directory -Force -Path (Join-Path $profiles 'Z2026OfflineTest') | Out-Null
  Set-Content -Path (Join-Path $profiles 'active.txt') -Value 'Z2026OfflineTest' -Encoding ascii -NoNewline
  Remove-Item -ErrorAction SilentlyContinue $trace,$combatTrace

  # The only game process launched is source-built *single player*.
  # No network address, connect, dedicated, Steam session or user credential.
  $argsLine='+set fs_basepath "'+$root+'" +set fs_homepath "'+$root+'" +set r_fullscreen 0 +set r_mode 4 +set com_introPlayed 1 +map killhouse +attack'
  $report.attack_command_requested=$true
  Write-Host 'Launching KisakCOD-sp, direct offline map killhouse; no multiplayer.'
  $stdout=Join-Path $ReportDir 'sp-stdout.txt'
  $stderr=Join-Path $ReportDir 'sp-stderr.txt'
  $proc=Start-Process -FilePath $exe -ArgumentList $argsLine -WorkingDirectory $root -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr -ErrorAction Stop
  $report.sp_process_launched=$true
  $exited=$proc.WaitForExit(40000)
  if($exited){$report.exit_code=$proc.ExitCode}
  else{$report.source_built_game_process_alive_at_40s=$true}
}
catch {
  $report.runtime_error=$_.Exception.Message
}
finally {
  if($null -ne $proc){
    try {
      $proc.Refresh()
      if(-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    } catch {}
  }
  if(Test-Path $trace) {
    $stages=@(Get-Content $trace -TotalCount 40 -ErrorAction SilentlyContinue)
    $report.stage_trace=@($stages | Where-Object { $_ -in @('G_INIT_ENTER', 'G_SPAWN_ENTITIES_RETURN', 'G_FRAME_ENTER', 'G_SECOND_FRAME', 'PLAYER_ENTITY_ACTIVE', 'PLAYER_WEAPON_EQUIPPED', 'SP_ACTOR_PRESENT', 'TEST_LOADOUT_BOOTSTRAP_BEGIN', 'TEST_REGISTERED_BULLET_WEAPON_FOUND', 'TEST_WEAPON_GRANTED', 'TEST_AMMO_INITIALIZED', 'TEST_WEAPON_SWITCH_REQUESTED', 'TEST_NO_VALID_REGISTERED_BULLET_WEAPON', 'TEST_WEAPON_GRANT_REJECTED') })
    $report.game_init_entered=('G_INIT_ENTER' -in $report.stage_trace)
    $report.spawn_entities_returned=('G_SPAWN_ENTITIES_RETURN' -in $report.stage_trace)
    $report.game_frame_started=('G_FRAME_ENTER' -in $report.stage_trace)
    $report.second_game_frame_started=('G_SECOND_FRAME' -in $report.stage_trace)
    $report.player_entity_active=('PLAYER_ENTITY_ACTIVE' -in $report.stage_trace)
    $report.player_weapon_equipped=('PLAYER_WEAPON_EQUIPPED' -in $report.stage_trace)
    $report.test_loadout_bootstrap_attempted=('TEST_LOADOUT_BOOTSTRAP_BEGIN' -in $report.stage_trace)
    $report.test_valid_registered_bullet_weapon_found=('TEST_REGISTERED_BULLET_WEAPON_FOUND' -in $report.stage_trace)
    $report.test_weapon_granted=('TEST_WEAPON_GRANTED' -in $report.stage_trace)
    $report.test_ammo_initialized=('TEST_AMMO_INITIALIZED' -in $report.stage_trace)
    $report.test_weapon_switch_requested=('TEST_WEAPON_SWITCH_REQUESTED' -in $report.stage_trace)
    $report.test_no_compatible_registered_weapon=('TEST_NO_VALID_REGISTERED_BULLET_WEAPON' -in $report.stage_trace)
    $report.sp_actor_present=('SP_ACTOR_PRESENT' -in $report.stage_trace)
    $report.offline_sp_level_loop_verified=$report.spawn_entities_returned -and $report.game_frame_started
  }
  if(Test-Path $combatTrace) {
    $report.combat_trace=@(Get-Content $combatTrace -TotalCount 40 -ErrorAction SilentlyContinue)
    $report.actual_weapon_fire_callback=('FIRE_WEAPON_ENTER' -in $report.combat_trace)
    $report.bullet_fire_dispatched=('BULLET_FIRE_DISPATCH' -in $report.combat_trace)
    $report.actor_ai_think_executed=('ACTOR_THINK_ENTER' -in $report.combat_trace)
    $report.actor_damage_callback=('G_DAMAGE_ACTOR' -in $report.combat_trace)
    $report.actor_pain_callback=('ACTOR_PAIN_ENTER' -in $report.combat_trace)
    $report.actor_death_callback=('ACTOR_DIE_ENTER' -in $report.combat_trace)
    $report.g_damage_callback=('G_DAMAGE_ENTER' -in $report.combat_trace)
  }
  $report | ConvertTo-Json -Depth 4 | Set-Content $reportPath -Encoding utf8
  Write-Host 'Z2026_OFFLINE_SP_RUNTIME_BEGIN'
  Get-Content $reportPath
  Write-Host 'Z2026_OFFLINE_SP_RUNTIME_END'
}
# Return successful CI diagnostic execution, not a fake 'Zombies playable' green.
