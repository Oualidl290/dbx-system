
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
