# PowerShell script to create Windows Task Scheduler task
# Run as Administrator

$taskName = "EmailTodoExtractor"
$taskPath = "\"
$scriptPath = "$PSScriptRoot\start_windows.bat"
$pythonPath = (Get-Command python).Source

# Create the action
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $PSScriptRoot

# Create triggers (run at startup and every 30 minutes)
$triggerStartup = New-ScheduledTaskTrigger -AtStartup
$triggerPeriodic = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 3 `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -TaskPath $taskPath `
    -Action $action `
    -Trigger $triggerStartup, $triggerPeriodic `
    -Settings $settings `
    -RunLevel Highest `
    -Description "Monitors emails and extracts todo items"

Write-Host "Task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "The task will run at startup and every 30 minutes." -ForegroundColor Yellow
Write-Host "To start immediately, run: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Cyan