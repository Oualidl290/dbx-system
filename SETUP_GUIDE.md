# DBX AI - Complete Setup Guide
## Step-by-Step Installation and Training Documentation

This document provides a complete walkthrough of setting up the DBX AI drone flight log analysis system from scratch.

## 🎯 What is DBX AI?

DBX AI is a comprehensive multi-aircraft system for analyzing drone flight logs using advanced machine learning and AI-generated insights. It uses:
- **Multi-Aircraft XGBoost** for specialized anomaly detection
- **Aircraft-Specific SHAP** for explainable AI insights
- **Google Gemini** for intelligent flight analysis reports
- **FastAPI** for REST API
- **Redis** for caching and queuing
- **Docker** for containerization

## 📋 Prerequisites

Before starting, ensure you have:
- Windows 10/11 with PowerShell
- Docker Desktop installed and running
- Git (optional, for version control)
- Text editor (VS Code recommended)

## 🚀 Step 1: Project Structure Setup

### 1.1 Create Main Directory
```powershell
mkdir dbx_ai
cd dbx_ai
```

### 1.2 Create Project Structure
```powershell
# Create main directories
mkdir ai-engine
mkdir ai-engine\app
mkdir ai-engine\app\models
mkdir ai-engine\app\services
mkdir data
mkdir data\models
mkdir data\cache
mkdir data\logs
mkdir data\reports
mkdir data\uploads
mkdir data\results
mkdir data\temp
mkdir notebooks
```

Final structure should look like:
```
dbx_ai/
├── ai-engine/           # Python AI/ML Engine
│   ├── app/
│   │   ├── models/      # ML models & SHAP explainer
│   │   ├── services/    # Log parser & report generator
│   │   ├── api.py       # FastAPI endpoints
│   │   └── config.py    # Configuration settings
│   ├── Dockerfile       # Container definition
│   └── requirements.txt # Python dependencies
├── data/               # Data storage
│   ├── models/         # Trained ML models
│   ├── cache/          # SHAP cache
│   ├── logs/           # Input flight logs
│   ├── reports/        # Generated reports
│   ├── uploads/        # Uploaded files
│   ├── results/        # Analysis results
│   └── temp/           # Temporary files
├── notebooks/          # Jupyter analysis notebooks
├── docker-compose.yml  # Service orchestration
├── .env               # Environment variables
└── README.md          # Project documentation
```

## 🔧 Step 2: Configuration Files

### 2.1 Create Environment File (.env)
```bash
# Model and cache paths
MODEL_PATH=models/xgboost_model.pkl
SHAP_CACHE=cache/shap_values.pkl

# OpenAI API key for AI-generated reports (optional)
# Get your key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Redis connection
REDIS_URL=redis://redis:6379
```

### 2.2 Create Docker Compose File (docker-compose.yml)
```yaml
# docker-compose.yml
services:
  ai-engine:
    build: ./ai-engine
    ports:
      - "8000:8000"
    volumes:
      - ./ai-engine/app:/app/app
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 2.3 Create Python Requirements (ai-engine/requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
numpy==1.25.2
scikit-learn==1.3.2
xgboost==2.0.1
shap==0.43.0
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0
openai==1.3.6
python-multipart==0.0.6
aiofiles==23.2.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
jinja2==3.1.2
weasyprint==60.2
celery[redis]==5.3.4
redis>=4.5.2,<5.0.0
pymavlink==2.4.37
```

### 2.4 Create Dockerfile (ai-engine/Dockerfile)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 🧠 Step 3: Machine Learning Components

### 3.1 Configuration Module (ai-engine/app/config.py)
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"
    MODEL_VERSION: str = "v1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.2 Anomaly Detection Model (ai-engine/app/models/model.py)
This file contains:
- **AnomalyDetector class** - Main ML model wrapper
- **XGBoost classifier** for anomaly detection
- **Synthetic data generation** for initial training
- **Feature engineering** for flight log data
- **Risk scoring** and anomaly identification

Key features:
- Automatically trains initial model with synthetic data
- Supports 12 flight parameters (altitude, battery, motors, GPS, vibration, etc.)
- Generates risk scores from 0-1 (LOW/MEDIUM/HIGH)
- Identifies specific anomalies with descriptions

### 3.3 SHAP Explainer (ai-engine/app/models/shap_explainer.py)
This file provides:
- **Explainable AI** using SHAP values
- **Feature importance** ranking
- **Human-readable explanations** of model decisions
- **Top contributing factors** identification

## 🔍 Step 4: Data Processing Services

### 4.1 Log Parser (ai-engine/app/services/parser.py)
Supports multiple drone log formats:
- **CSV files** - Standard comma-separated data
- **MAVLink binary logs** (.bin, .log) - ArduPilot format
- **ULog files** - PX4 flight stack format

Features:
- Automatic format detection
- Data cleaning and normalization
- Missing value handling
- Synthetic data generation for testing

### 4.2 Report Generator (ai-engine/app/services/report_generator.py)
Generates comprehensive analysis reports:
- **Flight statistics** (duration, altitude, battery usage)
- **Risk assessment** with scoring
- **AI-powered summaries** using OpenAI GPT
- **Actionable recommendations**
- **Technical details** and metadata

## 🌐 Step 5: API Layer

### 5.1 FastAPI Application (ai-engine/app/api.py)
Provides REST API endpoints:

