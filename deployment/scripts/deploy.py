#!/usr/bin/env python3
"""
Deployment script for DBX AI Multi-Aircraft System
Handles Docker deployment with proper health checks and optimization
"""

import os
import sys
import subprocess
import time
import json
import requests

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_docker():
    """Check if Docker is available"""
    return run_command("docker --version", "Checking Docker")

def check_docker_compose():
    """Check if Docker Compose is available"""
    return run_command("docker-compose --version", "Checking Docker Compose")

def build_system():
    """Build the Docker containers"""
    return run_command("docker-compose build", "Building containers")

def start_system():
    """Start the system"""
    return run_command("docker-compose up -d", "Starting system")

def check_health():
    """Check system health"""
    print("🔍 Checking system health...")
    
    # Wait for services to start
    print("⏳ Waiting for services to initialize...")
    time.sleep(30)
    
    try:
        # Check API health
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ API service is healthy")
            
            # Check system status
            status_response = requests.get("http://localhost:8000/api/v2/system/status", timeout=10)
            if status_response.status_code == 200:
                status = status_response.json()
                print("✅ Multi-aircraft system is operational")
                print(f"  • System Version: {status.get('system_version', 'Unknown')}")
                print(f"  • Supported Aircraft: {', '.join(status.get('supported_aircraft', []))}")
                print(f"  • Components: {len(status.get('components', {}))} active")
                return True
            else:
                print("⚠️ System status check failed")
                return False
        else:
            print("❌ API health check failed")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def show_endpoints():
    """Show available endpoints"""
    print("\n🌐 AVAILABLE ENDPOINTS:")
    print("  • Main API: http://localhost:8000")
    print("  • API Documentation: http://localhost:8000/docs")
    print("  • Health Check: http://localhost:8000/health")
    print("  • System Status: http://localhost:8000/api/v2/system/status")
    print("  • Aircraft Types: http://localhost:8000/api/v2/aircraft-types")
    print("  • Model Info: http://localhost:8000/api/v2/model/info")

def show_usage():
    """Show usage examples"""
    print("\n📝 USAGE EXAMPLES:")
    print("  # Upload and analyze flight log (v2 enhanced)")
    print("  curl -X POST 'http://localhost:8000/api/v2/analyze' \\")
    print("       -H 'Content-Type: multipart/form-data' \\")
    print("       -F 'file=@flight_log.csv'")
    print()
    print("  # Get supported aircraft types")
    print("  curl 'http://localhost:8000/api/v2/aircraft-types'")
    print()
    print("  # Check system status")
    print("  curl 'http://localhost:8000/api/v2/system/status'")

def main():
    """Main deployment function"""
    print("🚀 DBX AI Multi-Aircraft System Deployment")
    print("=" * 60)
    
    # Pre-flight checks
    if not check_docker():
        print("❌ Docker is required but not available")
        return False
    
    if not check_docker_compose():
        print("❌ Docker Compose is required but not available")
        return False
    
    # Check environment
    if not os.path.exists('.env'):
        print("⚠️ .env file not found - creating template...")
        env_template = """# DBX AI Multi-Aircraft System Configuration
MODEL_PATH=models/xgboost_model.pkl
SHAP_CACHE=cache/shap_values.pkl

# Gemini API key for AI-generated reports
# Get your key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Redis connection
REDIS_URL=redis://redis:6379
"""
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ Created .env template - please update with your Gemini API key")
    
    # Build and deploy
    if not build_system():
        return False
    
    if not start_system():
        return False
    
    # Health checks
    if not check_health():
        print("⚠️ System started but health checks failed")
        print("💡 Try: docker-compose logs to see what's wrong")
        return False
    
    # Success!
    print("\n🎉 DEPLOYMENT SUCCESSFUL!")
    print("=" * 60)
    
    show_endpoints()
    show_usage()
    
    print("\n🔧 MANAGEMENT COMMANDS:")
    print("  • View logs: docker-compose logs -f")
    print("  • Stop system: docker-compose down")
    print("  • Restart: docker-compose restart")
    print("  • Update: docker-compose up --build -d")
    
    print("\n✨ Your multi-aircraft system is ready for production!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)