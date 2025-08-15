@echo off
echo 🚀 Pushing DBX AI Docker Image to Hub
echo ====================================

REM Login to Docker Hub
echo 🔐 Logging into Docker Hub...
docker login

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Docker login failed
    exit /b 1
)

REM Push the image
echo 📤 Pushing image to Docker Hub...
docker push oualidl290/dbx-ai-system:latest

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Push failed
    exit /b 1
)

echo ✅ Successfully pushed to Docker Hub!
echo.
echo 🎉 Your friends can now run:
echo   docker pull oualidl290/dbx-ai-system:latest
echo   docker run -p 8000:8000 -e GEMINI_API_KEY=their_key oualidl290/dbx-ai-system:latest
echo.