@echo off
echo 💾 Save Docker Image for Windows Sharing
echo =========================================

echo 📦 Saving Docker image to tar file...
docker save -o dbx-ai-system.tar oualidl290/dbx-ai-system:latest

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Save failed
    exit /b 1
)

echo ✅ Image saved successfully!

echo.
echo 📊 File information:
dir dbx-ai-system.tar

echo.
echo 🎯 How to share with friends:
echo.
echo METHOD 1 - Direct File Sharing:
echo 1. Send them the file: dbx-ai-system.tar
echo 2. They run: docker load -i dbx-ai-system.tar
echo 3. They run: docker run -p 8000:8000 -e GEMINI_API_KEY=their_key oualidl290/dbx-ai-system:latest
echo.
echo METHOD 2 - Cloud Storage:
echo 1. Upload dbx-ai-system.tar to Google Drive/Dropbox
echo 2. Share the download link
echo 3. Friends download and load with: docker load -i dbx-ai-system.tar
echo.
echo 📏 File size: 
for %%A in (dbx-ai-system.tar) do echo %%~zA bytes (approximately %%~zA bytes)
echo.
echo 🎉 Ready to share!
echo.