@echo off
echo 🚀 Building DBX AI Docker Image
echo ================================

REM Build the Docker image
echo 🔄 Building image...
docker build -t oualidl290/dbx-ai-system:latest -f ai-engine/Dockerfile .

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Build failed
    exit /b 1
)

echo ✅ Build completed successfully!

REM Get image size
echo 📊 Image information:
docker images oualidl290/dbx-ai-system:latest

echo.
echo 🎯 Next steps:
echo   • Test locally: docker run -p 8000:8000 -e GEMINI_API_KEY=your_key oualidl290/dbx-ai-system:latest
echo   • Push to hub: docker push oualidl290/dbx-ai-system:latest
echo.