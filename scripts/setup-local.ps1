# DBX AI Aviation System - Local Development Setup Script (PowerShell)
# This script sets up the complete local development environment

param(
    [switch]$SkipChecks,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Info = "Cyan"
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
}

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    $color = $Colors[$Type]
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $color
}

function Test-DockerInstallation {
    Write-Status "Checking Docker installation..." "Info"
    
    try {
        $dockerVersion = docker --version 2>$null
        if (-not $dockerVersion) {
            throw "Docker command not found"
        }
        Write-Status "Docker is installed: $dockerVersion" "Success"
    }
    catch {
        Write-Status "Docker is not installed. Please install Docker Desktop first." "Error"
        Write-Status "Download from: https://www.docker.com/products/docker-desktop" "Info"
        exit 1
    }
    
    try {
        docker info 2>$null | Out-Null
        Write-Status "Docker is running" "Success"
    }
    catch {
        Write-Status "Docker is not running. Please start Docker Desktop first." "Error"
        exit 1
    }
    
    # Check for docker-compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            $script:DockerCompose = "docker-compose"
            Write-Status "Docker Compose is available: $composeVersion" "Success"
        }
        else {
            $composeVersion = docker compose version 2>$null
            if ($composeVersion) {
                $script:DockerCompose = "docker compose"
                Write-Status "Docker Compose is available: $composeVersion" "Success"
            }
            else {
                throw "Docker Compose not found"
            }
        }
    }
    catch {
        Write-Status "Docker Compose is not available. Please install Docker Compose." "Error"
        exit 1
    }
}

function New-RequiredDirectories {
    Write-Status "Creating necessary directories..." "Info"
    
    $directories = @(
        "data\models",
        "data\training_data", 
        "data\uploads",
        "data\results",
        "data\cache",
        "data\test",
        "logs",
        "docker\postgres\init-scripts",
        "docker\pgadmin"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            if ($Verbose) {
                Write-Status "Created directory: $dir" "Info"
            }
        }
    }
    
    Write-Status "Directories created successfully" "Success"
}

function Initialize-Environment {
    Write-Status "Setting up environment configuration..." "Info"
    
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.local" ".env"
        Write-Status "Environment file created (.env)" "Success"
        Write-Status "Please edit .env file to configure your settings (especially GEMINI_API_KEY)" "Warning"
    }
    else {
        Write-Status ".env file already exists, skipping..." "Warning"
    }
}

function Start-Services {
    Write-Status "Building and starting services..." "Info"
    
    # Stop any existing services
    Write-Status "Stopping any existing services..." "Info"
    & $DockerCompose -f docker-compose.local.yml down 2>$null
    
    # Build application image
    Write-Status "Building application image..." "Info"
    & $DockerCompose -f docker-compose.local.yml build dbx-app
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to build application image" "Error"
        exit 1
    }
    
    # Start database and cache services
    Write-Status "Starting database and cache services..." "Info"
    & $DockerCompose -f docker-compose.local.yml up -d dbx-postgres dbx-redis
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to start database services" "Error"
        exit 1
    }
    
    # Wait for database
    Write-Status "Waiting for database to be ready..." "Info"
    Start-Sleep -Seconds 30
    
    # Start application
    Write-Status "Starting application..." "Info"
    & $DockerCompose -f docker-compose.local.yml up -d dbx-app
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Failed to start application" "Error"
        exit 1
    }
    
    Write-Status "All services started successfully" "Success"
}

function Wait-ForServices {
    Write-Status "Waiting for services to be healthy..." "Info"
    
    # Wait for PostgreSQL
    Write-Status "Waiting for PostgreSQL..." "Info"
    $timeout = 60
    $ready = $false
    
    while ($timeout -gt 0 -and -not $ready) {
        try {
            docker exec dbx-postgres pg_isready -U postgres -d dbx_aviation 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                Write-Status "PostgreSQL is ready" "Success"
            }
        }
        catch {
            # Continue waiting
        }
        
        if (-not $ready) {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if (-not $ready) {
        Write-Status "PostgreSQL failed to start within 60 seconds" "Error"
        exit 1
    }
    
    # Wait for Redis
    Write-Status "Waiting for Redis..." "Info"
    $timeout = 30
    $ready = $false
    
    while ($timeout -gt 0 -and -not $ready) {
        try {
            docker exec dbx-redis redis-cli ping 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $ready = $true
                Write-Status "Redis is ready" "Success"
            }
        }
        catch {
            # Continue waiting
        }
        
        if (-not $ready) {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if (-not $ready) {
        Write-Status "Redis failed to start within 30 seconds" "Error"
        exit 1
    }
    
    # Wait for application
    Write-Status "Waiting for application..." "Info"
    $timeout = 60
    $ready = $false
    
    while ($timeout -gt 0 -and -not $ready) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $ready = $true
                Write-Status "Application is ready" "Success"
            }
        }
        catch {
            # Continue waiting
        }
        
        if (-not $ready) {
            Start-Sleep -Seconds 3
            $timeout -= 3
        }
    }
    
    if (-not $ready) {
        Write-Status "Application may not be fully ready yet, but continuing..." "Warning"
    }
}

