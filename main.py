#!/usr/bin/env python3
"""
DBX AI Aviation System - Production Entry Point
Refactored clean production entry point
"""

import sys
import os
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = str(current_dir / "src")
sys.path.insert(0, src_dir)

try:
    from src.main import main
    print("✅ Using refactored production structure")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Import error from refactored structure: {e}")
    print("🔄 Falling back to working ai-engine structure...")
    
    # Fallback to ai-engine structure
    ai_engine_path = str(current_dir / "ai-engine" / "app")
    sys.path.insert(0, ai_engine_path)
    
    try:
        import uvicorn
        from api import app
        
        print("✅ Using ai-engine fallback structure")
        
        if __name__ == "__main__":
            uvicorn.run(
                "api:app",
                host="0.0.0.0",
                port=8000,
                reload=False
            )
            
    except ImportError as e2:
        print(f"❌ Both structures failed: {e2}")
        print("🆘 Creating emergency minimal API...")
        
        from fastapi import FastAPI
        from datetime import datetime
        import uvicorn
        
        app = FastAPI(title="DBX AI Aviation System", version="2.0.0")
        
        @app.get("/")
        async def root():
            return {
                "message": "DBX AI Aviation System - Emergency Mode",
                "version": "2.0.0",
                "status": "emergency_fallback",
                "timestamp": datetime.now().isoformat(),
                "note": "System is in emergency mode - please check configuration"
            }
        
        if __name__ == "__main__":
            uvicorn.run(app, host="0.0.0.0", port=8000)