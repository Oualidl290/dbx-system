#!/usr/bin/env python3
"""
Debug AI Detection - Simple test to understand what's happening
"""

import requests
import json
import csv
from pathlib import Path

BASE_URL = "http://localhost:8000"

def create_extreme_test_cases():
    """Create extreme test cases that should be obvious"""
    
    data_dir = Path("data/test")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Case 1: Obvious Multirotor (4 motors, low speed, hovering)
    multirotor_data = []
    for i in range(100):
        multirotor_data.append({
            'timestamp': f"2024-01-01T10:00:{i:02d}",
            'altitude': 50.0,  # Constant hover
            'battery_voltage': 12.0,
            'motor_1_rpm': 3000,  # 4 active motors
            'motor_2_rpm': 3000,
            'motor_3_rpm': 3000,
            'motor_4_rpm': 3000,
            'gps_hdop': 1.0,
            'vibration_x': 5.0,  # High vibration
            'vibration_y': 5.0,
            'vibration_z': 5.0,
            'speed': 0.5,  # Very low speed (hovering)
            'temperature': 25.0
        })
    
    # Case 2: Obvious Fixed-Wing (1 motor, high speed, stable altitude)
    fixed_wing_data = []
    for i in range(100):
        fixed_wing_data.append({
            'timestamp': f"2024-01-01T10:00:{i:02d}",
            'altitude': 200.0,  # Stable cruise altitude
            'battery_voltage': 12.0,
            'motor_1_rpm': 2500,  # Only 1 motor active
            'motor_2_rpm': 0,     # Others off
            'motor_3_rpm': 0,
            'motor_4_rpm': 0,
            'gps_hdop': 0.8,
            'vibration_x': 0.5,   # Low vibration
            'vibration_y': 0.5,
            'vibration_z': 0.2,
            'speed': 30.0,        # High cruise speed
            'temperature': 20.0,
            'elevator': 0.0,      # Control surfaces
            'aileron': 0.0,
            'rudder': 0.0
        })
    
    # Case 3: Obvious VTOL (5 motors, transition pattern)
    vtol_data = []
    for i in range(100):
        if i < 30:  # Hover phase
            motors = [3000, 3000, 3000, 3000, 500]  # 4 lift + minimal forward
            altitude = 30.0
            speed = 1.0
        elif i < 70:  # Transition phase
            motors = [2500, 2500, 2500, 2500, 3000]  # Transitioning
            altitude = 30.0 + (i-30) * 2
            speed = 1.0 + (i-30) * 0.5
        else:  # Cruise phase
            motors = [2000, 2000, 2000, 2000, 5000]  # Forward flight
            altitude = 100.0
            speed = 35.0
        
        vtol_data.append({
            'timestamp': f"2024-01-01T10:00:{i:02d}",
            'altitude': altitude,
            'battery_voltage': 12.0,
            'motor_1_rpm': motors[0],
            'motor_2_rpm': motors[1],
            'motor_3_rpm': motors[2],
            'motor_4_rpm': motors[3],
            'motor_5_rpm': motors[4],  # 5th motor
            'gps_hdop': 1.0,
            'vibration_x': 2.0,
            'vibration_y': 2.0,
            'vibration_z': 1.5,
            'speed': speed,
            'temperature': 25.0,
            'elevator': 0.0,
            'aileron': 0.0
        })
    
    # Save test cases
    test_cases = [
        (multirotor_data, "extreme_multirotor.csv", "multirotor"),
        (fixed_wing_data, "extreme_fixed_wing.csv", "fixed_wing"),
        (vtol_data, "extreme_vtol.csv", "vtol")
    ]
    
    for data, filename, expected_type in test_cases:
        filepath = data_dir / filename
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Created {filename} with {len(data)} data points")
        
        # Test this case
        test_analysis(filepath, expected_type)

def test_analysis(filepath, expected_type):
    """Test a single file analysis"""
    print(f"\n🔍 Testing {filepath.name} (expecting {expected_type})")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filepath.name, f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/api/v2/analyze", files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            detected = result.get('aircraft_type', 'unknown')
            confidence = result.get('confidence', 0.0)
            risk_level = result.get('risk_level', 'unknown')
            
            print(f"   Detected: {detected} (confidence: {confidence:.2f})")
            print(f"   Expected: {expected_type}")
            print(f"   Risk Level: {risk_level}")
            
            # Show the full result for debugging
            print(f"   Full result keys: {list(result.keys())}")
            
            if 'report' in result:
                report = result['report']
                if isinstance(report, dict):
                    print(f"   Report keys: {list(report.keys())}")
            
            correct = detected == expected_type
            status = "✅ CORRECT" if correct else "❌ WRONG"
            print(f"   Result: {status}")
            
        else:
            print(f"   ❌ API Error: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error details: {error}")
            except:
                print(f"   Response text: {response.text}")
    
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def main():
    print("🔍 DBX AI Detection Debug Test")
    print("=" * 50)
    print("Creating extreme test cases to debug aircraft detection...")
    
    # Check API
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is available")
        else:
            print("❌ API health check failed")
            return
    except:
        print("❌ Cannot connect to API")
        return
    
    # Create and test extreme cases
    create_extreme_test_cases()
    
    print("\n" + "=" * 50)
    print("Debug test complete!")
    print("\nIf all tests show 'multirotor' detection, the issue is likely:")
    print("1. The aircraft detector is using a fallback/default")
    print("2. The feature analysis isn't working as expected")
    print("3. The scoring algorithm has a bug")

if __name__ == "__main__":
    main()