# Quick fix and restart script for DBX AI Aviation System

Write-Host "🔧 Fixing and restarting DBX AI Aviation System..." -ForegroundColor Cyan

# Stop all services
Write-Host "[INFO] Stopping all services..." -ForegroundColor Yellow
docker compose -f docker-compose.local.yml down

# Remove any problematic volumes
Write-Host "[INFO] Cleaning up volumes..." -ForegroundColor Yellow
docker volume prune -f

# Start services one by one
Write-Host "[INFO] Starting PostgreSQL..." -ForegroundColor Green
docker compose -f docker-compose.local.yml up -d dbx-postgres

# Wait for PostgreSQL
Write-Host "[INFO] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$timeout = 60
$ready = $false

while ($timeout -gt 0 -and -not $ready) {
    try {
        docker exec dbx-postgres pg_isready -U postgres -d dbx_aviation 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            Write-Host "[SUCCESS] PostgreSQL is ready!" -ForegroundColor Green
        }
    }
    catch {
        # Continue waiting
    }
    
    if (-not $ready) {
        Start-Sleep -Seconds 2
        $timeout -= 2
        Write-Host "  Waiting... ($timeout seconds remaining)" -ForegroundColor Gray
    }
}

if (-not $ready) {
    Write-Host "[ERROR] PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}

# Start Redis
Write-Host "[INFO] Starting Redis..." -ForegroundColor Green
docker compose -f docker-compose.local.yml up -d dbx-redis

# Wait for Redis
Write-Host "[INFO] Waiting for Redis..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start application
Write-Host "[INFO] Starting application..." -ForegroundColor Green
docker compose -f docker-compose.local.yml up -d dbx-app

# Wait for application
Write-Host "[INFO] Waiting for application to be ready..." -ForegroundColor Yellow
$timeout = 60
$ready = $false

while ($timeout -gt 0 -and -not $ready) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            Write-Host "[SUCCESS] Application is ready!" -ForegroundColor Green
        }
    }
    catch {
        # Continue waiting
    }
    
    if (-not $ready) {
        Start-Sleep -Seconds 3
        $timeout -= 3
        Write-Host "  Waiting... ($timeout seconds remaining)" -ForegroundColor Gray
    }
}

if ($ready) {
    Write-Host ""
    Write-Host "🎉 DBX AI Aviation System is now running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Service URLs:" -ForegroundColor Cyan
    Write-Host "   • Application: http://localhost:8000" -ForegroundColor White
    Write-Host "   • API Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   • Health Check: http://localhost:8000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "🧪 Test the setup:" -ForegroundColor Cyan
    Write-Host "   python scripts/test-api.py" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[WARNING] Application may not be fully ready yet" -ForegroundColor Yellow
    Write-Host "Check logs with: docker compose -f docker-compose.local.yml logs -f dbx-app" -ForegroundColor Gray
}