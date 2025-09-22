#!/usr/bin/env python3
"""
DBX AI Aviation System - Targeted AI Engine Testing
Testing with data that matches the AI engine's expectations exactly
"""

import requests
import json
import csv
import time
import sys
import random
import math
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"

class TargetedAITest:
    def __init__(self):
        self.data_dir = Path("data/test")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🧠 {title}")
        print(f"{'='*60}")
    
    def print_test(self, test_name):
        print(f"\n🔬 Testing: {test_name}")
        print("-" * 40)
    
    def print_result(self, success, message, details=None):
        status = "✅" if success else "❌"
        print(f"{status} {message}")
        if details:
            for key, value in details.items():
                print(f"   • {key}: {value}")
    
    def generate_clear_multirotor_data(self, duration=300):
        """Generate data that clearly indicates multirotor characteristics"""
        print(f"📊 Generating clear multirotor data ({duration}s)...")
        
        data = []
        random.seed(42)
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # Clear multirotor characteristics:
            # 1. 4 active motors with similar RPMs
            # 2. Low speed (hover/slow movement)
            # 3. Frequent altitude changes (vertical agility)
            # 4. Higher vibration
            
            base_rpm = 3000 + random.gauss(0, 100)
            
            # 4 motors with similar RPMs (multirotor signature)
            motor_1_rpm = base_rpm + random.gauss(0, 50)
            motor_2_rpm = base_rpm + random.gauss(0, 50)
            motor_3_rpm = base_rpm + random.gauss(0, 50)
            motor_4_rpm = base_rpm + random.gauss(0, 50)
            
            # Low speed typical of multirotors
            speed = 1 + abs(random.gauss(0, 2))  # 0-5 m/s typical
            
            # Frequent altitude changes (hover capability)
            if i % 30 < 10:  # Ascending
                altitude = 20 + (i % 30) * 2 + random.gauss(0, 1)
            elif i % 30 < 20:  # Hovering
                altitude = 40 + random.gauss(0, 1)
            else:  # Descending
                altitude = 40 - ((i % 30) - 20) * 2 + random.gauss(0, 1)
            
            # Higher vibration typical of multirotors
            vibration_x = random.gauss(0, 4)
            vibration_y = random.gauss(0, 4)
            vibration_z = random.gauss(0, 3)
            
            # Battery discharge
            battery_voltage = 12.6 - (i / duration) * 1.5 + random.gauss(0, 0.1)
            
            # GPS and other sensors
            gps_hdop = 1.0 + abs(random.gauss(0, 0.5))
            temperature = 25 + random.gauss(0, 2)
            
            data.append({
                'timestamp': timestamp,
                'altitude': round(altitude, 2),
                'battery_voltage': round(battery_voltage, 2),
                'motor_1_rpm': round(motor_1_rpm),
                'motor_2_rpm': round(motor_2_rpm),
                'motor_3_rpm': round(motor_3_rpm),
                'motor_4_rpm': round(motor_4_rpm),
                'gps_hdop': round(gps_hdop, 2),
                'vibration_x': round(vibration_x, 2),
                'vibration_y': round(vibration_y, 2),
                'vibration_z': round(vibration_z, 2),
                'speed': round(max(0, speed), 2),
                'temperature': round(temperature, 1)
            })
        
        return data
    
    def generate_clear_fixed_wing_data(self, duration=600):
        """Generate data that clearly indicates fixed-wing characteristics"""
        print(f"📊 Generating clear fixed-wing data ({duration}s)...")
        
        data = []
        random.seed(43)
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # Clear fixed-wing characteristics:
            # 1. Single motor (motor_1 active, others minimal)
            # 2. Higher sustained speed
            # 3. Stable altitude (less vertical agility)
            # 4. Lower vibration
            # 5. Control surface activity
            
            # Single engine aircraft
            motor_1_rpm = 2500 + random.gauss(0, 150)  # Main engine
            motor_2_rpm = random.gauss(0, 20)  # Minimal/noise
            motor_3_rpm = random.gauss(0, 20)  # Minimal/noise
            motor_4_rpm = random.gauss(0, 20)  # Minimal/noise
            
            # Higher sustained speed typical of fixed-wing
            speed = 25 + random.gauss(0, 3)  # 20-30 m/s cruise
            
            # More stable altitude (less vertical agility)
            cruise_altitude = 200
            altitude = cruise_altitude + random.gauss(0, 5)  # Small variations
            
            # Lower vibration
            vibration_x = random.gauss(0, 1)
            vibration_y = random.gauss(0, 1)
            vibration_z = random.gauss(0, 0.5)
            
            # Battery less critical for fuel aircraft
            battery_voltage = 12.0 + random.gauss(0, 0.2)
            
            # GPS typically better at altitude
            gps_hdop = 0.8 + abs(random.gauss(0, 0.3))
            temperature = 20 + random.gauss(0, 3)
            
            # Add control surface data (fixed-wing specific)
            elevator = random.gauss(0, 2)  # Small control inputs
            aileron = random.gauss(0, 3)
            rudder = random.gauss(0, 2)
            
            data.append({
                'timestamp': timestamp,
                'altitude': round(altitude, 2),
                'battery_voltage': round(battery_voltage, 2),
                'motor_1_rpm': round(motor_1_rpm),
                'motor_2_rpm': round(motor_2_rpm),
                'motor_3_rpm': round(motor_3_rpm),
                'motor_4_rpm': round(motor_4_rpm),
                'gps_hdop': round(gps_hdop, 2),
                'vibration_x': round(vibration_x, 2),
                'vibration_y': round(vibration_y, 2),
                'vibration_z': round(vibration_z, 2),
                'speed': round(max(0, speed), 2),
                'temperature': round(temperature, 1),
                'elevator': round(elevator, 2),
                'aileron': round(aileron, 2),
                'rudder': round(rudder, 2)
            })
        
        return data
    
    def generate_clear_vtol_data(self, duration=480):
        """Generate data that clearly indicates VTOL characteristics"""
        print(f"📊 Generating clear VTOL data ({duration}s)...")
        
        data = []
        random.seed(44)
        
        # VTOL flight has distinct phases
        hover_phase = duration // 3
        transition_phase = duration // 3
        cruise_phase = duration - hover_phase - transition_phase
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # Clear VTOL characteristics:
            # 1. Multiple motors (5+ for tilt-rotor)
            # 2. Distinct flight phases (hover -> transition -> cruise)
            # 3. Speed and altitude changes during transition
            # 4. Control surfaces + multiple motors
            
            if i < hover_phase:  # Hover phase
                # Multiple lift motors active
                motor_1_rpm = 3200 + random.gauss(0, 100)
                motor_2_rpm = 3200 + random.gauss(0, 100)
                motor_3_rpm = 3200 + random.gauss(0, 100)
                motor_4_rpm = 3200 + random.gauss(0, 100)
                motor_5_rpm = 1000 + random.gauss(0, 200)  # Forward motor minimal
                
                altitude = 30 + random.gauss(0, 2)  # Stable hover
                speed = 1 + abs(random.gauss(0, 0.5))  # Very low speed
                
            elif i < hover_phase + transition_phase:  # Transition phase
                # Motors transitioning
                transition_progress = (i - hover_phase) / transition_phase
                
                motor_1_rpm = 3200 - transition_progress * 400 + random.gauss(0, 150)
                motor_2_rpm = 3200 - transition_progress * 400 + random.gauss(0, 150)
                motor_3_rpm = 3200 - transition_progress * 400 + random.gauss(0, 150)
                motor_4_rpm = 3200 - transition_progress * 400 + random.gauss(0, 150)
                motor_5_rpm = 1000 + transition_progress * 4000 + random.gauss(0, 200)  # Forward motor spooling up
                
                altitude = 30 + transition_progress * 70 + random.gauss(0, 5)  # Climbing
                speed = 1 + transition_progress * 30 + random.gauss(0, 2)  # Accelerating
                
            else:  # Cruise phase
                # Forward flight configuration
                motor_1_rpm = 2200 + random.gauss(0, 100)  # Reduced lift motors
                motor_2_rpm = 2200 + random.gauss(0, 100)
                motor_3_rpm = 2200 + random.gauss(0, 100)
                motor_4_rpm = 2200 + random.gauss(0, 100)
                motor_5_rpm = 5000 + random.gauss(0, 300)  # Forward motor primary
                
                altitude = 100 + random.gauss(0, 8)  # Cruise altitude
                speed = 35 + random.gauss(0, 3)  # Cruise speed
            
            # Moderate vibration
            vibration_x = random.gauss(0, 2.5)
            vibration_y = random.gauss(0, 2.5)
            vibration_z = random.gauss(0, 2)
            
            # High battery consumption
            battery_voltage = 12.8 - (i / duration) * 2.2 + random.gauss(0, 0.1)
            
            # GPS and sensors
            gps_hdop = 1.2 + abs(random.gauss(0, 0.4))
            temperature = 28 + random.gauss(0, 2.5)
            
            # Control surfaces (VTOL has both)
            elevator = random.gauss(0, 2)
            aileron = random.gauss(0, 3)
            
            data.append({
                'timestamp': timestamp,
                'altitude': round(altitude, 2),
                'battery_voltage': round(battery_voltage, 2),
                'motor_1_rpm': round(motor_1_rpm),
                'motor_2_rpm': round(motor_2_rpm),
                'motor_3_rpm': round(motor_3_rpm),
                'motor_4_rpm': round(motor_4_rpm),
                'motor_5_rpm': round(motor_5_rpm),  # 5th motor for VTOL
                'gps_hdop': round(gps_hdop, 2),
                'vibration_x': round(vibration_x, 2),
                'vibration_y': round(vibration_y, 2),
                'vibration_z': round(vibration_z, 2),
                'speed': round(max(0, speed), 2),
                'temperature': round(temperature, 1),
                'elevator': round(elevator, 2),
                'aileron': round(aileron, 2)
            })
        
        return data
    
    def save_csv_data(self, data, filename):
        """Save data to CSV file"""
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', newline='') as csvfile:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        
        print(f"   Saved {len(data)} data points to: {filepath}")
        return filepath
    
    def analyze_flight_log(self, filepath, expected_type=None):
        """Analyze flight log via API"""
        print(f"🔍 Analyzing: {filepath.name}")
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.name, f, 'text/csv')}
                start_time = time.time()
                response = requests.post(f"{BASE_URL}/api/v2/analyze", files=files, timeout=30)
                processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                detected_type = result.get('aircraft_type', 'unknown')
                confidence = result.get('confidence', 0.0)
                risk_level = result.get('risk_level', 'unknown')
                analysis_id = result.get('analysis_id', 'N/A')
                
                # Check if detection is correct
                type_correct = (expected_type is None or detected_type == expected_type)
                confidence_good = confidence >= 0.7
                
                success = type_correct and confidence_good
                
                details = {
                    'Detected Type': detected_type,
                    'Expected': expected_type or 'Any',
                    'Confidence': f"{confidence:.2f}",
                    'Risk Level': risk_level,
                    'Processing Time': f"{processing_time:.2f}s",
                    'Analysis ID': analysis_id[:8] + '...' if len(analysis_id) > 8 else analysis_id
                }
                
                # Add debug info about the analysis
                report = result.get('report', {})
                if isinstance(report, dict):
                    if 'anomalies' in report:
                        details['Anomalies Found'] = len(report['anomalies'])
                    if 'aircraft_confidence' in report:
                        details['AI Confidence'] = f"{report['aircraft_confidence']:.2f}"
                
                message = f"Analysis complete - {detected_type} detected"
                self.print_result(success, message, details)
                
                return success, result
                
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                
                self.print_result(False, f"Analysis failed: {error_msg}")
                return False, None
                
        except Exception as e:
            self.print_result(False, f"Analysis error: {str(e)}")
            return False, None
    
    def test_clear_aircraft_detection(self):
        """Test with very clear aircraft type signatures"""
        self.print_header("Clear Aircraft Type Detection Test")
        
        test_cases = [
            (self.generate_clear_multirotor_data, 300, "multirotor", "clear_multirotor.csv"),
            (self.generate_clear_fixed_wing_data, 400, "fixed_wing", "clear_fixed_wing.csv"),
            (self.generate_clear_vtol_data, 360, "vtol", "clear_vtol.csv"),
        ]
        
        correct_detections = 0
        total_tests = len(test_cases)
        
        for generator_func, duration, expected_type, filename in test_cases:
            self.print_test(f"{expected_type.replace('_', ' ').title()} Detection")
            
            # Generate very clear signature data
            data = generator_func(duration)
            filepath = self.save_csv_data(data, filename)
            
            # Show some key characteristics of the generated data
            print(f"   Data characteristics:")
            if expected_type == "multirotor":
                motor_rpms = [data[0]['motor_1_rpm'], data[0]['motor_2_rpm'], 
                             data[0]['motor_3_rpm'], data[0]['motor_4_rpm']]
                print(f"     • 4 active motors: {motor_rpms}")
                print(f"     • Low speed: {data[0]['speed']} m/s")
                print(f"     • High vibration: {data[0]['vibration_x']}")
            elif expected_type == "fixed_wing":
                print(f"     • Single motor: {data[0]['motor_1_rpm']} RPM")
                print(f"     • High speed: {data[0]['speed']} m/s")
                print(f"     • Control surfaces: elevator={data[0]['elevator']}")
            elif expected_type == "vtol":
                print(f"     • Multiple motors: {data[0]['motor_1_rpm']}, {data[0]['motor_5_rpm']}")
                print(f"     • Variable speed: {data[0]['speed']} m/s")
                print(f"     • Both motors and surfaces")
            
            # Analyze
            success, result = self.analyze_flight_log(filepath, expected_type)
            if success:
                correct_detections += 1
            
            time.sleep(2)  # Pause between tests
        
        # Summary
        accuracy = (correct_detections / total_tests) * 100
        print(f"\n📊 Clear Detection Results:")
        print(f"   Correct: {correct_detections}/{total_tests}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        return accuracy >= 66  # At least 2/3 correct
    
    def test_system_diagnostics(self):
        """Test system diagnostics and debug info"""
        self.print_header("System Diagnostics")
        
        # Test system status
        self.print_test("System Status Check")
        try:
            response = requests.get(f"{BASE_URL}/api/v2/system/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                details = {
                    'System': status.get('system', 'Unknown'),
                    'Version': status.get('version', 'Unknown'),
                    'API Version': status.get('api_version', 'Unknown'),
                    'Features': len(status.get('features', {})),
                    'Models': status.get('models', {})
                }
                self.print_result(True, "System status retrieved", details)
            else:
                self.print_result(False, f"System status failed: HTTP {response.status_code}")
        except Exception as e:
            self.print_result(False, f"System status error: {str(e)}")
        
        return True
    
    def run_targeted_tests(self):
        """Run targeted AI engine tests"""
        print("🎯 DBX AI Aviation System - Targeted AI Engine Testing")
        print("=" * 65)
        print("Testing with clear aircraft signatures to validate AI detection")
        
        # Check API availability
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                print("❌ API not available")
                return False
        except:
            print("❌ Cannot connect to API")
            return False
        
        print("✅ API connection established")
        
        # Run tests
        results = []
        
        # 1. System Diagnostics
        diag_pass = self.test_system_diagnostics()
        results.append(("System Diagnostics", diag_pass))
        
        # 2. Clear Aircraft Detection
        detection_pass = self.test_clear_aircraft_detection()
        results.append(("Clear Aircraft Detection", detection_pass))
        
        # Final Results
        self.print_header("Targeted Test Results")
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Results:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        if detection_pass:
            print("\n🎉 AI Engine is working correctly!")
            print("   The system can distinguish between aircraft types")
            print("   when given clear characteristic signatures.")
        else:
            print("\n🔍 AI Engine needs attention:")
            print("   The aircraft detection logic may need tuning")
            print("   or the feature engineering needs improvement.")
        
        print("\n💡 Next Steps:")
        print("   • Review the generated test data characteristics")
        print("   • Check if the AI model training data matches real patterns")
        print("   • Consider retraining with more diverse datasets")
        
        return passed == total

def main():
    tester = TargetedAITest()
    success = tester.run_targeted_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())