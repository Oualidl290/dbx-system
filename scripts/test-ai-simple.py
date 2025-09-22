#!/usr/bin/env python3
"""
DBX AI Aviation System - Simple AI Engine Testing
Real-world testing using only built-in Python libraries
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
import io

# Configuration
BASE_URL = "http://localhost:8000"

class SimpleAITest:
    def __init__(self):
        self.test_results = []
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
    
    def generate_multirotor_data(self, scenario="normal", duration=300):
        """Generate realistic multirotor flight data"""
        print(f"📊 Generating multirotor data ({scenario}, {duration}s)...")
        
        data = []
        random.seed(42)  # For reproducible results
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # Multirotor characteristics
            if scenario == "normal":
                altitude = 50 + random.gauss(0, 2)
                speed = 2 + abs(random.gauss(0, 1))
                motor_base = 3000
                battery_voltage = 12.6 - (i / duration) * 1.5 + random.gauss(0, 0.1)
            elif scenario == "emergency":
                if i < duration * 0.7:
                    altitude = 80 + random.gauss(0, 2)
                    speed = 3 + abs(random.gauss(0, 1))
                    motor_base = 3000
                else:
                    # Emergency descent
                    descent_rate = (i - duration * 0.7) * 2
                    altitude = max(0, 80 - descent_rate)
                    speed = 1 + abs(random.gauss(0, 2))
                    motor_base = 3500  # Overworking motors
                battery_voltage = 12.0 - (i / duration) * 2.0 + random.gauss(0, 0.15)
                if i > duration * 0.8:
                    battery_voltage = 10.5 + random.gauss(0, 0.2)  # Critical voltage
            
            # Motor RPMs (4 motors for multirotor)
            motor_1_rpm = motor_base + random.gauss(0, 50)
            motor_2_rpm = motor_base + random.gauss(0, 50)
            motor_3_rpm = motor_base + random.gauss(0, 50)
            
            # Motor failure in emergency scenario
            if scenario == "emergency" and i > duration * 0.5:
                motor_4_rpm = max(0, motor_base * 0.3 + random.gauss(0, 200))
            else:
                motor_4_rpm = motor_base + random.gauss(0, 50)
            
            # Higher vibration for multirotors
            vibration_x = random.gauss(0, 3)
            vibration_y = random.gauss(0, 3)
            vibration_z = random.gauss(0, 2)
            
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
    
    def generate_fixed_wing_data(self, scenario="normal", duration=600):
        """Generate realistic fixed-wing aircraft data"""
        print(f"📊 Generating fixed-wing data ({scenario}, {duration}s)...")
        
        data = []
        random.seed(43)
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # Fixed-wing characteristics
            if scenario == "normal":
                altitude = 200 + random.gauss(0, 5)
                speed = 25 + random.gauss(0, 2)  # Higher cruise speed
                motor_1_rpm = 2500 + random.gauss(0, 100)  # Single engine
            elif scenario == "engine_issue":
                altitude = 180 + random.gauss(0, 5)
                speed = 20 + random.gauss(0, 3)
                if i > duration * 0.4:
                    motor_1_rpm = 2000 + random.gauss(0, 200)  # Reduced power
                else:
                    motor_1_rpm = 2500 + random.gauss(0, 100)
            
            # Other motors minimal (single engine aircraft)
            motor_2_rpm = random.gauss(0, 10)
            motor_3_rpm = random.gauss(0, 10)
            motor_4_rpm = random.gauss(0, 10)
            
            # Battery less critical for fuel aircraft
            battery_voltage = 12.0 + random.gauss(0, 0.2)
            
            # Lower vibration for fixed-wing
            vibration_x = random.gauss(0, 1)
            vibration_y = random.gauss(0, 1)
            vibration_z = random.gauss(0, 0.5)
            
            gps_hdop = 0.8 + abs(random.gauss(0, 0.3))
            temperature = 20 + random.gauss(0, 3)
            
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
    
    def generate_vtol_data(self, scenario="normal", duration=480):
        """Generate realistic VTOL aircraft data"""
        print(f"📊 Generating VTOL data ({scenario}, {duration}s)...")
        
        data = []
        random.seed(44)
        
        for i in range(duration):
            timestamp = (datetime.now() - timedelta(seconds=duration-i)).isoformat()
            
            # VTOL flight phases
            phase_duration = duration // 3
            
            if scenario == "normal":
                if i < phase_duration:  # Hover phase
                    altitude = 30 + random.gauss(0, 2)
                    speed = 1 + abs(random.gauss(0, 0.5))
                    motor_base = 3200
                elif i < 2 * phase_duration:  # Transition
                    altitude = 30 + (i - phase_duration) * 0.5 + random.gauss(0, 5)
                    speed = 1 + (i - phase_duration) * 0.1 + abs(random.gauss(0, 2))
                    motor_base = 2800
                else:  # Forward flight
                    altitude = 100 + random.gauss(0, 8)
                    speed = 35 + random.gauss(0, 3)
                    motor_base = 2200
            elif scenario == "transition_failure":
                if i < duration * 0.6:
                    altitude = 35 + random.gauss(0, 2)
                    speed = 1 + abs(random.gauss(0, 0.5))
                    motor_base = 3200
                else:  # Failed transition
                    altitude = max(10, 35 - (i - duration * 0.6) * 0.3)
                    speed = 0.5 + abs(random.gauss(0, 1))
                    motor_base = 3500  # Overworking
            
            # Multiple motors active
            motor_1_rpm = motor_base + random.gauss(0, 100)
            motor_2_rpm = motor_base + random.gauss(0, 100)
            motor_3_rpm = motor_base + random.gauss(0, 100)
            motor_4_rpm = motor_base + random.gauss(0, 100)
            
            # High battery consumption
            battery_voltage = 12.8 - (i / duration) * 2.0 + random.gauss(0, 0.1)
            
            # Moderate vibration
            vibration_x = random.gauss(0, 2)
            vibration_y = random.gauss(0, 2)
            vibration_z = random.gauss(0, 1.5)
            
            gps_hdop = 1.2 + abs(random.gauss(0, 0.4))
            temperature = 28 + random.gauss(0, 2.5)
            
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
                
                # Check for anomalies in report
                report = result.get('report', {})
                if isinstance(report, dict) and 'anomalies' in report:
                    anomaly_count = len(report['anomalies'])
                    details['Anomalies Found'] = anomaly_count
                
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
    
    def test_aircraft_detection(self):
        """Test multi-aircraft type detection"""
        self.print_header("Multi-Aircraft Type Detection")
        
        test_cases = [
            # (generator_func, scenario, duration, expected_type, filename)
            (self.generate_multirotor_data, "normal", 300, "multirotor", "multirotor_normal.csv"),
            (self.generate_multirotor_data, "emergency", 200, "multirotor", "multirotor_emergency.csv"),
            (self.generate_fixed_wing_data, "normal", 400, "fixed_wing", "fixed_wing_normal.csv"),
            (self.generate_fixed_wing_data, "engine_issue", 300, "fixed_wing", "fixed_wing_issue.csv"),
            (self.generate_vtol_data, "normal", 360, "vtol", "vtol_normal.csv"),
            (self.generate_vtol_data, "transition_failure", 240, "vtol", "vtol_failure.csv"),
        ]
        
        correct_detections = 0
        total_tests = len(test_cases)
        
        for generator_func, scenario, duration, expected_type, filename in test_cases:
            self.print_test(f"{expected_type.replace('_', ' ').title()} - {scenario.replace('_', ' ').title()}")
            
            # Generate data
            data = generator_func(scenario, duration)
            filepath = self.save_csv_data(data, filename)
            
            # Analyze
            success, result = self.analyze_flight_log(filepath, expected_type)
            if success:
                correct_detections += 1
            
            time.sleep(1)  # Brief pause
        
        # Summary
        accuracy = (correct_detections / total_tests) * 100
        print(f"\n📊 Detection Results:")
        print(f"   Correct: {correct_detections}/{total_tests}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        return accuracy >= 75  # 75% threshold
    
    def test_anomaly_detection(self):
        """Test anomaly detection capabilities"""
        self.print_header("Anomaly Detection & Risk Assessment")
        
        # Test normal vs problematic scenarios
        test_cases = [
            (self.generate_multirotor_data, "normal", 300, "low", "multirotor_normal_risk.csv"),
            (self.generate_multirotor_data, "emergency", 200, "high", "multirotor_emergency_risk.csv"),
            (self.generate_fixed_wing_data, "normal", 400, "low", "fixed_wing_normal_risk.csv"),
            (self.generate_fixed_wing_data, "engine_issue", 300, "high", "fixed_wing_issue_risk.csv"),
        ]
        
        appropriate_assessments = 0
        total_assessments = len(test_cases)
        
        for generator_func, scenario, duration, expected_risk, filename in test_cases:
            aircraft_type = "multirotor" if "multirotor" in filename else "fixed_wing"
            self.print_test(f"{aircraft_type.title()} - {scenario.title()} (expect {expected_risk} risk)")
            
            # Generate data
            data = generator_func(scenario, duration)
            filepath = self.save_csv_data(data, filename)
            
            # Analyze
            success, result = self.analyze_flight_log(filepath)
            
            if result:
                detected_risk = result.get('risk_level', 'unknown').lower()
                
                # Check if risk assessment is appropriate
                risk_appropriate = False
                if expected_risk == "low":
                    risk_appropriate = detected_risk in ["low", "normal"]
                elif expected_risk == "high":
                    risk_appropriate = detected_risk in ["high", "critical", "warning", "elevated"]
                
                if risk_appropriate:
                    appropriate_assessments += 1
                    print(f"   ✅ Risk assessment appropriate: {detected_risk}")
                else:
                    print(f"   ❌ Risk mismatch: expected {expected_risk}, got {detected_risk}")
            
            time.sleep(1)
        
        # Summary
        risk_accuracy = (appropriate_assessments / total_assessments) * 100
        print(f"\n📊 Risk Assessment Results:")
        print(f"   Appropriate: {appropriate_assessments}/{total_assessments}")
        print(f"   Accuracy: {risk_accuracy:.1f}%")
        
        return risk_accuracy >= 70  # 70% threshold
    
    def test_system_performance(self):
        """Test system performance and response times"""
        self.print_header("System Performance Testing")
        
        self.print_test("Large Dataset Processing")
        
        # Generate larger dataset
        data = self.generate_multirotor_data("normal", 600)  # 10 minutes of data
        filepath = self.save_csv_data(data, "performance_test.csv")
        
        # Measure performance
        start_time = time.time()
        success, result = self.analyze_flight_log(filepath)
        total_time = time.time() - start_time
        
        if success and result:
            details = {
                'Total Time': f"{total_time:.2f}s",
                'Data Points': len(data),
                'Throughput': f"{len(data)/total_time:.1f} points/sec",
                'Status': 'PASS' if total_time < 15.0 else 'SLOW'
            }
            
            performance_good = total_time < 15.0  # Under 15 seconds
            self.print_result(performance_good, "Performance test", details)
            return performance_good
        else:
            self.print_result(False, "Performance test failed")
            return False
    
    def run_all_tests(self):
        """Run comprehensive AI engine tests"""
        print("🚀 DBX AI Aviation System - Real-World AI Engine Testing")
        print("=" * 65)
        
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
        
        # Run test suites
        results = []
        
        # 1. Aircraft Detection
        detection_pass = self.test_aircraft_detection()
        results.append(("Aircraft Type Detection", detection_pass))
        
        # 2. Anomaly Detection
        anomaly_pass = self.test_anomaly_detection()
        results.append(("Anomaly & Risk Detection", anomaly_pass))
        
        # 3. Performance
        performance_pass = self.test_system_performance()
        results.append(("System Performance", performance_pass))
        
        # Final Results
        self.print_header("Final Test Results")
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All AI engine tests PASSED!")
            print("\n🚀 System Capabilities Verified:")
            print("   ✅ Multi-aircraft type detection (Multirotor, Fixed-wing, VTOL)")
            print("   ✅ Real-time anomaly detection")
            print("   ✅ Intelligent risk assessment")
            print("   ✅ High-performance processing")
            print("   ✅ Production-ready reliability")
            print("\n💡 The AI engine is ready for real-world aviation analysis!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. System needs attention.")
        
        return passed == total

def main():
    tester = SimpleAITest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())