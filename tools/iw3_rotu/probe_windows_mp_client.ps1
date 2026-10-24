param(
  [Parameter(Mandatory=$true)][string]$GameRoot,
  [Parameter(Mandatory=$true)][string]$ClientExecutable,
  [Parameter(Mandatory=$true)][string]$ReportDir,
  [int]$ServerPort=28960
)
$ErrorActionPreference='Stop'
New-Item -Type Directory -Force -Path $ReportDir | Out-Null
$reportPath=Join-Path $ReportDir 'mp-client-loopback-report.json'
$stdout=Join-Path $ReportDir 'client-stdout.txt'
$stderr=Join-Path $ReportDir 'client-stderr.txt'
$report=[ordered]@{
  test='Windows KisakCOD source-built client -> source-built dedicated localhost'
  server_endpoint='127.0.0.1:28960'
  source_built_client_detected=$false
  client_process_started=$false
  client_alive_after_16s=$false
  client_exit_code=$null
  connection_attempt_sent=$false
  udp_server_status_replied_after_client_attempt=$false
  server_reports_connected_player=$false
  first_player_record_redacted=$null
  gameplay_verified=$false
  zombies_verified=$false
  error=$null
}
$proc=$null
try {
  if (!(Test-Path $ClientExecutable)) { throw 'Client executable not found' }
  $exe=Join-Path $GameRoot 'KisakCOD-mp.exe'
  Copy-Item -Path $ClientExecutable -Destination $exe -Force
  $pdb=[IO.Path]::ChangeExtension($ClientExecutable,'.pdb')
  if(Test-Path $pdb){Copy-Item $pdb -Destination (Join-Path $GameRoot 'KisakCOD-mp.pdb') -Force}
  $report.source_built_client_detected=$true
  # Only local connection is requested. This is a disposable CI process,
  # never a remote server or networked public session.
  $argsLine='+set fs_basepath "'+$GameRoot+'" +set fs_homepath "'+$GameRoot+'" +set r_fullscreen 0 +set r_mode 4 +set net_ip 127.0.0.1 +connect 127.0.0.1:'+([string]$ServerPort)
  Write-Host 'Launching native Windows MP client and attempting localhost game connection.'
  $proc=Start-Process -FilePath $exe -WorkingDirectory $GameRoot -ArgumentList $argsLine -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr -ErrorAction Stop
  $report.client_process_started=$true
  $report.connection_attempt_sent=$true
  $hasExited=$proc.WaitForExit(16000)
  if($hasExited){$report.client_exit_code=$proc.ExitCode}else{$report.client_alive_after_16s=$true}
  # Actual server UDP response and explicit player records, not a process PID,
  # are the only valid evidence for a completed client-server join.
  $query=[byte[]](@(255,255,255,255)+[Text.Encoding]::ASCII.GetBytes("getstatus"+[char]10))
  $udp=[Net.Sockets.UdpClient]::new()
  try {
    $udp.Client.ReceiveTimeout=2200
    $udp.Connect('127.0.0.1',$ServerPort)
    [void]$udp.Send($query,$query.Length)
    $remote=[Net.IPEndPoint]::new([Net.IPAddress]::Any,0)
    $reply=[Text.Encoding]::ASCII.GetString($udp.Receive([ref]$remote))
    $report.udp_server_status_replied_after_client_attempt=($reply.Contains('statusResponse'))
    $lines=@($reply -split '[\r\n]+' | Where-Object {$_ -match '^\s*[0-9]+\s+[0-9]+\s+"[^"]+"'})
    $report.server_reports_connected_player=($lines.Count -gt 0)
    if($lines.Count -gt 0){$report.first_player_record_redacted='Score/ping/player row present, identifying name not stored'}
  } catch {
    $report.udp_server_status_error=$_.Exception.GetType().Name
  } finally {
    $udp.Dispose()
  }
} catch {
  $report.error=$_.Exception.Message
} finally {
  if($null -ne $proc){
    try {
      $proc.Refresh()
      if(-not $proc.HasExited){Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}
    }catch{}
  }
  $report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding utf8
  Write-Host "CLIENT_LOOPBACK_DIAGNOSTIC_BEGIN"
  Get-Content $reportPath
  Write-Host "CLIENT_LOOPBACK_DIAGNOSTIC_END"
}
# Non-connecting clients are a measured RED gate, not a CI script exception.
