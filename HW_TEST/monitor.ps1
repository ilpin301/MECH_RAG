<#
Real-time hardware/process telemetry around an ingest run.

    .\monitor.ps1            # start
    .\monitor.ps1 -Stop      # stop

Everything lands under C:\Dumps\ingest\<stamp>\ -- deliberately NOT on X:, so the
log survives a failure of the drive or controller the ingest is hammering.
Every writer flushes per line, so a hard hang keeps what was already sampled.
#>
param([switch]$Stop, [int]$IntervalSec = 5)
$ErrorActionPreference = 'Stop'
$root  = 'C:\Dumps\ingest'
$pidf  = Join-Path $root 'monitor.pids'

if ($Stop) {
  if (-not (Test-Path $pidf)) { 'monitor: nothing running (no pid file)'; return }
  Get-Content $pidf | ForEach-Object {
    $procId = [int]$_
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    "stopped $procId"
  }
  Remove-Item $pidf -Force
  return
}
if (Test-Path $pidf) { throw "monitor: already running (see $pidf) - run -Stop first" }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dir   = Join-Path $root $stamp
New-Item -ItemType Directory -Force -Path $dir | Out-Null

# one-shot context: what the machine looked like when the run started
& {
  "=== monitor start $(Get-Date -f s) interval=${IntervalSec}s ==="
  nvidia-smi -q 2>&1
  "=== disks ==="
  Get-PhysicalDisk | Select-Object DeviceId,FriendlyName,MediaType,HealthStatus | Format-Table -Auto | Out-String
  Get-Volume | Where-Object DriveLetter | Select-Object DriveLetter,FileSystemLabel,
    @{n='FreeGB';e={[math]::Round($_.SizeRemaining/1GB,1)}},HealthStatus | Format-Table -Auto | Out-String
  "=== docker ==="
  docker ps -a 2>&1
} *> (Join-Path $dir 'context.txt')

$pids = @()

# System: CPU / RAM / kernel pool / pagefile / disk queue -- pool counters matter,
# the 04-Sep bugcheck was kernel pool metadata corruption.
$counters = @(
  '\Processor Information(_Total)\% Processor Time'
  '\Processor Information(_Total)\% Processor Performance'
  '\Memory\Available MBytes'
  '\Memory\Committed Bytes'
  '\Memory\Pool Nonpaged Bytes'
  '\Memory\Pool Paged Bytes'
  '\Paging File(_Total)\% Usage'
  '\PhysicalDisk(_Total)\Current Disk Queue Length'
  '\PhysicalDisk(_Total)\Avg. Disk sec/Transfer'
  '\System\Context Switches/sec'
)
$cf = Join-Path $dir 'counters.txt'
$counters | Set-Content -LiteralPath $cf -Encoding ascii
$pids += (Start-Process typeperf -PassThru -WindowStyle Hidden -ArgumentList @(
  '-cf', "`"$cf`"", '-si', "$IntervalSec", '-f', 'CSV', '-o', "`"$(Join-Path $dir 'sys.csv')`"")).Id

# GPU + per-process, one flushed line per tick (see sampler.ps1 for why not
# nvidia-smi -f / typeperf: both would leave us with nothing after a hang).
$pids += (Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass',
  '-File', (Join-Path $PSScriptRoot 'sampler.ps1'),
  '-GpuFile',  "`"$(Join-Path $dir 'gpu.csv')`"",
  '-ProcFile', "`"$(Join-Path $dir 'proc.csv')`"",
  '-HwFile',   "`"$(Join-Path $dir 'hw.csv')`"",
  '-IntervalSec', "$IntervalSec")).Id

$pids | Set-Content -LiteralPath $pidf -Encoding ascii
"monitor started -> $dir"
"pids: $($pids -join ', ')"
