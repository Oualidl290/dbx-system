#!/usr/bin/env python3
"""
Live Demo Script for Presentation
Run this during your presentation to show the system working
"""

import requests
import json
import time
import os

def demo_system_status():
    """Demo 1: Show system health"""
    print("🔍 DEMO 1: System Health Check")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/v2/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ System Status: OPERATIONAL")
            print(f"📊 Version: {data.get('system_version', 'Unknown')}")
            print(f"🛠️ Components Active: {len([k for k, v in data.get('components', {}).items() if v == 'active'])}/5")
            print(f"✈️ Supported Aircraft: {', '.join(data.get('supported_aircraft', []))}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the system is running: python deploy.py")
        return False

def demo_aircraft_types():
    """Demo 2: Show supported aircraft types"""
    print("\n🔍 DEMO 2: Aircraft Type Detection")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/v2/aircraft-types", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Aircraft Detection Capabilities:")
            
            for aircraft in data.get('supported_types', []):
                print(f"\n✈️ {aircraft['name']}:")
                print(f"   • Type: {aircraft['type']}")
                print(f"   • Motors: {aircraft['typical_characteristics']['motor_count']}")
                print(f"   • VTOL Capable: {aircraft['typical_characteristics']['vertical_takeoff_capable']}")
                print(f"   • Speed Range: {aircraft['typical_characteristics']['cruise_speed_range']} m/s")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def demo_model_evaluation():
    """Demo 3: Run model evaluation"""
    print("\n🔍 DEMO 3: Model Performance Evaluation")
    print("=" * 50)
    
    print("🤖 Running live model evaluation...")
    os.system("python simple_evaluation.py")
    
    print("\n📊 Generated Visualizations:")
    if os.path.exists("reports/confusion_matrix.png"):
        print("   ✅ Confusion Matrix: reports/confusion_matrix.png")
    if os.path.exists("reports/feature_importance.png"):
        print("   ✅ Feature Importance: reports/feature_importance.png")

def demo_file_analysis():
    """Demo 4: Simulate file analysis"""
    print("\n🔍 DEMO 4: Flight Log Analysis Simulation")
    print("=" * 50)
    
    # Simulate analysis results
    sample_result = {
        "aircraft_type": "multirotor",
        "confidence": 0.94,
        "risk_score": 0.23,
        "risk_level": "LOW",
        "anomalies": [],
        "processing_time": "1.8s",
        "flight_statistics": {
            "flight_duration": "420 seconds",
            "max_altitude": "85.3 m",
            "avg_speed": "12.4 m/s",
            "battery_consumption": "2.1 V"
        },
        "ai_summary": "Normal multirotor flight detected. All parameters within safe operating limits. No anomalies found."
    }
    
    print("📁 Analyzing sample flight log...")
    time.sleep(2)  # Simulate processing time
    
    print("✅ Analysis Complete!")
    print(f"✈️ Aircraft Type: {sample_result['aircraft_type'].upper()} (confidence: {sample_result['confidence']:.1%})")
    print(f"⚠️ Risk Level: {sample_result['risk_level']} (score: {sample_result['risk_score']:.2f})")
    print(f"⏱️ Processing Time: {sample_result['processing_time']}")
    print(f"🧠 AI Summary: {sample_result['ai_summary']}")

def show_demo_fallbacks():
    """Show fallback options if live demo fails"""
    print("\n🛡️ DEMO FALLBACK OPTIONS")
    print("=" * 50)
    print("If live demo fails, you have these backups:")
    print("1. 📊 Pre-generated plots in reports/ folder")
    print("2. 📋 Sample JSON responses in demo_outputs/")
    print("3. 🎥 Recorded demo video (if available)")
    print("4. 📖 Static documentation and validation report")

def main():
    """Run complete demo sequence"""
    print("🚀 DBX AI SYSTEM - LIVE DEMONSTRATION")
    print("=" * 60)
    
    # Check if system is running
    system_ok = demo_system_status()
    
    if system_ok:
        demo_aircraft_types()
        demo_file_analysis()
    else:
        print("\n⚠️ System not running - showing offline capabilities:")
    
    demo_model_evaluation()
    show_demo_fallbacks()
    
    print("\n🎯 DEMO COMPLETE")
    print("=" * 60)
    print("Questions? Let's dive deeper into any aspect!")

if __name__ == "__main__":
    main()