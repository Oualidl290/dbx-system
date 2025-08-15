@echo off
echo 🚀 Building DBX AI Aviation System v2.0 Docker Image
echo ===================================================

REM Set build arguments
set BUILD_DATE=%date% %time%
set VERSION=2.0.0

REM Build the production Docker image
echo 🔄 Building production image with latest architecture...
docker build -t oualidl290/dbx-ai-system:v2.0.0 ^
             -t oualidl290/dbx-ai-system:latest ^
             --build-arg BUILD_DATE="%BUILD_DATE%" ^
             --build-arg VERSION=%VERSION% ^
             --build-arg VCS_REF=%GITHUB_SHA% ^
             -f Dockerfile .

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed
    exit /b 1
)

echo ✅ Build completed successfully!

REM Get image information
echo 📊 Image information:
docker images oualidl290/dbx-ai-system

echo.
echo 🎯 Production Features:
echo   • Multi-aircraft AI system (92%% accuracy)
echo   • PostgreSQL database integration
echo   • Enterprise security (non-root user)
echo   • Multi-stage optimized build
echo   • Health checks and monitoring
echo.
echo 🧪 Test locally:
echo   docker run -p 8000:8000 -e GEMINI_API_KEY=your_key oualidl290/dbx-ai-system:v2.0.0
echo.
echo 🚀 Deploy production:
echo   docker-compose -f docker-compose.prod.yml up -d
echo.
echo 📤 Push to hub:
echo   docker push oualidl290/dbx-ai-system:v2.0.0
echo   docker push oualidl290/dbx-ai-system:latest
echo.