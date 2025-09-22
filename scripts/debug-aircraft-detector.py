#!/usr/bin/env python3
"""
DBX AI Aviation System - Aircraft Detection Logic Debugger
Deep debugging of the aircraft detection algorithm to fix the 33% accuracy issue
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import json
import csv

# Add src to path to import the actual detection logic
current_dir = Path(__file__).parent.parent
src_dir = str(current_dir / "src")
sys.path.insert(0, src_dir)

try:
    from core.ai.aircraft_detector import AircraftTypeDetector, AircraftType
    print("✅ Successfully imported aircraft detector")
except ImportError as e:
    print(f"❌ Failed to import aircraft detector: {e}")
    print("Creating mock detector for debugging...")
    
    class AircraftType:
        FIXED_WING = "fixed_wing"
        MULTIROTOR = "multirotor"
        VTOL = "vtol"
        UNKNOWN = "unknown"
    
    class AircraftTypeDetector:
        def detect_aircraft_type(self, df):
            return AircraftType.MULTIROTOR, 0.85

class AircraftDetectionDebugger:
    def __init__(self):
        self.detector = AircraftTypeDetector()
        self.test_data_dir = Path("data/test")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
    def print_header(self, title):
        print(f"\n{'='*70}")
        print(f"🔍 {title}")
        print(f"{'='*70}")
    
    def create_debug_datasets(self):
        """Create datasets with very clear, distinct characteristics"""
        
        datasets = {}
        
        # 1. EXTREME MULTIROTOR - Should be 100% obvious
        print("📊 Creating extreme multirotor dataset...")
        multirotor_data = []
        for i in range(200):
            multirotor_data.append({
                'timestamp': f"2024-01-01T10:{i//60:02d}:{i%60:02d}",
                'altitude': 50 + np.sin(i * 0.1) * 10,  # Hovering with small variations
                'battery_voltage': 12.6 - (i / 200) * 1.5,
                'motor_1_rpm': 3000 + np.random.normal(0, 50),  # 4 ACTIVE MOTORS
                'motor_2_rpm': 3000 + np.random.normal(0, 50),
                'motor_3_rpm': 3000 + np.random.normal(0, 50),
                'motor_4_rpm': 3000 + np.random.normal(0, 50),
                'gps_hdop': 1.0 + np.random.normal(0, 0.2),
                'vibration_x': np.random.normal(0, 5),  # HIGH VIBRATION
                'vibration_y': np.random.normal(0, 5),
                'vibration_z': np.random.normal(0, 4),
                'speed': 0.5 + abs(np.random.normal(0, 1)),  # VERY LOW SPEED
                'temperature': 25 + np.random.normal(0, 2)
            })
        datasets['extreme_multirotor'] = multirotor_data
        
        # 2. EXTREME FIXED-WING - Should be 100% obvious
        print("📊 Creating extreme fixed-wing dataset...")
        fixed_wing_data = []
        for i in range(200):
            fixed_wing_data.append({
                'timestamp': f"2024-01-01T10:{i//60:02d}:{i%60:02d}",
                'altitude': 200 + np.random.normal(0, 3),  # STABLE CRUISE ALTITUDE
                'battery_voltage': 12.0 + np.random.normal(0, 0.1),
                'motor_1_rpm': 2500 + np.random.normal(0, 100),  # SINGLE MOTOR ONLY
                'motor_2_rpm': np.random.normal(0, 10),  # MINIMAL/OFF
                'motor_3_rpm': np.random.normal(0, 10),  # MINIMAL/OFF
                'motor_4_rpm': np.random.normal(0, 10),  # MINIMAL/OFF
                'gps_hdop': 0.8 + np.random.normal(0, 0.1),
                'vibration_x': np.random.normal(0, 0.8),  # LOW VIBRATION
                'vibration_y': np.random.normal(0, 0.8),
                'vibration_z': np.random.normal(0, 0.5),
                'speed': 30 + np.random.normal(0, 2),  # HIGH CRUISE SPEED
                'temperature': 20 + np.random.normal(0, 2),
                'elevator': np.random.normal(0, 1),  # CONTROL SURFACES
                'aileron': np.random.normal(0, 1.5),
                'rudder': np.random.normal(0, 0.8)
            })
        datasets['extreme_fixed_wing'] = fixed_wing_data
        
        # 3. EXTREME VTOL - Should be 100% obvious
        print("📊 Creating extreme VTOL dataset...")
        vtol_data = []
        for i in range(200):
            # VTOL has distinct phases
            if i < 60:  # Hover phase
                altitude = 30 + np.random.normal(0, 1)
                speed = 1 + abs(np.random.normal(0, 0.3))
                motor_1_rpm = 3200 + np.random.normal(0, 80)
                motor_2_rpm = 3200 + np.random.normal(0, 80)
                motor_3_rpm = 3200 + np.random.normal(0, 80)
                motor_4_rpm = 3200 + np.random.normal(0, 80)
                motor_5_rpm = 800 + np.random.normal(0, 100)  # Forward motor minimal
            elif i < 120:  # Transition phase
                progress = (i - 60) / 60
                altitude = 30 + progress * 70
                speed = 1 + progress * 25
                motor_1_rpm = 3200 - progress * 600 + np.random.normal(0, 100)
                motor_2_rpm = 3200 - progress * 600 + np.random.normal(0, 100)
                motor_3_rpm = 3200 - progress * 600 + np.random.normal(0, 100)
                motor_4_rpm = 3200 - progress * 600 + np.random.normal(0, 100)
                motor_5_rpm = 800 + progress * 4200 + np.random.normal(0, 200)  # Forward motor spooling
            else:  # Forward flight phase
                altitude = 100 + np.random.normal(0, 5)
                speed = 35 + np.random.normal(0, 3)
                motor_1_rpm = 2000 + np.random.normal(0, 100)  # Lift motors reduced
                motor_2_rpm = 2000 + np.random.normal(0, 100)
                motor_3_rpm = 2000 + np.random.normal(0, 100)
                motor_4_rpm = 2000 + np.random.normal(0, 100)
                motor_5_rpm = 5000 + np.random.normal(0, 200)  # Forward motor primary
            
            vtol_data.append({
                'timestamp': f"2024-01-01T10:{i//60:02d}:{i%60:02d}",
                'altitude': altitude,
                'battery_voltage': 12.8 - (i / 200) * 2.0,
                'motor_1_rpm': motor_1_rpm,
                'motor_2_rpm': motor_2_rpm,
                'motor_3_rpm': motor_3_rpm,
                'motor_4_rpm': motor_4_rpm,
                'motor_5_rpm': motor_5_rpm,  # 5TH MOTOR - KEY VTOL IDENTIFIER
                'gps_hdop': 1.2 + np.random.normal(0, 0.2),
                'vibration_x': np.random.normal(0, 2.5),
                'vibration_y': np.random.normal(0, 2.5),
                'vibration_z': np.random.normal(0, 2),
                'speed': speed,
                'temperature': 28 + np.random.normal(0, 2),
                'elevator': np.random.normal(0, 1),  # HAS CONTROL SURFACES
                'aileron': np.random.normal(0, 1.2)
            })
        datasets['extreme_vtol'] = vtol_data
        
        return datasets
    
    def save_debug_datasets(self, datasets):
        """Save datasets and return file paths"""
        filepaths = {}
        
        for name, data in datasets.items():
            filepath = self.test_data_dir / f"debug_{name}.csv"
            
            with open(filepath, 'w', newline='') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            filepaths[name] = filepath
            print(f"   Saved {len(data)} points to: {filepath}")
        
        return filepaths
    
    def analyze_dataset_characteristics(self, datasets):
        """Analyze the characteristics of each dataset"""
        
        self.print_header("Dataset Characteristics Analysis")
        
        for name, data in datasets.items():
            print(f"\n🔍 Analyzing {name.replace('_', ' ').title()}:")
            df = pd.DataFrame(data)
            
            # Motor analysis
            motor_cols = [col for col in df.columns if 'motor' in col and 'rpm' in col]
            active_motors = 0
            motor_rpms = []
            
            for col in motor_cols:
                avg_rpm = df[col].mean()
                if avg_rpm > 500:
                    active_motors += 1
                    motor_rpms.append(avg_rpm)
                print(f"   • {col}: {avg_rpm:.0f} RPM ({'ACTIVE' if avg_rpm > 500 else 'INACTIVE'})")
            
            print(f"   • Active Motors: {active_motors}")
            
            # Speed analysis
            avg_speed = df['speed'].mean()
            max_speed = df['speed'].max()
            print(f"   • Speed: avg={avg_speed:.1f} m/s, max={max_speed:.1f} m/s")
            
            # Altitude analysis
            alt_std = df['altitude'].std()
            alt_range = df['altitude'].max() - df['altitude'].min()
            print(f"   • Altitude: std={alt_std:.1f}m, range={alt_range:.1f}m")
            
            # Vibration analysis
            vib_cols = [col for col in df.columns if 'vibration' in col]
            if vib_cols:
                avg_vib = np.mean([df[col].abs().mean() for col in vib_cols])
                print(f"   • Vibration: avg={avg_vib:.1f}")
            
            # Control surfaces
            control_cols = ['elevator', 'aileron', 'rudder']
            has_controls = any(col in df.columns for col in control_cols)
            print(f"   • Control Surfaces: {'YES' if has_controls else 'NO'}")
            
            print(f"   • Expected Detection: {name.split('_')[1].upper()}")
    
    def test_detection_logic_step_by_step(self, datasets, filepaths):
        """Test the detection logic step by step with detailed debugging"""
        
        self.print_header("Step-by-Step Detection Logic Testing")
        
        for name, filepath in filepaths.items():
            expected_type = name.split('_')[1]  # Extract type from name
            
            print(f"\n🧪 Testing {name} (expecting {expected_type}):")
            print(f"   File: {filepath}")
            
            # Load the data
            df = pd.DataFrame(datasets[name])
            
            try:
                # Test the actual detection logic
                detected_type, confidence = self.detector.detect_aircraft_type(df)
                
                print(f"   🎯 Result: {detected_type} (confidence: {confidence:.3f})")
                print(f"   ✅ Expected: {expected_type}")
                
                correct = (detected_type.lower() == expected_type.lower() or 
                          (hasattr(detected_type, 'value') and detected_type.value == expected_type))
                
                status = "✅ CORRECT" if correct else "❌ WRONG"
                print(f"   📊 Status: {status}")
                
                # If we have access to the internal methods, debug them
                if hasattr(self.detector, '_analyze_motors'):
                    motor_analysis = self.detector._analyze_motors(df)
                    print(f"   🔧 Motor Analysis: {motor_analysis}")
                
                if hasattr(self.detector, '_analyze_flight_patterns'):
                    flight_patterns = self.detector._analyze_flight_patterns(df)
                    print(f"   🔧 Flight Patterns: {flight_patterns}")
                
                if hasattr(self.detector, '_analyze_speed_patterns'):
                    speed_analysis = self.detector._analyze_speed_patterns(df)
                    print(f"   🔧 Speed Analysis: {speed_analysis}")
                
            except Exception as e:
                print(f"   ❌ Detection Error: {e}")
                import traceback
                traceback.print_exc()
    
    def debug_scoring_algorithm(self, datasets):
        """Debug the scoring algorithm in detail"""
        
        self.print_header("Scoring Algorithm Deep Debug")
        
        # If we can access the detector's internal methods
        if not hasattr(self.detector, '_analyze_motors'):
            print("❌ Cannot access internal detector methods for debugging")
            return
        
        for name, data in datasets.items():
            expected_type = name.split('_')[1]
            df = pd.DataFrame(data)
            
            print(f"\n🔬 Deep Analysis: {name} (expecting {expected_type})")
            
            try:
                # Get all the analysis components
                motor_analysis = self.detector._analyze_motors(df)
                flight_patterns = self.detector._analyze_flight_patterns(df)
                control_surfaces = self.detector._analyze_control_surfaces(df)
                speed_analysis = self.detector._analyze_speed_patterns(df)
                
                print(f"   🔧 Motor Analysis:")
                for key, value in motor_analysis.items():
                    print(f"      • {key}: {value}")
                
                print(f"   🔧 Flight Patterns:")
                for key, value in flight_patterns.items():
                    print(f"      • {key}: {value}")
                
                print(f"   🔧 Control Surfaces:")
                for key, value in control_surfaces.items():
                    print(f"      • {key}: {value}")
                
                print(f"   🔧 Speed Analysis:")
                for key, value in speed_analysis.items():
                    print(f"      • {key}: {value}")
                
                # Manual scoring calculation
                print(f"   📊 Manual Score Calculation:")
                
                # Fixed-wing scoring
                fw_score = 0.0
                if motor_analysis['active_motors'] == 1:
                    fw_score += 0.3
                    print(f"      • Fixed-wing motor bonus: +0.3 (total: {fw_score})")
                if control_surfaces.get('has_elevator', False) or control_surfaces.get('has_aileron', False):
                    fw_score += 0.2
                    print(f"      • Fixed-wing control surfaces bonus: +0.2 (total: {fw_score})")
                if flight_patterns['cruise_ratio'] > 0.6:
                    fw_score += 0.2
                    print(f"      • Fixed-wing cruise bonus: +0.2 (total: {fw_score})")
                if speed_analysis['avg_speed'] > 15:
                    fw_score += 0.2
                    print(f"      • Fixed-wing speed bonus: +0.2 (total: {fw_score})")
                if flight_patterns['vertical_transitions'] < 0.2:
                    fw_score += 0.1
                    print(f"      • Fixed-wing stability bonus: +0.1 (total: {fw_score})")
                
                # Multirotor scoring
                mr_score = 0.0
                if motor_analysis['active_motors'] >= 4:
                    mr_score += 0.3
                    print(f"      • Multirotor motor bonus: +0.3 (total: {mr_score})")
                if flight_patterns['hover_ratio'] > 0.3:
                    mr_score += 0.2
                    print(f"      • Multirotor hover bonus: +0.2 (total: {mr_score})")
                if flight_patterns['vertical_transitions'] > 0.4:
                    mr_score += 0.2
                    print(f"      • Multirotor agility bonus: +0.2 (total: {mr_score})")
                if speed_analysis['avg_speed'] < 15:
                    mr_score += 0.1
                    print(f"      • Multirotor speed bonus: +0.1 (total: {mr_score})")
                if motor_analysis['motor_symmetry'] > 0.7:
                    mr_score += 0.2
                    print(f"      • Multirotor symmetry bonus: +0.2 (total: {mr_score})")
                
                # VTOL scoring
                vtol_score = 0.0
                if motor_analysis['active_motors'] >= 5:
                    vtol_score += 0.2
                    print(f"      • VTOL motor count bonus: +0.2 (total: {vtol_score})")
                if flight_patterns['hover_ratio'] > 0.2 and flight_patterns['cruise_ratio'] > 0.3:
                    vtol_score += 0.3
                    print(f"      • VTOL dual-mode bonus: +0.3 (total: {vtol_score})")
                if control_surfaces.get('has_elevator', False) and motor_analysis['active_motors'] >= 4:
                    vtol_score += 0.2
                    print(f"      • VTOL hybrid bonus: +0.2 (total: {vtol_score})")
                if flight_patterns['transition_events'] > 0:
                    vtol_score += 0.3
                    print(f"      • VTOL transition bonus: +0.3 (total: {vtol_score})")
                
                print(f"   📊 Final Scores:")
                print(f"      • Fixed-wing: {fw_score:.2f}")
                print(f"      • Multirotor: {mr_score:.2f}")
                print(f"      • VTOL: {vtol_score:.2f}")
                
                best_score = max(fw_score, mr_score, vtol_score)
                if best_score == fw_score:
                    predicted = "fixed_wing"
                elif best_score == mr_score:
                    predicted = "multirotor"
                else:
                    predicted = "vtol"
                
                print(f"   🎯 Predicted: {predicted} (score: {best_score:.2f})")
                print(f"   ✅ Expected: {expected_type}")
                
                correct = predicted == expected_type
                status = "✅ CORRECT" if correct else "❌ WRONG"
                print(f"   📊 Manual Calculation: {status}")
                
            except Exception as e:
                print(f"   ❌ Debug Error: {e}")
                import traceback
                traceback.print_exc()
    
    def run_comprehensive_debug(self):
        """Run comprehensive debugging of the aircraft detection system"""
        
        print("🚨 DBX AI Aviation System - Aircraft Detection Logic Debugger")
        print("=" * 70)
        print("Debugging the 33% accuracy issue in aircraft type detection")
        
        # Step 1: Create debug datasets
        self.print_header("Creating Debug Datasets")
        datasets = self.create_debug_datasets()
        filepaths = self.save_debug_datasets(datasets)
        
        # Step 2: Analyze dataset characteristics
        self.analyze_dataset_characteristics(datasets)
        
        # Step 3: Test detection logic
        self.test_detection_logic_step_by_step(datasets, filepaths)
        
        # Step 4: Debug scoring algorithm
        self.debug_scoring_algorithm(datasets)
        
        # Step 5: Summary and recommendations
        self.print_header("Debug Summary and Recommendations")
        
        print("🔍 Key Findings:")
        print("1. Check if the detector is using fallback logic")
        print("2. Verify that feature extraction is working correctly")
        print("3. Ensure scoring thresholds are appropriate")
        print("4. Validate that all analysis methods are functioning")
        
        print("\n🔧 Immediate Actions:")
        print("1. Add debug logging to aircraft_detector.py")
        print("2. Verify confidence threshold settings")
        print("3. Check for exception handling that might cause fallbacks")
        print("4. Test with even more extreme datasets")
        
        print("\n📊 Expected vs Actual:")
        print("- All three aircraft types should be detectable with >90% accuracy")
        print("- Current system appears to default to multirotor")
        print("- This suggests either fallback logic or broken feature analysis")

def main():
    debugger = AircraftDetectionDebugger()
    debugger.run_comprehensive_debug()

if __name__ == "__main__":
    main()