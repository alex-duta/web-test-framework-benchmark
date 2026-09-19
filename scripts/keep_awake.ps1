# Keeps Windows from idle-sleeping while run_measurements.sh runs.
# It asks Windows to stay awake for as long as this process runs (SetThreadExecutionState with
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED); no power setting is changed. The process exits on its own
# when the process ParentPid (the measurement script) ends, or after Seconds at the latest.
param([int]$ParentPid = 0, [int]$Seconds = 43200)
if (-not $ParentPid) { Write-Output "keep-awake: no parent process given, exiting"; exit 1 }
$k = Add-Type -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);' -Name K -Namespace W -PassThru
$null = $k::SetThreadExecutionState([uint32]"0x80000001")
Write-Output "keep-awake active (pid $PID, parent $ParentPid)"
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end) {
    # stop as soon as the measurement script has ended
    if (-not (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue)) { break }
    Start-Sleep 5
}
