#!/usr/bin/env python3
"""
DBX AI Aviation System - Production Entry Point
Clean, production-ready entry point for the refactored system
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = str(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import from new structure
try:
    from api.v2.endpoints import app
    from config.settings import get_settings
    
    print("✅ Successfully imported from new refactored structure")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Creating minimal fallback app...")
    
    from fastapi import FastAPI
    from datetime import datetime
    
    app = FastAPI(
        title="DBX AI Aviation System",
        version="2.0.0",
        description="Production-ready refactored system"
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "DBX AI Aviation System - Refactored Structure",
            "version": "2.0.0",
            "status": "fallback_mode",
            "timestamp": datetime.now().isoformat(),
            "note": "Some imports failed, running in fallback mode"
        }

def main():
    """Main entry point"""
    try:
        settings = get_settings()
        
        print(f"🚀 Starting DBX AI Aviation System v2.0.0")
        print(f"📁 Structure: Refactored Production")
        print(f"🌍 Environment: {settings.environment}")
        print(f"🔗 Host: {settings.api.host}:{settings.api.port}")
        
        uvicorn.run(
            "main:app",
            host=settings.api.host,
            port=settings.api.port,
            reload=settings.api.reload,
            workers=settings.api.workers if not settings.api.reload else 1,
            log_level=settings.logging.level.lower()
        )
        
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        print("🔄 Starting with default configuration...")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

if __name__ == "__main__":
    main()