function Show-Information {
    Write-Host ""
    Write-Host "🎉 DBX AI Aviation System is now running locally!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Service URLs:" -ForegroundColor Cyan
    Write-Host "   • Application API: http://localhost:8000"
    Write-Host "   • API Documentation: http://localhost:8000/docs"
    Write-Host "   • Health Check: http://localhost:8000/health"
    Write-Host ""
    Write-Host "🗄️  Database Connections:" -ForegroundColor Cyan
    Write-Host "   • PostgreSQL: localhost:5432"
    Write-Host "   • Database: dbx_aviation"
    Write-Host "   • Username: postgres"
    Write-Host "   • Password: password"
    Write-Host ""
    Write-Host "🔄 Cache:" -ForegroundColor Cyan
    Write-Host "   • Redis: localhost:6379"
    Write-Host ""
    Write-Host "🔧 Management Tools (optional):" -ForegroundColor Cyan
    Write-Host "   • Start pgAdmin: $DockerCompose -f docker-compose.local.yml --profile tools up -d dbx-pgadmin"
    Write-Host "   • pgAdmin URL: http://localhost:5050 (admin@dbx-ai.com / admin123)"
    Write-Host "   • Start Redis Commander: $DockerCompose -f docker-compose.local.yml --profile tools up -d dbx-redis-commander"
    Write-Host "   • Redis Commander URL: http://localhost:8081"
    Write-Host ""
    Write-Host "📝 Default Credentials:" -ForegroundColor Cyan
    Write-Host "   • Admin User: admin@dbx-ai.com / admin123"
    Write-Host "   • Sample Aircraft: TEST-001, TEST-002, TEST-003"
    Write-Host ""
    Write-Host "🛠️  Useful Commands:" -ForegroundColor Cyan
    Write-Host "   • View logs: $DockerCompose -f docker-compose.local.yml logs -f"
    Write-Host "   • Stop services: $DockerCompose -f docker-compose.local.yml down"
    Write-Host "   • Restart app: $DockerCompose -f docker-compose.local.yml restart dbx-app"
    Write-Host "   • Database shell: docker exec -it dbx-postgres psql -U postgres -d dbx_aviation"
    Write-Host "   • Redis shell: docker exec -it dbx-redis redis-cli"
    Write-Host "   • Test API: python scripts/test-api.py"
    Write-Host ""
    Write-Host "⚠️  Important Notes:" -ForegroundColor Yellow
    Write-Host "   • Edit .env file to configure your Gemini API key"
    Write-Host "   • This is a development setup - not for production use"
    Write-Host "   • Default passwords should be changed for any non-local use"
    Write-Host ""
}

function Test-Setup {
    Write-Status "Running basic API test..." "Info"
    
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try {
            python scripts/test-api.py
            if ($LASTEXITCODE -eq 0) {
                Write-Status "API test completed successfully!" "Success"
            }
            else {
                Write-Status "API test completed with some issues. Check the output above." "Warning"
            }
        }
        catch {
            Write-Status "Could not run API test. You can run it manually later: python scripts/test-api.py" "Warning"
        }
    }
    else {
        Write-Status "Python not found. You can test the API manually at http://localhost:8000/docs" "Warning"
    }
}

# Main execution
function Main {
    Write-Host "🔧 DBX AI Aviation System - Local Development Setup" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        if (-not $SkipChecks) {
            Test-DockerInstallation
        }
        
        New-RequiredDirectories
        Initialize-Environment
        Start-Services
        Wait-ForServices
        Show-Information
        
        if (-not $SkipChecks) {
            Test-Setup
        }
        
        Write-Status "Setup completed successfully! 🎉" "Success"
    }
    catch {
        Write-Status "Setup failed: $($_.Exception.Message)" "Error"
        Write-Status "Check the error above and try running the script again." "Info"
        exit 1
    }
}

# Run main function
Main