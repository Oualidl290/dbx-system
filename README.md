DBX AI is a comprehensive system for analyzing drone flight logs using advanced machine learning and AI-generated insights. Built to compete with and surpass existing solutions like AirData.

## 🎯 Key Features

- **🤖 AI-Powered Analysis**: Multi-Aircraft XGBoost anomaly detection
- **🔍 SHAP Explanations**: Aircraft-specific explainable AI insights  
- **📝 AI Reports**: Gemini-powered intelligent flight analysis
- **🐳 Docker Ready**: Fully containerized for easy deployment
- **📊 Multiple Formats**: Supports CSV, MAVLink (.bin), ULog files
- **⚡ Real-time API**: FastAPI backend with async processing
- **🔬 Jupyter Notebooks**: Interactive analysis and training

## 🏗️ Architecture

```
dbx-ai/
├── ai-engine/           # Python AI/ML Engine
│   ├── app/
│   │   ├── models/      # ML models & SHAP explainer
│   │   ├── services/    # Log parser & report generator  
│   │   └── api.py       # FastAPI endpoints
│   └── Dockerfile
├── notebooks/           # Jupyter analysis notebooks
├── docker-compose.yml   # Full system orchestration
└── data/               # Logs, models, reports storage
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo>
cd dbx-ai
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
# Add your OpenAI API key for AI reports (optional)
```

### 3. Launch with Docker
```bash
# Start all services
docker-compose
