@echo off
echo 🚀 Pushing DBX AI Aviation System v2.0 to Docker Hub
echo ===================================================

REM Login to Docker Hub
echo 🔐 Logging into Docker Hub...
docker login

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker login failed
    exit /b 1
)

REM Push both version tags
echo 📤 Pushing versioned image...
docker push oualidl290/dbx-ai-system:v2.0.0

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Version push failed
    exit /b 1
)

echo 📤 Pushing latest tag...
docker push oualidl290/dbx-ai-system:latest

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Latest push failed
    exit /b 1
)

echo ✅ Successfully pushed to Docker Hub!
echo.
echo 🎉 Production-ready system available:
echo.
echo 🔥 Quick Start:
echo   docker pull oualidl290/dbx-ai-system:v2.0.0
echo   docker run -p 8000:8000 -e GEMINI_API_KEY=your_key oualidl290/dbx-ai-system:v2.0.0
echo.
echo 🏭 Production Deployment:
echo   docker pull oualidl290/dbx-ai-system:v2.0.0
echo   docker-compose -f docker-compose.prod.yml up -d
echo.
echo 📊 Features:
echo   • Multi-aircraft AI (Fixed-wing, Multirotor, VTOL)
echo   • 92%% aircraft detection accuracy
echo   • PostgreSQL database integration
echo   • Enterprise security and monitoring
echo   • Real-time processing (^<2 seconds)
echo.