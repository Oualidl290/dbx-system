#!/usr/bin/env python3
"""
DBX AI Aviation System - API Test Script
Simple script to test the local development environment
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_system_status():
    """Test the system status endpoint"""
    print("🔍 Testing system status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System status: {data.get('system', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Features: {len(data.get('features', {}))}")
            return True
        else:
            print(f"❌ System status failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ System status failed: {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible"""
    print("🔍 Testing API documentation...")
    try:
        # Try the v2 docs endpoint first
        response = requests.get(f"{BASE_URL}/api/v2/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation is accessible at /api/v2/docs")
            return True
        
        # Fallback to /docs
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation is accessible at /docs")
            return True
        else:
            print(f"❌ API documentation failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation failed: {e}")
        return False

def create_sample_csv():
    """Create a sample flight log CSV for testing"""
    csv_content = """timestamp,altitude,battery_voltage,motor_1_rpm,motor_2_rpm,motor_3_rpm,motor_4_rpm,gps_hdop,vibration_x,vibration_y,vibration_z,speed,temperature
2024-01-01T10:00:00,100.5,12.6,3000,3010,2990,3005,1.2,0.1,0.2,0.1,5.5,25.3
2024-01-01T10:00:01,101.2,12.5,3100,3110,3090,3105,1.1,0.2,0.1,0.2,6.2,25.4
2024-01-01T10:00:02,102.1,12.4,3200,3210,3190,3205,1.0,0.1,0.3,0.1,7.1,25.5
2024-01-01T10:00:03,103.5,12.3,3300,3310,3290,3305,0.9,0.3,0.2,0.3,8.0,25.6
2024-01-01T10:00:04,105.2,12.2,3400,3410,3390,3405,0.8,0.2,0.4,0.2,8.8,25.7
"""
    
    # Create data directory if it doesn't exist
    data_dir = Path("data/test")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write sample CSV
    csv_file = data_dir / "sample_flight_log.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    return csv_file

def test_flight_analysis():
    """Test flight log analysis endpoint"""
    print("🔍 Testing flight log analysis...")
    
    # Create sample CSV
    csv_file = create_sample_csv()
    
    try:
        with open(csv_file, 'rb') as f:
            files = {'file': ('sample_flight_log.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/api/v2/analyze", 
                files=files, 
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flight analysis successful!")
            print(f"   Analysis ID: {data.get('analysis_id', 'unknown')}")
            print(f"   Aircraft Type: {data.get('aircraft_type', 'unknown')}")
            print(f"   Confidence: {data.get('confidence', 0):.2f}")
            print(f"   Risk Level: {data.get('risk_level', 'unknown')}")
            return True
        else:
            print(f"❌ Flight analysis failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Flight analysis failed: {e}")
        return False

def test_recent_analyses():
    """Test recent analyses endpoint"""
    print("🔍 Testing recent analyses endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v2/analyses", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recent analyses retrieved: {data.get('total', 0)} analyses")
            return True
        else:
            print(f"❌ Recent analyses failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Recent analyses failed: {e}")
        return False

def wait_for_service():
    """Wait for the service to be available"""
    print("⏳ Waiting for service to be available...")
    
    for i in range(TIMEOUT):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ Service is available!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"   Waiting... ({i+1}/{TIMEOUT})")
        time.sleep(1)
    
    print("❌ Service did not become available within timeout")
    return False

def main():
    """Run all tests"""
    print("🧪 DBX AI Aviation System - API Test Suite")
    print("=" * 50)
    
    # Wait for service
    if not wait_for_service():
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("System Status", test_system_status),
        ("API Documentation", test_api_docs),
        ("Flight Analysis", test_flight_analysis),
        ("Recent Analyses", test_recent_analyses),
    ]
    
    passed = 0
    total = len(tests)
    
    print("\n🔬 Running Tests:")
    print("-" * 30)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your local environment is working correctly.")
        print("\n🚀 Next steps:")
        print("   • Visit http://localhost:8000/docs for API documentation")
        print("   • Upload your own flight logs for analysis")
        print("   • Explore the database with pgAdmin at http://localhost:5050")
        return 0
    else:
        print(f"❌ {total - passed} tests failed. Please check the logs and configuration.")
        print("\n🔧 Troubleshooting:")
        print("   • Check if all services are running: docker-compose -f docker-compose.local.yml ps")
        print("   • View logs: docker-compose -f docker-compose.local.yml logs -f")
        print("   • Restart services: docker-compose -f docker-compose.local.yml restart")
        return 1

if __name__ == "__main__":
    sys.exit(main())