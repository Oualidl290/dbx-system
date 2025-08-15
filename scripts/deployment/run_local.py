#!/usr/bin/env python3
"""
Local Development Server for DBX AI System
Runs the FastAPI application directly without Docker
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'scikit-learn',
        'xgboost',
        'psycopg2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "-r", "ai-engine/requirements.txt"
        ])
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies available")

def setup_environment():
    """Setup environment variables"""
    print("🔧 Setting up environment...")
    
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        print("  ✅ Found .env file")
        from dotenv import load_dotenv
        load_dotenv()
    else:
        print("  ⚠️  No .env file found, using defaults")
    
    # Set default environment variables
    defaults = {
        'PYTHONPATH': str(Path.cwd()),
        'MODEL_VERSION': 'v2.0.0',
        'DEBUG': 'true',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"  ✅ Set {key}={value}")

def check_database():
    """Check database connection"""
    print("🗄️  Checking database connection...")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        # Try to connect
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database='dbx_aviation'
        )
        conn.close()
        print("  ✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"  ⚠️  Database connection failed: {e}")
        print("  💡 Run database setup first: python database/setup_database.py")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting DBX AI Server...")
    print("=" * 50)
    
    # Change to ai-engine directory
    os.chdir("ai-engine")
    
    # Start uvicorn server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("=" * 50)
    print("🌐 Server will be available at:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🚀 DBX AI Local Development Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("ai-engine").exists():
        print("❌ ai-engine directory not found!")
        print("Make sure you're running this from the project root directory")
        sys.exit(1)
    
    # Run setup steps
    steps = [
        ("Checking dependencies", check_dependencies),
        ("Setting up environment", setup_environment),
        ("Checking database", check_database),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        try:
            result = step_func()
            if result is False:
                print(f"⚠️  {step_name} had issues, but continuing...")
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            if "database" not in step_name.lower():
                sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Setup completed! Starting server...")
    print("=" * 50)
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()