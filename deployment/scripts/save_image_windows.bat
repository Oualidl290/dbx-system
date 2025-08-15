@echo off
echo 💾 Save DBX AI Aviation System v2.0 for Sharing
echo ===============================================

echo 📦 Saving production Docker image to tar file...
docker save -o dbx-ai-system-v2.0.tar oualidl290/dbx-ai-system:v2.0.0

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Save failed
    exit /b 1
)

echo ✅ Image saved successfully!

echo.
echo 📊 File information:
dir dbx-ai-system-v2.0.tar

echo.
echo 🎯 How to share the production system:
echo.
echo METHOD 1 - Direct File Sharing:
echo 1. Send them: dbx-ai-system-v2.0.tar
echo 2. They run: docker load -i dbx-ai-system-v2.0.tar
echo 3. They run: docker run -p 8000:8000 -e GEMINI_API_KEY=their_key oualidl290/dbx-ai-system:v2.0.0
echo.
echo METHOD 2 - Production Deployment:
echo 1. Share: dbx-ai-system-v2.0.tar + docker-compose.prod.yml
echo 2. They run: docker load -i dbx-ai-system-v2.0.tar
echo 3. They run: docker-compose -f docker-compose.prod.yml up -d
echo.
echo METHOD 3 - Cloud Storage:
echo 1. Upload dbx-ai-system-v2.0.tar to Google Drive/Dropbox
echo 2. Share download link
echo 3. Include setup instructions
echo.
echo 🚀 What they get:
echo   • Multi-aircraft AI system (92%% accuracy)
echo   • Production-ready architecture
echo   • PostgreSQL database integration
echo   • Enterprise security features
echo   • Real-time processing (^<2 seconds)
echo   • Complete API documentation at /docs
echo.
echo 📏 File size: 
for %%A in (dbx-ai-system-v2.0.tar) do echo %%~zA bytes
echo.
echo 🎉 Production system ready to share!
echo.