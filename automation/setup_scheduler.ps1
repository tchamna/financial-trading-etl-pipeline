# Daily Financial Data Collection - Windows Task Scheduler Setup
# Author: Tyler Chamberlain
# Email: tyler.chamberlain@example.com

# PowerShell script to set up Windows Task Scheduler for daily data collection

param(
    [string]$ProjectPath = "C:\Users\tcham\OneDrive\Documents\Workspace_Codes\PORTFOLIO\etl-end-to-end\financial-trading-etl-pipeline",
    [string]$PythonPath = "python",
    [string]$RunTime = "06:00"  # 6:00 AM daily
)

Write-Host "Setting up Windows Task Scheduler for Daily Data Collection..." -ForegroundColor Green

# Create the task action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ProjectPath\automation\daily_data_collection.py" -WorkingDirectory $ProjectPath

# Create the task trigger (daily at specified time)
$Trigger = New-ScheduledTaskTrigger -Daily -At $RunTime

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create the principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register the scheduled task
$TaskName = "Financial-Data-Collection-Daily"
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Daily cryptocurrency minute data collection and analysis pipeline"
    Write-Host "✅ Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "   - Runs daily at $RunTime" -ForegroundColor Cyan
    Write-Host "   - Collects minute-level crypto data for previous day" -ForegroundColor Cyan
    Write-Host "   - Uploads to S3 and performs technical analysis" -ForegroundColor Cyan
    
    # Show task details
    Get-ScheduledTask -TaskName $TaskName | Format-Table -Property TaskName, State, NextRunTime
    
} catch {
    Write-Host "❌ Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "You may need to run PowerShell as Administrator" -ForegroundColor Yellow
}

Write-Host "`n📋 Manual Commands:" -ForegroundColor Yellow
Write-Host "To run the task manually:" -ForegroundColor White
Write-Host "Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan

Write-Host "`nTo view task status:" -ForegroundColor White
Write-Host "Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan

Write-Host "`nTo remove the task:" -ForegroundColor White
Write-Host "Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Cyan

Write-Host "`n🔧 Configuration:" -ForegroundColor Yellow
Write-Host "Project Path: $ProjectPath" -ForegroundColor White
Write-Host "Python Path: $PythonPath" -ForegroundColor White
Write-Host "Run Time: $RunTime" -ForegroundColor White

Write-Host "`n📊 What happens daily:" -ForegroundColor Yellow
Write-Host "1. Collect minute-level data for yesterday (8 cryptocurrencies)" -ForegroundColor White
Write-Host "2. Upload compressed data to S3 with proper partitioning" -ForegroundColor White
Write-Host "3. Perform technical analysis (RSI, SMA, volatility)" -ForegroundColor White
Write-Host "4. Generate analysis reports with trading insights" -ForegroundColor White
Write-Host "5. Clean up old data files (keep 7 days)" -ForegroundColor White
Write-Host "6. Log all activities to automation/daily_collection.log" -ForegroundColor White