**Core Endpoints:**
- `GET /` - System status
- `GET /health` - Health check
- `GET /api/v1/model/info` - Model information

**Analysis Endpoints:**
- `POST /api/v1/analyze` - Direct synchronous analysis
- `POST /api/v1/upload` - Async file upload and analysis
- `GET /api/v1/analysis/{id}` - Get analysis results

**Features:**
- File upload handling
- Background task processing
- JSON serialization of numpy types
- CORS support for web frontends

## 🏗️ Step 6: Build and Deploy

### 6.1 Build Docker Images
```powershell
# Navigate to project directory
cd dbx_ai

# Build and start services
docker-compose up --build -d
```

### 6.2 Verify Installation
```powershell
# Check service status
docker-compose ps

# Test API endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/model/info
```

### 6.3 View Logs
```powershell
# Check application logs
docker-compose logs ai-engine

# Follow logs in real-time
docker-compose logs -f ai-engine
```

## 🧪 Step 7: Testing the System

### 7.1 Create Test Data
Create a sample CSV file with flight data:
```csv
timestamp,altitude,battery_voltage,motor_1_rpm,motor_2_rpm,motor_3_rpm,motor_4_rpm,gps_hdop,vibration_x,vibration_y,vibration_z,speed,temperature
2024-01-15 10:00:00,0,12.6,0,0,0,0,1.2,0.1,0.1,0.1,0,25
2024-01-15 10:00:01,5,12.5,2800,2850,2820,2830,1.1,0.2,0.1,0.2,2,25
...
```

### 7.2 Test Analysis
```powershell
# Test direct analysis
curl -X POST -F "file=@test_flight.csv" http://localhost:8000/api/v1/analyze
```

## 🎓 Step 8: Understanding the ML Training Process

### 8.1 Automatic Model Training
The system automatically trains an initial model when first started:

1. **Synthetic Data Generation**:
   - Creates 10,000 samples (80% normal, 20% anomalous)
   - Simulates realistic flight parameters
   - Includes various failure modes (battery issues, motor failures, GPS problems)

2. **Feature Engineering**:
   - 12 key flight parameters
   - Standardized scaling
   - Missing value handling

3. **Model Training**:
   - XGBoost classifier for anomaly detection
   - 100 estimators, max depth 6
   - Cross-validation for performance

4. **Model Persistence**:
   - Saves trained model to `data/models/xgboost_model.pkl`
   - Saves scaler to `data/models/scaler.pkl`

### 8.2 Retraining Process
To retrain with new data:
1. Collect labeled flight logs
2. Use the `retrain()` method in AnomalyDetector
3. Model automatically saves updated version

## 🔧 Step 9: Troubleshooting

### 9.1 Common Issues

**Docker Desktop not running:**
```powershell
# Start Docker Desktop manually or run:
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

**Dependency conflicts:**
- Check requirements.txt versions
- Rebuild containers: `docker-compose up --build -d`

**API errors:**
- Check logs: `docker-compose logs ai-engine`
- Verify file formats and data structure

**Memory issues:**
- Reduce SHAP sample size in explainer
- Use smaller datasets for testing

### 9.2 Performance Optimization

**For large datasets:**
- Implement data sampling
- Use batch processing
- Add database storage

**For production:**
- Add authentication
- Implement rate limiting
- Use production WSGI server

## 📊 Step 10: Understanding the Analysis Output

### 10.1 Risk Scoring
- **0.0 - 0.3**: LOW risk (normal flight)
- **0.3 - 0.7**: MEDIUM risk (some anomalies)
- **0.7 - 1.0**: HIGH risk (multiple anomalies)

### 10.2 Anomaly Types
The system detects:
- Battery voltage issues
- Motor performance problems
- GPS signal degradation
- Excessive vibration
- Altitude anomalies
- Temperature extremes

### 10.3 SHAP Explanations
- Feature importance scores
- Positive/negative impact indicators
- Top contributing factors
- Human-readable explanations

## 🚀 Step 11: Next Steps

### 11.1 Production Deployment
- Set up proper database (PostgreSQL)
- Implement user authentication
- Add monitoring and logging
- Set up CI/CD pipeline

### 11.2 Model Improvements
- Collect real flight data
- Implement active learning
- Add more sophisticated features
- Experiment with deep learning models

### 11.3 Feature Enhancements
- Real-time streaming analysis
- Web dashboard interface
- Mobile app integration
- Advanced visualization tools

## 📝 Summary

This guide covered the complete setup of DBX AI from scratch:

1. ✅ Project structure creation
2. ✅ Configuration files setup
3. ✅ Machine learning model implementation
4. ✅ Data processing services
5. ✅ REST API development
6. ✅ Docker containerization
7. ✅ Testing and validation
8. ✅ ML training process
9. ✅ Troubleshooting guide
10. ✅ Analysis interpretation

The system is now ready to analyze real drone flight logs and provide AI-powered insights for flight safety and performance optimization.

## 🔗 Quick Reference

**Start System:**
```powershell
docker-compose up -d
```

**Stop System:**
```powershell
docker-compose down
```

**View API Documentation:**
http://localhost:8000/docs

**Test Analysis:**
```powershell
curl -X POST -F "file=@your_log.csv" http://localhost:8000/api/v1/analyze
```

**Check Status:**
```powershell
curl http://localhost:8000/health
```