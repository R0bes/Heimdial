# Windows Deployment Script
# Stoppt den Bot, pulled den neuesten Code und startet den Bot neu

Write-Host "🔄 Deploying Bot..." -ForegroundColor Cyan

# Bot stoppen
if (Test-Path "bot\bot.pid") {
    $BotPID = Get-Content "bot\bot.pid"
    $process = Get-Process -Id $BotPID -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "⏹️  Stopping bot (PID: $BotPID)..." -ForegroundColor Yellow
        Stop-Process -Id $BotPID -Force
        Start-Sleep -Seconds 2
    }
    Remove-Item "bot\bot.pid" -ErrorAction SilentlyContinue
}

# Git pull
Write-Host "📥 Pulling latest code..." -ForegroundColor Cyan
git pull

# Dependencies installieren
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
cd bot
pip install -r requirements.txt

# Environment Variables laden (falls .env existiert)
if (Test-Path ".env") {
    Write-Host "📝 Loading environment variables from .env..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Bot starten
Write-Host "🚀 Starting bot..." -ForegroundColor Cyan

$process = Start-Process -FilePath "python" -ArgumentList "bot.py" -PassThru -NoNewWindow -RedirectStandardOutput "bot.log" -RedirectStandardError "bot.log"
$process.Id | Out-File -FilePath "bot.pid" -Encoding ASCII

Start-Sleep -Seconds 2

# Verifizieren
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Write-Host "✅ Bot deployed successfully! (PID: $($process.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Bot failed to start. Check bot.log" -ForegroundColor Red
    Get-Content "bot.log" -ErrorAction SilentlyContinue
    exit 1
}

cd ..

