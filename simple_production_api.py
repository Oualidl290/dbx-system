#!/usr/bin/env python3
"""
Simple API for testing the production structure
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="DBX AI Aviation System",
    version="2.0.0",
    description="Production-ready AI system for aviation safety"
)

@app.get("/")
async def root():
    return {
        "message": "DBX AI Aviation System - Production Structure",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "structure": "production-ready"
    }

@app.get("/api/v2/system/status")
async def system_status():
    return {
        "system": "DBX AI Multi-Aircraft System",
        "version": "2.0.0",
        "structure": "production-level",
        "features": [
            "Multi-tenant architecture",
            "API versioning",
            "Comprehensive testing",
            "Infrastructure as Code",
            "CI/CD pipeline"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
