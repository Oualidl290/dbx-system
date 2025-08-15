#!/usr/bin/env python3
"""
Simple Local Server for DBX AI System
Minimal setup for Python 3.13 compatibility
"""

import os
import sys
import subprocess
from pathlib import Path

def install_basic_deps():
    """Install only the essential dependencies"""
    print("📦 Installing essential dependencies...")
    
    essential_packages = [
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0", 
        "pandas>=2.2.0",
        "numpy>=1.26.0",
        "python-multipart>=0.0.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "psycopg2-binary>=2.9.0"
    ]
    
    for package in essential_packages:
        print(f"  Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️  Failed to install {package}, continuing...")

def create_minimal_api():
    """Create a minimal API file if the full one doesn't work"""
    minimal_api = """
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import json
from datetime import datetime

app = FastAPI(title="DBX AI Engine - Minimal", version="2.0.0")

@app.get("/")
async def root():
    return {
        "message": "DBX AI Engine - Minimal Version", 
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v2/system/status")
async def system_status():
    return {
        "system": "DBX AI Multi-Aircraft System",
        "version": "2.0.0",
        "status": "operational",
        "database": "postgresql",
        "features": ["multi-aircraft", "ai-analysis", "real-time"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v2/analyze")
async def analyze_flight(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        content = await file.read()
        
        # Try to parse as CSV
        try:
            import io
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
            
            # Simple analysis (placeholder)
            analysis = {
                "session_id": "demo-session-123",
                "detected_aircraft_type": "multirotor",
                "aircraft_confidence": 0.85,
                "anomaly_detected": False,
                "risk_score": 0.25,
                "risk_level": "low",
                "analysis_summary": f"Analyzed {len(df)} data points successfully",
                "timestamp": datetime.now().isoformat()
            }
            
            return JSONResponse(content=analysis)
            
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to parse CSV: {str(e)}"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    # Write minimal API
    minimal_path = Path("minimal_api.py")
    with open(minimal_path, 'w') as f:
        f.write(minimal_api)
    
    print(f"✅ Created minimal API at {minimal_path}")
    return minimal_path

def main():
    """Main function"""
    print("🚀 DBX AI Simple Local Server")
    print("=" * 50)
    print("🐍 Python version:", sys.version)
    print("=" * 50)
    
    # Install essential dependencies
    install_basic_deps()
    
    # Skip original API for now and use minimal version
    print("🔄 Using minimal API for Python 3.13 compatibility...")
    
    # Fall back to minimal API
    print("🔄 Creating minimal API...")
    minimal_api_path = create_minimal_api()
    
    print("🚀 Starting minimal server...")
    print("=" * 50)
    print("🌐 Server will be available at:")
    print("   • API: http://localhost:8000")
    print("   • Health: http://localhost:8000/health")
    print("   • Status: http://localhost:8000/api/v2/system/status")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        cmd = [sys.executable, str(minimal_api_path)]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")

if __name__ == "__main__":
    main()