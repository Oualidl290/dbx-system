#!/usr/bin/env python3
"""
DBX AI Aviation System - Core AI Engine Real-World Testing
Comprehensive testing of multi-aircraft detection and anomaly analysis
"""

import requests
import json
import pandas as pd
import numpy as np
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
import io

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class AIEngineTest:
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
        
        self.test_results.append({
            'test': message,
            'success': success,
            'details': details or {}
        })
    
    def generate_multirotor_flight_log(self, scenario="normal"):
        """Generate realistic multirotor flight log data"""
        print(f"📊 Generating multirotor flight log ({scenario} scenario)...")
        
        # Flight parameters based on scenario
        if scenario == "normal":
            duration = 300  # 5 minutes
            altitude_profile = "stable_hover"
            motor_health = "good"
            battery_profile = "normal_discharge"
        elif scenario == "aggressive":
            duration = 180  # 3 minutes
            altitude_profile = "rapid_maneuvers"
            motor_health = "good"
            battery_profile = "high_discharge"
        elif scenario == "emergency":
            duration = 120  # 2 minutes
            altitude_profile = "emergency_landing"
            motor_health = "motor_failure"
            battery_profile = "critical_low"
        else:
            duration = 240
            altitude_profile = "stable_hover"
            motor_health = "good"
            battery_profile = "normal_discharge"
        
        # Generate time series
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=duration//60),
            periods=duration,
            freq='1S'
        )
        
        data = []
        np.random.seed(42)  # For reproducible results
        
        for i, ts in enumerate(timestamps):
            # Base multirotor characteristics
            base_rpm = 3000
            
            # Altitude profile
            if altitude_profile == "stable_hover":
                altitude = 50 + np.random.normal(0, 2)  # Stable hover at 50m
            elif altitude_profile == "rapid_maneuvers":
                altitude = 30 + 20 * np.sin(i * 0.1) + np.random.normal(0, 3)
            elif altitude_profile == "emergency_landing":
                if i < duration * 0.7:
                    altitude = 80 + np.random.normal(0, 2)  # Normal flight
                else:
                    # Emergency descent
                    descent_rate = (i - duration * 0.7) * 2
                    altitude = max(0, 80 - descent_rate + np.random.normal(0, 1))
            
            # Motor RPM based on health
            if motor_health == "good":
                motor_1_rpm = base_rpm + np.random.normal(0, 50)
                motor_2_rpm = base_rpm + np.random.normal(0, 50)
                motor_3_rpm = base_rpm + np.random.normal(0, 50)
                motor_4_rpm = base_rpm + np.random.normal(0, 50)
            elif motor_health == "motor_failure":
                motor_1_rpm = base_rpm + np.random.normal(0, 50)
                motor_2_rpm = base_rpm + np.random.normal(0, 50)
                motor_3_rpm = base_rpm + np.random.normal(0, 50)
                # Motor 4 fails halfway through
                if i > duration * 0.5:
                    motor_4_rpm = max(0, base_rpm * 0.3 + np.random.normal(0, 200))
                else:
                    motor_4_rpm = base_rpm + np.random.normal(0, 50)
            
            # Battery voltage based on profile
            if battery_profile == "normal_discharge":
                battery_voltage = 12.6 - (i / duration) * 1.5 + np.random.normal(0, 0.1)
            elif battery_profile == "high_discharge":
                battery_voltage = 12.6 - (i / duration) * 2.5 + np.random.normal(0, 0.15)
            elif battery_profile == "critical_low":
                if i < duration * 0.8:
                    battery_voltage = 12.0 - (i / duration) * 1.0 + np.random.normal(0, 0.1)
                else:
                    # Critical voltage drop
                    battery_voltage = 10.5 + np.random.normal(0, 0.2)
            
            # Speed (multirotors typically slower)
            if altitude_profile == "rapid_maneuvers":
                speed = 5 + 10 * abs(np.sin(i * 0.05)) + np.random.normal(0, 1)
            else:
                speed = 2 + np.random.normal(0, 1)  # Typical hover/slow movement
            
            # Vibration (higher for multirotors)
            vibration_x = np.random.normal(0, 3)
            vibration_y = np.random.normal(0, 3)
            vibration_z = np.random.normal(0, 2)
            
            # GPS accuracy
            gps_hdop = 1.0 + np.random.gamma(1, 0.5)
            
            # Temperature
            temperature = 25 + np.random.normal(0, 2)
            
            data.append({
                'timestamp': ts.isoformat(),
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
        
        df = pd.DataFrame(data)
        filename = f"multirotor_{scenario}_flight.csv"
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        print(f"   Generated {len(data)} data points over {duration} seconds")
        print(f"   Saved to: {filepath}")
        
        return filepath, df
    
    def generate_fixed_wing_flight_log(self, scenario="normal"):
        """Generate realistic fixed-wing aircraft flight log"""
        print(f"📊 Generating fixed-wing flight log ({scenario} scenario)...")
        
        if scenario == "normal":
            duration = 600  # 10 minutes
            flight_profile = "cruise"
            engine_health = "good"
        elif scenario == "aerobatic":
            duration = 300  # 5 minutes
            flight_profile = "aerobatic"
            engine_health = "good"
        elif scenario == "engine_issue":
            duration = 240  # 4 minutes
            flight_profile = "emergency"
            engine_health = "degraded"
        
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=duration//60),
            periods=duration,
            freq='1S'
        )
        
        data = []
        np.random.seed(43)  # Different seed for variety
        
        for i, ts in enumerate(timestamps):
            # Fixed-wing characteristics
            if flight_profile == "cruise":
                altitude = 200 + np.random.normal(0, 5)  # Stable cruise altitude
                speed = 25 + np.random.normal(0, 2)  # Typical cruise speed
            elif flight_profile == "aerobatic":
                altitude = 150 + 50 * np.sin(i * 0.05) + np.random.normal(0, 10)
                speed = 20 + 15 * abs(np.cos(i * 0.03)) + np.random.normal(0, 3)
            elif flight_profile == "emergency":
                if i < duration * 0.6:
                    altitude = 180 + np.random.normal(0, 5)
                    speed = 22 + np.random.normal(0, 2)
                else:
                    # Emergency descent
                    descent_rate = (i - duration * 0.6) * 1.5
                    altitude = max(50, 180 - descent_rate)
                    speed = 15 + np.random.normal(0, 3)  # Reduced speed
            
            # Single motor (fixed-wing)
            if engine_health == "good":
                motor_1_rpm = 2500 + np.random.normal(0, 100)
            elif engine_health == "degraded":
                if i > duration * 0.4:
                    motor_1_rpm = 2000 + np.random.normal(0, 200)  # Reduced power
                else:
                    motor_1_rpm = 2500 + np.random.normal(0, 100)
            
            # Other motors should be 0 or very low for fixed-wing
            motor_2_rpm = np.random.normal(0, 10)
            motor_3_rpm = np.random.normal(0, 10)
            motor_4_rpm = np.random.normal(0, 10)
            
            # Battery (less critical for fuel-powered aircraft)
            battery_voltage = 12.0 + np.random.normal(0, 0.2)
            
            # Lower vibration for fixed-wing
            vibration_x = np.random.normal(0, 1)
            vibration_y = np.random.normal(0, 1)
            vibration_z = np.random.normal(0, 0.5)
            
            # GPS
            gps_hdop = 0.8 + np.random.gamma(1, 0.3)
            
            # Temperature
            temperature = 20 + np.random.normal(0, 3)
            
            data.append({
                'timestamp': ts.isoformat(),
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
        
        df = pd.DataFrame(data)
        filename = f"fixed_wing_{scenario}_flight.csv"
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        print(f"   Generated {len(data)} data points over {duration} seconds")
        print(f"   Saved to: {filepath}")
        
        return filepath, df
    
    def generate_vtol_flight_log(self, scenario="normal"):
        """Generate realistic VTOL aircraft flight log"""
        print(f"📊 Generating VTOL flight log ({scenario} scenario)...")
        
        if scenario == "normal":
            duration = 480  # 8 minutes
            flight_profile = "vtol_transition"
        elif scenario == "hover_only":
            duration = 300  # 5 minutes
            flight_profile = "hover_mode"
        elif scenario == "transition_failure":
            duration = 200  # 3+ minutes
            flight_profile = "failed_transition"
        
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(minutes=duration//60),
            periods=duration,
            freq='1S'
        )
        
        data = []
        np.random.seed(44)
        
        for i, ts in enumerate(timestamps):
            # VTOL flight phases
            phase_duration = duration // 3
            
            if flight_profile == "vtol_transition":
                if i < phase_duration:  # Hover phase
                    altitude = 30 + np.random.normal(0, 2)
                    speed = 1 + np.random.normal(0, 0.5)
                    # Multiple motors active
                    motor_1_rpm = 3200 + np.random.normal(0, 100)
                    motor_2_rpm = 3200 + np.random.normal(0, 100)
                    motor_3_rpm = 3200 + np.random.normal(0, 100)
                    motor_4_rpm = 3200 + np.random.normal(0, 100)
                elif i < 2 * phase_duration:  # Transition phase
                    altitude = 30 + (i - phase_duration) * 0.5 + np.random.normal(0, 5)
                    speed = 1 + (i - phase_duration) * 0.1 + np.random.normal(0, 2)
                    # Motors transitioning
                    motor_1_rpm = 2800 + np.random.normal(0, 150)
                    motor_2_rpm = 2800 + np.random.normal(0, 150)
                    motor_3_rpm = 2800 + np.random.normal(0, 150)
                    motor_4_rpm = 2800 + np.random.normal(0, 150)
                else:  # Forward flight phase
                    altitude = 100 + np.random.normal(0, 8)
                    speed = 35 + np.random.normal(0, 3)
                    # Reduced motor activity in forward flight
                    motor_1_rpm = 2200 + np.random.normal(0, 100)
                    motor_2_rpm = 2200 + np.random.normal(0, 100)
                    motor_3_rpm = 1800 + np.random.normal(0, 100)
                    motor_4_rpm = 1800 + np.random.normal(0, 100)
            
            elif flight_profile == "hover_mode":
                altitude = 40 + np.random.normal(0, 3)
                speed = 2 + np.random.normal(0, 1)
                motor_1_rpm = 3100 + np.random.normal(0, 80)
                motor_2_rpm = 3100 + np.random.normal(0, 80)
                motor_3_rpm = 3100 + np.random.normal(0, 80)
                motor_4_rpm = 3100 + np.random.normal(0, 80)
            
            elif flight_profile == "failed_transition":
                if i < duration * 0.6:  # Normal hover
                    altitude = 35 + np.random.normal(0, 2)
                    speed = 1 + np.random.normal(0, 0.5)
                    motor_1_rpm = 3200 + np.random.normal(0, 100)
                    motor_2_rpm = 3200 + np.random.normal(0, 100)
                    motor_3_rpm = 3200 + np.random.normal(0, 100)
                    motor_4_rpm = 3200 + np.random.normal(0, 100)
                else:  # Failed transition - emergency hover
                    altitude = max(10, 35 - (i - duration * 0.6) * 0.3)
                    speed = 0.5 + np.random.normal(0, 1)
                    motor_1_rpm = 3500 + np.random.normal(0, 200)  # Overworking
                    motor_2_rpm = 3500 + np.random.normal(0, 200)
                    motor_3_rpm = 3500 + np.random.normal(0, 200)
                    motor_4_rpm = 3500 + np.random.normal(0, 200)
            
            # Battery (high consumption for VTOL)
            battery_voltage = 12.8 - (i / duration) * 2.0 + np.random.normal(0, 0.1)
            
            # Moderate vibration
            vibration_x = np.random.normal(0, 2)
            vibration_y = np.random.normal(0, 2)
            vibration_z = np.random.normal(0, 1.5)
            
            # GPS
            gps_hdop = 1.2 + np.random.gamma(1, 0.4)
            
            # Temperature
            temperature = 28 + np.random.normal(0, 2.5)
            
            data.append({
                'timestamp': ts.isoformat(),
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
        
        df = pd.DataFrame(data)
        filename = f"vtol_{scenario}_flight.csv"
        filepath = self.data_dir / filename
        df.to_csv(filepath, index=False)
        
        print(f"   Generated {len(data)} data points over {duration} seconds")
        print(f"   Saved to: {filepath}")
        
        return filepath, df
    
    def analyze_flight_log(self, filepath, expected_aircraft_type=None, expected_risk_level=None):
        """Analyze a flight log using the API"""
        print(f"🔍 Analyzing flight log: {filepath.name}")
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filepath.name, f, 'text/csv')}
                response = requests.post(
                    f"{BASE_URL}/api/v2/analyze",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract key results
                detected_type = result.get('aircraft_type', 'unknown')
                confidence = result.get('confidence', 0.0)
                risk_level = result.get('risk_level', 'unknown')
                anomalies = result.get('report', {}).get('anomalies', [])
                
                # Determine success based on expectations
                type_correct = (expected_aircraft_type is None or 
                              detected_type == expected_aircraft_type)
                confidence_good = confidence >= 0.7
                
                success = type_correct and confidence_good
                
                details = {
                    'Detected Type': detected_type,
                    'Expected Type': expected_aircraft_type or 'Any',
                    'Confidence': f"{confidence:.2f}",
                    'Risk Level': risk_level,
                    'Anomalies Found': len(anomalies),
                    'Analysis ID': result.get('analysis_id', 'N/A')
                }
                
                if anomalies:
                    details['Top Anomaly'] = anomalies[0].get('description', 'Unknown') if anomalies else 'None'
                
                message = f"Flight analysis - {detected_type} detected"
                self.print_result(success, message, details)
                
                return success, result
                
            else:
                error_msg = f"API error: HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                    error_msg += f" - {error_detail}"
                except:
                    pass
                
                self.print_result(False, f"Analysis failed: {error_msg}")
                return False, None
                
        except Exception as e:
            self.print_result(False, f"Analysis failed: {str(e)}")
            return False, None
    
    def test_aircraft_type_detection(self):
        """Test multi-aircraft type detection accuracy"""
        self.print_header("Aircraft Type Detection Tests")
        
        test_cases = [
            # Multirotor tests
            ("multirotor", "normal", "multirotor"),
            ("multirotor", "aggressive", "multirotor"),
            ("multirotor", "emergency", "multirotor"),
            
            # Fixed-wing tests
            ("fixed_wing", "normal", "fixed_wing"),
            ("fixed_wing", "aerobatic", "fixed_wing"),
            ("fixed_wing", "engine_issue", "fixed_wing"),
            
            # VTOL tests
            ("vtol", "normal", "vtol"),
            ("vtol", "hover_only", "vtol"),
            ("vtol", "transition_failure", "vtol"),
        ]
        
        correct_detections = 0
        total_tests = len(test_cases)
        
        for aircraft_type, scenario, expected_type in test_cases:
            self.print_test(f"{aircraft_type.title()} - {scenario.replace('_', ' ').title()}")
            
            # Generate flight log
            if aircraft_type == "multirotor":
                filepath, df = self.generate_multirotor_flight_log(scenario)
            elif aircraft_type == "fixed_wing":
                filepath, df = self.generate_fixed_wing_flight_log(scenario)
            elif aircraft_type == "vtol":
                filepath, df = self.generate_vtol_flight_log(scenario)
            
            # Analyze
            success, result = self.analyze_flight_log(filepath, expected_type)
            if success:
                correct_detections += 1
            
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        accuracy = (correct_detections / total_tests) * 100
        print(f"\n📊 Aircraft Detection Summary:")
        print(f"   Correct Detections: {correct_detections}/{total_tests}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        return accuracy >= 80  # 80% accuracy threshold
    
    def test_anomaly_detection(self):
        """Test anomaly detection capabilities"""
        self.print_header("Anomaly Detection Tests")
        
        # Test normal vs anomalous flights
        test_cases = [
            ("multirotor", "normal", "low"),
            ("multirotor", "emergency", "high"),
            ("fixed_wing", "normal", "low"),
            ("fixed_wing", "engine_issue", "high"),
            ("vtol", "normal", "low"),
            ("vtol", "transition_failure", "high"),
        ]
        
        anomaly_tests_passed = 0
        total_anomaly_tests = len(test_cases)
        
        for aircraft_type, scenario, expected_risk in test_cases:
            self.print_test(f"{aircraft_type.title()} - {scenario.replace('_', ' ').title()} (expect {expected_risk} risk)")
            
            # Generate flight log
            if aircraft_type == "multirotor":
                filepath, df = self.generate_multirotor_flight_log(scenario)
            elif aircraft_type == "fixed_wing":
                filepath, df = self.generate_fixed_wing_flight_log(scenario)
            elif aircraft_type == "vtol":
                filepath, df = self.generate_vtol_flight_log(scenario)
            
            # Analyze
            success, result = self.analyze_flight_log(filepath)
            
            if result:
                detected_risk = result.get('risk_level', 'unknown').lower()
                risk_appropriate = (
                    (expected_risk == "low" and detected_risk in ["low", "normal"]) or
                    (expected_risk == "high" and detected_risk in ["high", "critical", "warning", "elevated"])
                )
                
                if risk_appropriate:
                    anomaly_tests_passed += 1
                    print(f"   ✅ Risk level appropriate: {detected_risk}")
                else:
                    print(f"   ❌ Risk level mismatch: expected {expected_risk}, got {detected_risk}")
            
            time.sleep(1)
        
        # Summary
        anomaly_accuracy = (anomaly_tests_passed / total_anomaly_tests) * 100
        print(f"\n📊 Anomaly Detection Summary:")
        print(f"   Appropriate Risk Assessments: {anomaly_tests_passed}/{total_anomaly_tests}")
        print(f"   Accuracy: {anomaly_accuracy:.1f}%")
        
        return anomaly_accuracy >= 70  # 70% accuracy threshold for anomaly detection
    
    def test_performance_metrics(self):
        """Test system performance with various load scenarios"""
        self.print_header("Performance & Load Testing")
        
        # Generate a larger dataset
        self.print_test("Large Dataset Processing")
        filepath, df = self.generate_multirotor_flight_log("normal")
        
        # Measure processing time
        start_time = time.time()
        success, result = self.analyze_flight_log(filepath)
        processing_time = time.time() - start_time
        
        if success and result:
            processing_time_ms = result.get('report', {}).get('processing_time_ms', processing_time * 1000)
            
            details = {
                'Processing Time': f"{processing_time:.2f}s",
                'API Response Time': f"{processing_time_ms}ms" if processing_time_ms else "N/A",
                'Data Points': len(df),
                'Throughput': f"{len(df)/processing_time:.1f} points/sec"
            }
            
            # Performance thresholds
            performance_good = processing_time < 10.0  # Under 10 seconds
            
            self.print_result(performance_good, "Performance test", details)
            return performance_good
        else:
            self.print_result(False, "Performance test failed")
            return False
    
    def run_comprehensive_test(self):
        """Run all AI engine tests"""
        print("🚀 DBX AI Aviation System - Comprehensive AI Engine Testing")
        print("=" * 70)
        print("Testing real-world scenarios with multi-aircraft detection and anomaly analysis")
        
        # Check if API is available
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                print("❌ API not available. Please ensure the system is running.")
                return False
        except:
            print("❌ Cannot connect to API. Please ensure the system is running.")
            return False
        
        print("✅ API connection established")
        
        # Run test suites
        test_results = []
        
        # 1. Aircraft Type Detection
        detection_success = self.test_aircraft_type_detection()
        test_results.append(("Aircraft Type Detection", detection_success))
        
        # 2. Anomaly Detection
        anomaly_success = self.test_anomaly_detection()
        test_results.append(("Anomaly Detection", anomaly_success))
        
        # 3. Performance Testing
        performance_success = self.test_performance_metrics()
        test_results.append(("Performance Testing", performance_success))
        
        # Final Summary
        self.print_header("Final Test Results")
        
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        for test_name, success in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_name}")
        
        print(f"\n📊 Overall Results:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 All AI engine tests passed! The system is performing excellently.")
            print("\n🚀 Ready for production use with:")
            print("   • Multi-aircraft type detection")
            print("   • Advanced anomaly analysis")
            print("   • Real-time performance")
            print("   • Comprehensive risk assessment")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Review the results above.")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = AIEngineTest()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())