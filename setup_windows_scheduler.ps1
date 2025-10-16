# ===================================================================
# WINDOWS TASK SCHEDULER - ALTERNATIVE TO AIRFLOW
# ===================================================================
# Since Airflow doesn't run on Windows, use Windows Task Scheduler instead

# This PowerShell script creates a Windows Task Scheduler job that runs
# the ETL pipeline every 6 hours

Write-Host "Creating Windows Task Scheduler Job..." -ForegroundColor Cyan
Write-Host ""

# Configuration
$taskName = "FinancialCryptoETL"
$scriptPath = "$PSScriptRoot\automation\daily_data_collection.py"
$pythonPath = "$PSScriptRoot\venv\Scripts\python.exe"
$workingDir = $PSScriptRoot

# Calculate start time (5 minutes from now)
$startTime = (Get-Date).AddMinutes(5)

# Create the scheduled task action (what to run)
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $workingDir

# Create the trigger (when to run - every 6 hours)
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At $startTime `
    -RepetitionInterval (New-TimeSpan -Hours 6) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Create the task settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the scheduled task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Financial Crypto ETL Pipeline - Runs every 6 hours" `
    -Force

Write-Host "SUCCESS! Scheduled task created:" -ForegroundColor Green
Write-Host "  Name: $taskName" -ForegroundColor Yellow
Write-Host "  First Run: $startTime" -ForegroundColor Yellow
Write-Host "  Frequency: Every 6 hours" -ForegroundColor Yellow
Write-Host ""
Write-Host "To manage the task:" -ForegroundColor Cyan
Write-Host "  1. Open Task Scheduler: Win+R -> taskschd.msc" -ForegroundColor White
Write-Host "  2. Find task: $taskName" -ForegroundColor White
Write-Host "  3. Right-click to Run, Disable, or Delete" -ForegroundColor White
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  Check automation/logs/ folder" -ForegroundColor White
Write-Host ""

# Display task info
Write-Host "Task Details:" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Gray
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, @{Name='NextRunTime';Expression={(Get-ScheduledTaskInfo $_).NextRunTime}}
