<#
Per-tick sampler for monitor.ps1: GPU + board/CPU sensors + ingest processes,
one flushed line each. Runs under Windows PowerShell 5.1 (.NET Framework) --
LibreHardwareMonitorLib is a net472 build and will not load under pwsh 7.

Why this exists instead of the built-in loggers:
  * nvidia-smi -l -f BUFFERS. A full test run left gpu.csv at 0 bytes -- after a
    hard hang the GPU log, the whole point of the exercise, would be empty.
  * typeperf binds \Process(...) instances at start, so a python that appears
    later never gets a column. This loop re-resolves every tick.
Add-Content opens and closes per line, so what is sampled is on disk.

LHM needs the PawnIO kernel driver for anything below user mode: IntelMSR.bin for
the i7-2600K core temps, LpcIO.bin for the Nuvoton NCT6776F. Without it you still
get GPU (NVML) and drive temps (WMI), so the sensor block degrades, never throws.
NCT6776F rail names are the chip's raw channels: "Voltage #6" is not labelled +12V
because the ASUS scaling factor is unknown here. Read them as deltas, not absolutes.
#>
param(
  [Parameter(Mandatory=$true)][string]$GpuFile,
  [Parameter(Mandatory=$true)][string]$ProcFile,
  [Parameter(Mandatory=$true)][string]$HwFile,
  [int]$IntervalSec = 5,
  [string]$LhmDll = 'C:\Dumps\tools\lhm\LibreHardwareMonitorLib.dll'
)

# Format numbers invariantly. The first version used {N:N1}, whose thousands separator
# turned a 2403.0 MB working set into "2,403.0" and split it across two CSV columns -- every
# row for a process over 1 GB was silently misaligned. F1 plus invariant culture also stops a
# comma decimal separator appearing under a non-English locale.
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture

$gpuFields = 'timestamp,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,' +
             'power.draw,clocks.sm,clocks.mem,clocks_throttle_reasons.active,pstate,fan.speed,' +
             'ecc.errors.uncorrected.volatile.total,pcie.link.gen.current,pcie.link.width.current'
$gpuFields | Set-Content -LiteralPath $GpuFile -Encoding ascii
'time,name,pid,cpu_s,ws_mb,private_mb,threads,handles' | Set-Content -LiteralPath $ProcFile -Encoding ascii
'time,hardware,type,sensor,value' | Set-Content -LiteralPath $HwFile -Encoding ascii

# --- LibreHardwareMonitor: opened once, updated per tick (Add-Type per tick would
#     cost seconds). Any failure here must not take the other two loggers down.
$computer = $null
try {
  Add-Type -Path $LhmDll
  $computer = New-Object LibreHardwareMonitor.Hardware.Computer
  $computer.IsCpuEnabled = $true; $computer.IsMotherboardEnabled = $true
  $computer.IsMemoryEnabled = $true; $computer.IsStorageEnabled = $true
  $computer.IsGpuEnabled = $true;   $computer.IsControllerEnabled = $true
  $computer.Open()
} catch {
  "# LHM unavailable: $($_.Exception.Message)" | Add-Content -LiteralPath $HwFile -Encoding ascii
  $computer = $null
}
# Load/Data/Factor/Level are static or already covered by typeperf and proc.csv.
$keep = 'Temperature','Voltage','Fan','Power','Clock','Control','Throughput'

function Write-Sensors($hw, $t) {
  $hw.Update()
  foreach ($s in $hw.Sensors) {
    if ($null -ne $s.Value -and $keep -contains $s.SensorType.ToString()) {
      '{0},{1},{2},{3},{4}' -f $t, ($hw.Name -replace ',',' '), $s.SensorType,
        ($s.Name -replace ',',' '), [math]::Round($s.Value, 2) |
        Add-Content -LiteralPath $HwFile -Encoding ascii
    }
  }
  foreach ($sub in $hw.SubHardware) { Write-Sensors $sub $t }
}

while ($true) {
  $tick = Get-Date
  $t = $tick.ToString('s')

  $gpu = & nvidia-smi "--query-gpu=$gpuFields" --format=csv,noheader,nounits 2>&1
  if ($gpu) { $gpu | Add-Content -LiteralPath $GpuFile -Encoding ascii }

  if ($computer) {
    try { foreach ($hw in $computer.Hardware) { Write-Sensors $hw $t } }
    catch { "$t,LHM,Error,tick,$($_.Exception.Message -replace ',',';')" | Add-Content -LiteralPath $HwFile -Encoding ascii }
  }

  foreach ($p in Get-Process python,pythonw,mineru,pwsh,dockerd,'com.docker.backend' -ErrorAction SilentlyContinue) {
    '{0},{1},{2},{3:F1},{4:F1},{5:F1},{6},{7}' -f $t,$p.ProcessName,$p.Id,$p.CPU,
      ($p.WorkingSet64/1MB),($p.PrivateMemorySize64/1MB),$p.Threads.Count,$p.HandleCount |
      Add-Content -LiteralPath $ProcFile -Encoding ascii
  }

  # sleep the remainder, so sampling time does not stretch the interval
  $rest = $IntervalSec - ((Get-Date) - $tick).TotalSeconds
  if ($rest -gt 0) { Start-Sleep -Milliseconds ([int]($rest * 1000)) }
}
