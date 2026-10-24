param(
    [Parameter(Mandatory=$true)][string]$GameRoot,
    [Parameter(Mandatory=$true)][string]$BuildDir,
    [Parameter(Mandatory=$true)][string]$ReportDir
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$stdoutPath=Join-Path $ReportDir 'server-stdout.txt'
$stderrPath=Join-Path $ReportDir 'server-stderr.txt'
$reportPath=Join-Path $ReportDir 'server-runtime-report.json'

$report=[ordered]@{
  stage='Windows KisakCOD x86 dedicated isolated MP boot smoke'
  multiplayer_level='mp_crash'
  used_source_built_kisak_server=$true
  copied_original_commercial_executables=$false
  local_only_127_0_0_1=$true
  source_game_assets_complete=$false
  executable_detected=$false
  server_process_started=$false
  server_alive_at_45_seconds=$false
  exited_early=$false
  exit_code=$null
  map_boot_verified=$false
  client_connected=$false
  mod_ff_present=$false
  zombies_spawned=$false
  runtime_exception=$null
  runtime_dll_inventory=@()
  runtime_log_keyword_hits=@()
}
$process=$null
try {
  $root=(Resolve-Path $GameRoot).Path
  if ($env:KISAK_DIAGNOSTIC_EXE -and (Test-Path $env:KISAK_DIAGNOSTIC_EXE)) {
    $exeCandidates=@(Get-Item $env:KISAK_DIAGNOSTIC_EXE)
  } else {
    $exeCandidates=@(Get-ChildItem -Path (Join-Path $BuildDir 'bin') -Recurse -Filter 'KisakCOD-dedi.exe' -File -ErrorAction SilentlyContinue)
  }
  if ($exeCandidates.Count -eq 0) {
    $exeCandidates=@(Get-ChildItem -Path 'third_party/KisakCOD/bin' -Recurse -Filter 'KisakCOD-dedi.exe' -File -ErrorAction SilentlyContinue)
  }
  if ($exeCandidates.Count -eq 0) {
    $exeCandidates=@(Get-ChildItem -Path $BuildDir -Recurse -Filter 'KisakCOD-dedi.exe' -File -ErrorAction SilentlyContinue)
  }
  if ($exeCandidates.Count -ne 1) { throw "Expected one KisakCOD-dedi.exe, found $($exeCandidates.Count)" }
  $exe=$exeCandidates[0]
  $report.executable_detected=$true
  Copy-Item -Path $exe.FullName -Destination (Join-Path $root 'KisakCOD-dedi.exe') -Force
  if ($env:KISAK_DIAGNOSTIC_PDB -and (Test-Path $env:KISAK_DIAGNOSTIC_PDB)) {
    Copy-Item $env:KISAK_DIAGNOSTIC_PDB -Destination (Join-Path $root 'KisakCOD-dedi.pdb') -Force
  }
  $deps='third_party/KisakCOD/deps'
  $dlls=@(
    "$deps/binklib/binkw32.dll",
    "$deps/msslib/dlls/mss32.dll",
    "$deps/steamsdk/steam_api.dll"
  )
  foreach ($src in $dlls) {
    if (Test-Path $src) {
      Copy-Item $src -Destination $root -Force
    }
  }
  # The Microsoft.DXSDK.D3DX NuGet package stores the x86 runtime DLLs in
  # Release/bin/x86, separate from the headers and import libs used at build.
  # Windows exit status 0xC0000135 identifies a missing load-time DLL.
  $d3dxBin=Join-Path $env:DXSDK_NATIVE 'Release/bin/x86'
  if (!(Test-Path (Join-Path $d3dxBin 'D3DX9_43.dll'))) {
    throw "Missing official x86 D3DX9_43.dll at $d3dxBin"
  }
  foreach($name in @('D3DX9_43.dll','D3DCompiler_43.dll','d3dx10_43.dll','d3dx11_43.dll')){
    $path=Join-Path $d3dxBin $name
    if(Test-Path $path){
      Copy-Item $path -Destination $root -Force
    }
  }
  $report.runtime_dll_inventory=@((Get-ChildItem $root -Filter '*.dll' -File).Name | Sort-Object)
  $miles=Join-Path $root 'miles'
  New-Item -ItemType Directory -Force -Path $miles | Out-Null
  Get-ChildItem "$deps/msslib/dlls/miles" -File -ErrorAction SilentlyContinue |
      ForEach-Object { Copy-Item $_.FullName -Destination $miles -Force }

  # Windows user-mode server executable was produced from KisakCOD C++ source.
  # Input remains in this ephemeral runner; loopback-only networking.
  $launchArgs='+set net_ip 127.0.0.1 +set net_port 28960 +set sv_lanOnly 1 +set sv_punkbuster 0 +set dedicated 2 +set fs_basepath "'+$root+'" +set fs_homepath "'+$root+'" +set sv_pure 0 +set sv_maxclients 4 +set g_gametype war +map mp_crash'
  $report.arguments_redacted='+set net_ip 127.0.0.1 +set dedicated 2 +set g_gametype war +map mp_crash'
  Write-Host 'Starting KisakCOD source-built dedicated server in local-only diagnostic sandbox.'
  $process=Start-Process -FilePath (Join-Path $root 'KisakCOD-dedi.exe') -WorkingDirectory $root -ArgumentList $launchArgs -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -ErrorAction Stop
  $report.server_process_started=$true
  $exited=$process.WaitForExit(45000)
  $report.exited_early=$exited
  if ($exited) {
    $report.exit_code=$process.ExitCode
    if($process.ExitCode -eq -1073741515){$report.runtime_exception='STATUS_DLL_NOT_FOUND (0xC0000135) before game initialization'}
  } else {
    $report.server_alive_at_45_seconds=$true
  }
} catch {
  $report.runtime_exception=$_.Exception.Message
  Write-Host ("Server diagnostic issue: "+$report.runtime_exception)
} finally {
  if ($null -ne $process) {
    try {
      $process.Refresh()
      if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    } catch {}
  }
  Start-Sleep -Seconds 2
  $lines=@()
  foreach ($p in @($stdoutPath,$stderrPath)) {
    if (Test-Path $p) {
      $lines+= @(Get-Content -Path $p -ErrorAction SilentlyContinue -Tail 130)
    }
  }
  $patterns=@('could not load','failed','missing','error','SV_SpawnServer','map mp_crash','fs_game','InitGame','dedicated server')
  foreach($pattern in $patterns){
    $hits=@($lines | Where-Object { $_ -match [regex]::Escape($pattern) })
    if($hits.Count -gt 0){
      $report.runtime_log_keyword_hits+=@{ keyword=$pattern;count=$hits.Count;sample=@($hits | Select-Object -First 3) }
    }
  }
  $report.runtime_console_tail=@($lines | Select-Object -Last 110)
  $exceptionPath=Join-Path $root 'kisak-breakpoint-diagnostic.txt'
  if (Test-Path $exceptionPath) {
    $report.exception_diagnostics=@(Get-Content $exceptionPath -ErrorAction SilentlyContinue -TotalCount 60)
  } else {
    $report.exception_diagnostics=@()
    $report.early_breakpoint_before_winmain_not_excluded=$true
  }
  $report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding utf8
  Write-Host 'SERVER_BOOT_DIAGNOSTIC_BEGIN'
  Get-Content $reportPath
  Write-Host 'SERVER_BOOT_DIAGNOSTIC_END'
}
# A diagnostic is not proof that the map loaded; never silently set runtime gate green.
if (-not $report.server_process_started) { exit 0 }
