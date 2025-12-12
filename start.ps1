# Windows Script zum Bot starten (ohne Deployment)
# Verwendet .env Datei oder Environment Variables

Write-Host "🚀 Starting Bot..." -ForegroundColor Cyan

# Prüfen ob Bot bereits läuft
if (Test-Path "bot\bot.pid") {
    $BotPID = Get-Content "bot\bot.pid"
    $process = Get-Process -Id $BotPID -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "⚠️  Bot is already running (PID: $BotPID)" -ForegroundColor Yellow
        Write-Host "   Use stop.ps1 to stop it first, or deploy.ps1 to restart" -ForegroundColor Yellow
        exit 1
    } else {
        Remove-Item "bot\bot.pid" -ErrorAction SilentlyContinue
    }
}

# Environment Variables laden (falls .env existiert)
if (Test-Path ".env") {
    Write-Host "📝 Loading environment variables from .env..." -ForegroundColor Cyan
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            $parts = $line -split '=', 2
            if ($parts.Length -eq 2) {
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                Write-Host "   ✓ Loaded $key" -ForegroundColor Gray
            }
        }
    }
} else {
    Write-Host "⚠️  No .env file found. Make sure environment variables are set!" -ForegroundColor Yellow
}

# Prüfen ob Environment Variables gesetzt sind
if (-not $env:BOT_TOKEN) {
    Write-Host "❌ BOT_TOKEN not set!" -ForegroundColor Red
    Write-Host "   Create a .env file or set environment variables" -ForegroundColor Yellow
    exit 1
}

if (-not $env:ALLOWED_USER_IDS) {
    Write-Host "❌ ALLOWED_USER_IDS not set!" -ForegroundColor Red
    exit 1
}

if (-not $env:WEBAPP_URL) {
    Write-Host "❌ WEBAPP_URL not set!" -ForegroundColor Red
    exit 1
}

# Dependencies prüfen
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
cd bot
$pipCheck = python -m pip show python-telegram-bot 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
}

# Bot starten
Write-Host "🤖 Starting bot..." -ForegroundColor Cyan
$process = Start-Process -FilePath "python" -ArgumentList "bot.py" -PassThru -NoNewWindow -RedirectStandardOutput "bot.log" -RedirectStandardError "bot_error.log"
$process.Id | Out-File -FilePath "bot.pid" -Encoding ASCII

Start-Sleep -Seconds 2

# Verifizieren
if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
    Write-Host "✅ Bot started successfully! (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "📋 Logs: bot\bot.log" -ForegroundColor Cyan
    Write-Host "🛑 Stop with: .\stop.ps1" -ForegroundColor Cyan
} else {
    Write-Host "❌ Bot failed to start. Check bot.log" -ForegroundColor Red
    Get-Content "bot.log" -ErrorAction SilentlyContinue
    exit 1
}

cd ..

