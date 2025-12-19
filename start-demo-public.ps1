# ============================
# CONFIG (EDIT THESE 3)
# ============================
$CLOUDFLARED  = "D:\Michele\Download\cloudflared-windows-amd64.exe"
$FRONTEND_DIR = "D:\Michele\DEMO_CHATBOT\frontend"
$BACKEND_DIR  = "D:\Michele\DEMO_CHATBOT"

# Ports
$FRONTEND_PORT = 5173
$BACKEND_PORT  = 8000

# Backend command (EDIT if needed)
$BACKEND_CMD = "uvicorn backend:app --host 127.0.0.1 --port $BACKEND_PORT"

# Frontend command
$FRONTEND_CMD = "npm run dev -- --host 127.0.0.1 --port $FRONTEND_PORT"

# Log files for tunnels
$LOG_DIR = Join-Path $env:TEMP "cf_tunnel_logs"
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
$BACKEND_LOG  = Join-Path $LOG_DIR "backend_tunnel.log"
$FRONTEND_LOG = Join-Path $LOG_DIR "frontend_tunnel.log"
Remove-Item -Force -ErrorAction SilentlyContinue $BACKEND_LOG, $FRONTEND_LOG

function Wait-ForTryCloudflareUrl {
  param(
    [Parameter(Mandatory=$true)][string]$LogPath,
    [int]$TimeoutSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  $pattern = 'https://[a-z0-9-]+\.trycloudflare\.com'

  while ((Get-Date) -lt $deadline) {
    if (Test-Path $LogPath) {
      $content = Get-Content $LogPath -Raw -ErrorAction SilentlyContinue
      if ($content) {
        $m = [regex]::Match($content, $pattern)
        if ($m.Success) { return $m.Value }
      }
    }
    Start-Sleep -Milliseconds 300
  }

  throw "Timed out waiting for trycloudflare URL in $LogPath"
}

function Upsert-EnvVar {
  param(
    [Parameter(Mandatory=$true)][string]$EnvFile,
    [Parameter(Mandatory=$true)][string]$Key,
    [Parameter(Mandatory=$true)][string]$Value
  )

  $line = "$Key=$Value"

  if (!(Test-Path $EnvFile)) {
    Set-Content -Path $EnvFile -Value $line -Encoding UTF8
    return
  }

  $lines = Get-Content $EnvFile -ErrorAction SilentlyContinue
  $found = $false
  $out = foreach ($l in $lines) {
    if ($l -match "^\s*$Key\s*=") {
      $found = $true
      $line
    } else {
      $l
    }
  }

  if (-not $found) {
    $out += $line
  }

  Set-Content -Path $EnvFile -Value $out -Encoding UTF8
}

Write-Host "== Starting BACKEND ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "cd `"$BACKEND_DIR`"; $BACKEND_CMD"
) | Out-Null

Start-Sleep -Seconds 2

Write-Host "== Starting BACKEND tunnel (quick) ==" -ForegroundColor Cyan
# Run cloudflared in a separate window, log to file so we can parse the URL
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "cd `"$BACKEND_DIR`"; & `"$CLOUDFLARED`" tunnel --url http://127.0.0.1:$BACKEND_PORT 2>&1 | Tee-Object -FilePath `"$BACKEND_LOG`""
) | Out-Null

$backendPublicUrl = Wait-ForTryCloudflareUrl -LogPath $BACKEND_LOG -TimeoutSeconds 60
Write-Host "Backend public URL: $backendPublicUrl" -ForegroundColor Green

Write-Host "== Updating frontend .env ==" -ForegroundColor Cyan
$envFile = Join-Path $FRONTEND_DIR ".env"
Upsert-EnvVar -EnvFile $envFile -Key "VITE_API_BASE_URL" -Value $backendPublicUrl
Write-Host "Updated $envFile with VITE_API_BASE_URL" -ForegroundColor Green

Write-Host "== Starting FRONTEND ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "cd `"$FRONTEND_DIR`"; $FRONTEND_CMD"
) | Out-Null

Start-Sleep -Seconds 3

Write-Host "== Starting FRONTEND tunnel (quick) ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "cd `"$FRONTEND_DIR`"; & `"$CLOUDFLARED`" tunnel --url http://127.0.0.1:$FRONTEND_PORT 2>&1 | Tee-Object -FilePath `"$FRONTEND_LOG`""
) | Out-Null

$frontendPublicUrl = Wait-ForTryCloudflareUrl -LogPath $FRONTEND_LOG -TimeoutSeconds 60
Write-Host ""
Write-Host "==========================" -ForegroundColor Yellow
Write-Host "✅ SHARE THIS FRONTEND URL:" -ForegroundColor Yellow
Write-Host "   $frontendPublicUrl" -ForegroundColor Yellow
Write-Host "Backend URL (already in .env):" -ForegroundColor Yellow
Write-Host "   $backendPublicUrl" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Keep all windows open to keep the tunnels alive." -ForegroundColor DarkGray
