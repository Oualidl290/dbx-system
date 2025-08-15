# DBX AI Aviation System v2.0 - PowerShell Build Script
Write-Host "🚀 Building DBX AI Aviation System v2.0 Docker Image" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

# Set build arguments
$BUILD_DATE = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$VERSION = "2.0.0"

Write-Host "🔄 Building production image with latest architecture..." -ForegroundColor Yellow

# Build the Docker image
docker build -t oualidl290/dbx-ai-system:v2.0.0 `
             -t oualidl290/dbx-ai-system:latest `
             --build-arg BUILD_DATE="$BUILD_DATE" `
             --build-arg VERSION=$VERSION `
             -f Dockerfile .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Build completed successfully!" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "📊 Image information:" -ForegroundColor Cyan
    docker images oualidl290/dbx-ai-system
    
    Write-Host ""
    Write-Host "🎯 Production Features:" -ForegroundColor Cyan
    Write-Host "  • Multi-aircraft AI system (92% accuracy)" -ForegroundColor White
    Write-Host "  • PostgreSQL database integration" -ForegroundColor White
    Write-Host "  • Enterprise security (non-root user)" -ForegroundColor White
    Write-Host "  • Multi-stage optimized build" -ForegroundColor White
    Write-Host "  • Health checks and monitoring" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🧪 Test locally:" -ForegroundColor Yellow
    Write-Host "  docker run -p 8000:8000 -e GEMINI_API_KEY=your_key oualidl290/dbx-ai-system:v2.0.0" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🚀 Deploy production:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.prod.yml up -d" -ForegroundColor White
} else {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}