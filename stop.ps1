# Windows Script zum Bot stoppen

Write-Host "⏹️  Stopping Bot..." -ForegroundColor Cyan

if (Test-Path "bot\bot.pid") {
    $BotPID = Get-Content "bot\bot.pid" -ErrorAction SilentlyContinue
    if ($BotPID -and $BotPID -match '^\d+$') {
        $process = Get-Process -Id $BotPID -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "🛑 Stopping bot (PID: $BotPID)..." -ForegroundColor Yellow
            Stop-Process -Id $BotPID -Force
            Start-Sleep -Seconds 1
            Write-Host "✅ Bot stopped successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Bot process not found (PID: $BotPID)" -ForegroundColor Yellow
        }
    }
    Remove-Item "bot\bot.pid" -ErrorAction SilentlyContinue
} else {
    Write-Host "ℹ️  No bot.pid file found. Bot might not be running." -ForegroundColor Yellow
}

