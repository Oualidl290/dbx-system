@echo off
REM DBX AI Aviation System - Local Development Setup Script (Windows)
REM This script sets up the complete local development environment

setlocal enabledelayedexpansion

echo 🚀 Setting up DBX AI Aviation System for local development...

REM Check if Docker is installed and running
echo [INFO] Checking Docker installation...

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check for docker-compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose is not available. Please install Docker Compose.
        pause
        exit /b 1
    ) else (
        set DOCKER_COMPOSE=docker compose
    )
) else (
    set DOCKER_COMPOSE=docker-compose
)

echo [SUCCESS] Docker is installed and running

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "data" mkdir data
if not exist "data\models" mkdir data\models
if not exist "data\training_data" mkdir data\training_data
if not exist "data\uploads" mkdir data\uploads
if not exist "data\results" mkdir data\results
if not exist "data\cache" mkdir data\cache
if not exist "logs" mkdir logs
if not exist "docker" mkdir docker
if not exist "docker\postgres" mkdir docker\postgres
if not exist "docker\postgres\init-scripts" mkdir docker\postgres\init-scripts
if not exist "docker\pgadmin" mkdir docker\pgadmin

echo [SUCCESS] Directories created

REM Setup environment file
echo [INFO] Setting up environment configuration...
if not exist ".env" (
    copy ".env.local" ".env" >nul
    echo [SUCCESS] Environment file created (.env)
    echo [WARNING] Please edit .env file to configure your settings (especially GEMINI_API_KEY)
) else (
    echo [WARNING] .env file already exists, skipping...
)

REM Build and start services
echo [INFO] Building and starting services...

echo [INFO] Stopping any existing services...
%DOCKER_COMPOSE% -f docker-compose.local.yml down

echo [INFO] Building application image...
%DOCKER_COMPOSE% -f docker-compose.local.yml build dbx-app

echo [INFO] Starting database and cache services...
%DOCKER_COMPOSE% -f docker-compose.local.yml up -d dbx-postgres dbx-redis

echo [INFO] Waiting for database to be ready...
timeout /t 30 /nobreak >nul

echo [INFO] Starting application...
%DOCKER_COMPOSE% -f docker-compose.local.yml up -d dbx-app

echo [SUCCESS] All services started successfully

REM Wait for services to be healthy
echo [INFO] Waiting for services to be healthy...

REM Wait for PostgreSQL
echo [INFO] Waiting for PostgreSQL...
set timeout=60
:wait_postgres
docker exec dbx-postgres pg_isready -U postgres -d dbx_aviation >nul 2>&1
if errorlevel 1 (
    if !timeout! gtr 0 (
        timeout /t 2 /nobreak >nul
        set /a timeout-=2
        goto wait_postgres
    ) else (
        echo [ERROR] PostgreSQL failed to start within 60 seconds
        pause
        exit /b 1
    )
)
echo [SUCCESS] PostgreSQL is ready

REM Wait for Redis
echo [INFO] Waiting for Redis...
set timeout=30
:wait_redis
docker exec dbx-redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    if !timeout! gtr 0 (
        timeout /t 2 /nobreak >nul
        set /a timeout-=2
        goto wait_redis
    ) else (
        echo [ERROR] Redis failed to start within 30 seconds
        pause
        exit /b 1
    )
)
echo [SUCCESS] Redis is ready

REM Wait for application
echo [INFO] Waiting for application...
set timeout=60
:wait_app
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    if !timeout! gtr 0 (
        timeout /t 3 /nobreak >nul
        set /a timeout-=3
        goto wait_app
    ) else (
        echo [WARNING] Application may not be fully ready yet, but continuing...
    )
) else (
    echo [SUCCESS] Application is ready
)

REM Display connection information
echo.
echo 🎉 DBX AI Aviation System is now running locally!
echo.
echo 📊 Service URLs:
echo    • Application API: http://localhost:8000
echo    • API Documentation: http://localhost:8000/docs
echo    • Health Check: http://localhost:8000/health
echo.
echo 🗄️  Database Connections:
echo    • PostgreSQL: localhost:5432
echo    • Database: dbx_aviation
echo    • Username: postgres
echo    • Password: password
echo.
echo 🔄 Cache:
echo    • Redis: localhost:6379
echo.
echo 🔧 Management Tools (optional):
echo    • Start pgAdmin: %DOCKER_COMPOSE% -f docker-compose.local.yml --profile tools up -d dbx-pgadmin
echo    • pgAdmin URL: http://localhost:5050 (admin@dbx-ai.com / admin123)
echo    • Start Redis Commander: %DOCKER_COMPOSE% -f docker-compose.local.yml --profile tools up -d dbx-redis-commander
echo    • Redis Commander URL: http://localhost:8081
echo.
echo 📝 Default Credentials:
echo    • Admin User: admin@dbx-ai.com / admin123
echo    • Sample Aircraft: TEST-001, TEST-002, TEST-003
echo.
echo 🛠️  Useful Commands:
echo    • View logs: %DOCKER_COMPOSE% -f docker-compose.local.yml logs -f
echo    • Stop services: %DOCKER_COMPOSE% -f docker-compose.local.yml down
echo    • Restart app: %DOCKER_COMPOSE% -f docker-compose.local.yml restart dbx-app
echo    • Database shell: docker exec -it dbx-postgres psql -U postgres -d dbx_aviation
echo    • Redis shell: docker exec -it dbx-redis redis-cli
echo.
echo ⚠️  Important Notes:
echo    • Edit .env file to configure your Gemini API key
echo    • This is a development setup - not for production use
echo    • Default passwords should be changed for any non-local use
echo.

echo [SUCCESS] Setup completed successfully! 🎉

pause