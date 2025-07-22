#!/usr/bin/env python3
"""
Windows-Compatible Multi-Aircraft Model Training Script
Trains specialized XGBoost models for Fixed-Wing, Multirotor, and VTOL aircraft
"""

import sys
import os
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import json

# Windows-compatible console output
if sys.platform.startswith('win'):
    os.system('chcp 65001 >nul')  # Set UTF-8 code page

def install_dependencies():
    """Install required dependencies"""
    print("[SETUP] Installing required dependencies...")
    
    required_packages = [
        'scikit-learn',
        'xgboost', 
        'pandas',
        'numpy'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"[OK] {package} already installed")
        except ImportError:
            print(f"[INSTALL] Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"[OK] {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to install {package}: {e}")
                return False
    
    return True

def setup_directories():
    """Create necessary directories for training"""
    directories = [
        'data/models',
        'data/logs', 
        'data/cache',
        'data/training_data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[OK] Directory ready: {directory}")

def train_multi_aircraft_models():
    """Train all multi-aircraft models"""
    print("[TRAINING] Starting Multi-Aircraft Model Training")
    print("=" * 60)
    
    try:
        # Add the ai-engine app to the path
        sys.path.append('ai-engine/app')
        
        from models.multi_aircraft_detector import MultiAircraftAnomalyDetector
        from models.aircraft_detector import AircraftType
        
        # Initialize the multi-aircraft detector
        detector = MultiAircraftAnomalyDetector()
        
        # Train models for each aircraft type
        aircraft_types = [AircraftType.FIXED_WING, AircraftType.MULTIROTOR, AircraftType.VTOL]
        training_results = {}
        
        for aircraft_type in aircraft_types:
            print(f"\n[AIRCRAFT] Training {aircraft_type.value.upper()} Model")
            print("-" * 40)
            
            # Generate training data
            print("[DATA] Generating synthetic training data...")
            X, y = detector.generate_training_data(aircraft_type, n_samples=10000)
            
            print(f"[OK] Generated {len(X)} samples with {len(X.columns)} features")
            print(f"     Normal samples: {len(y[y==0])}")
            print(f"     Anomaly samples: {len(y[y==1])}")
            
            # Save training data for inspection
            training_data_path = f"data/training_data/{aircraft_type.value}_training_data.csv"
            X['label'] = y
            X.to_csv(training_data_path, index=False)
            print(f"[SAVE] Training data saved: {training_data_path}")
            
            # Prepare features
            X_features = X.drop('label', axis=1)
            
            # Scale features
            print("[SCALE] Scaling features...")
            scaler = detector.scalers[aircraft_type]
            X_scaled = scaler.fit_transform(X_features)
            
            # Train model
            print("[TRAIN] Training XGBoost model...")
            model = detector.models[aircraft_type]
            model.fit(X_scaled, y)
            
            # Evaluate model
            print("[EVAL] Evaluating model performance...")
            train_score = model.score(X_scaled, y)
            
            # Store results
            training_results[aircraft_type.value] = {
                'training_accuracy': float(train_score),
                'samples_trained': len(X),
                'features_used': list(X_features.columns),
                'feature_count': len(X_features.columns),
                'training_time': datetime.now().isoformat(),
                'model_params': model.get_params()
            }
            
            print(f"[OK] {aircraft_type.value.upper()} Model Training Complete")
            print(f"     Training Accuracy: {train_score:.3f}")
            print(f"     Features Used: {len(X_features.columns)}")
            
            # Save individual model and scaler
            model_path = f"data/models/{aircraft_type.value}_model.pkl"
            scaler_path = f"data/models/{aircraft_type.value}_scaler.pkl"
            
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
                
            print(f"[SAVE] Model saved: {model_path}")
            print(f"[SAVE] Scaler saved: {scaler_path}")
        
        # Save comprehensive training report
        training_report = {
            'training_timestamp': datetime.now().isoformat(),
            'system_version': '2.0.0',
            'training_method': 'synthetic_data_generation',
            'models_trained': list(training_results.keys()),
            'total_models': len(training_results),
            'results': training_results
        }
        
        report_path = "data/models/training_report.json"
        with open(report_path, 'w') as f:
            json.dump(training_report, f, indent=2)
        
        print(f"\n[REPORT] Training Report Saved: {report_path}")
        
        return training_results
        
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_trained_models():
    """Test the trained models with sample data"""
    print("\n[TEST] Testing Trained Models")
    print("-" * 30)
    
    try:
        sys.path.append('ai-engine/app')
        from models.multi_aircraft_detector import MultiAircraftAnomalyDetector
        from models.aircraft_detector import AircraftType
        import pickle
        
        # Initialize detector and load the trained models and scalers
        detector = MultiAircraftAnomalyDetector()
        
        # Load the trained models and scalers
        for aircraft_type in [AircraftType.FIXED_WING, AircraftType.MULTIROTOR, AircraftType.VTOL]:
            model_path = f"data/models/{aircraft_type.value}_model.pkl"
            scaler_path = f"data/models/{aircraft_type.value}_scaler.pkl"
            
            with open(model_path, 'rb') as f:
                detector.models[aircraft_type] = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                detector.scalers[aircraft_type] = pickle.load(f)
        
        print("[OK] Loaded trained models and scalers")
        
        # Generate test data for each aircraft type
        test_results = {}
        
        for aircraft_type_name in ['fixed_wing', 'multirotor', 'vtol']:
            print(f"\n[TEST] Testing {aircraft_type_name.upper()} detection...")
            
            # Create test flight data
            if aircraft_type_name == 'fixed_wing':
                test_data = pd.DataFrame({
                    'timestamp': pd.date_range('2025-01-20 10:00:00', periods=100, freq='0.1S'),
                    'altitude': np.random.uniform(100, 300, 100),
                    'battery_voltage': np.random.normal(11.1, 0.2, 100),
                    'motor_rpm': np.random.normal(5000, 300, 100),
                    'airspeed': np.random.normal(25, 3, 100),
                    'ground_speed': np.random.normal(23, 4, 100),
                    'throttle_position': np.random.normal(75, 10, 100),
                    'elevator_position': np.random.normal(0, 2, 100),
                    'rudder_position': np.random.normal(0, 2, 100),
                    'aileron_position': np.random.normal(0, 3, 100),
                    'pitch_angle': np.random.normal(5, 3, 100),
                    'roll_angle': np.random.normal(0, 5, 100),
                    'yaw_rate': np.random.normal(0, 2, 100),
                    'gps_hdop': np.random.gamma(2, 0.5, 100),
                    'temperature': np.random.normal(25, 8, 100),
                    'wind_speed': np.random.gamma(2, 2, 100),
                    'angle_of_attack': np.random.normal(5, 2, 100)
                })
            elif aircraft_type_name == 'multirotor':
                test_data = pd.DataFrame({
                    'timestamp': pd.date_range('2025-01-20 10:00:00', periods=100, freq='0.1S'),
                    'altitude': np.random.uniform(5, 120, 100),
                    'battery_voltage': np.random.normal(11.1, 0.2, 100),
                    'motor_1_rpm': np.random.normal(3000, 200, 100),
                    'motor_2_rpm': np.random.normal(3000, 200, 100),
                    'motor_3_rpm': np.random.normal(3000, 200, 100),
                    'motor_4_rpm': np.random.normal(3000, 200, 100),
                    'vibration_x': np.random.normal(0, 2, 100),
                    'vibration_y': np.random.normal(0, 2, 100),
                    'vibration_z': np.random.normal(0, 2, 100),
                    'vibration_w': np.random.normal(0, 2, 100),
                    'pitch_angle': np.random.normal(0, 10, 100),
                    'roll_angle': np.random.normal(0, 10, 100),
                    'speed': np.random.uniform(0, 12, 100),
                    'temperature': np.random.normal(25, 5, 100),
                    'gps_hdop': np.random.gamma(2, 1, 100)
                })
            else:  # VTOL
                test_data = pd.DataFrame({
                    'timestamp': pd.date_range('2025-01-20 10:00:00', periods=100, freq='0.1S'),
                    'altitude': np.random.uniform(10, 300, 100),
                    'battery_voltage': np.random.normal(22, 0.8, 100),
                    'motor_1_rpm': np.random.normal(3000, 200, 100),
                    'motor_2_rpm': np.random.normal(3000, 200, 100),
                    'motor_3_rpm': np.random.normal(3000, 200, 100),
                    'motor_4_rpm': np.random.normal(3000, 200, 100),
                    'motor_5_rpm': np.random.normal(5000, 300, 100),
                    'airspeed': np.random.normal(15, 5, 100),
                    'elevator_position': np.random.normal(0, 2, 100),
                    'aileron_position': np.random.normal(0, 3, 100),
                    'gps_hdop': np.random.gamma(2, 0.5, 100),
                    'vibration_x': np.random.normal(0, 2, 100),
                    'vibration_y': np.random.normal(0, 2, 100),
                    'vibration_z': np.random.normal(0, 2, 100),
                    'vibration_w': np.random.normal(0, 2, 100),
                    'temperature': np.random.normal(25, 8, 100),
                    'transition_mode': np.random.choice([0, 1], 100, p=[0.8, 0.2]),
                    'pitch_angle': np.random.normal(0, 8, 100),
                    'roll_angle': np.random.normal(0, 8, 100)
                })
            
            # Analyze with the trained system
            result = detector.analyze_flight_log(test_data)
            
            test_results[aircraft_type_name] = {
                'detected_type': result['aircraft_type'],
                'confidence': result['aircraft_confidence'],
                'risk_score': result['risk_score'],
                'risk_level': result['risk_level'],
                'anomalies_found': len(result['anomalies']),
                'flight_phases': result['flight_phases'],
                'performance_metrics': result['performance_metrics']
            }
            
            print(f"[OK] {aircraft_type_name.upper()} Test Results:")
            print(f"     Detected as: {result['aircraft_type']} (confidence: {result['aircraft_confidence']:.2f})")
            print(f"     Risk Level: {result['risk_level']} ({result['risk_score']:.3f})")
            print(f"     Anomalies: {len(result['anomalies'])}")
        
        # Save test results
        test_report_path = "data/models/test_results.json"
        with open(test_report_path, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"\n[REPORT] Test Results Saved: {test_report_path}")
        
        return test_results
        
    except Exception as e:
        print(f"[ERROR] Testing failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def generate_training_summary():
    """Generate a comprehensive training summary"""
    print("\n[SUMMARY] Training Summary")
    print("=" * 50)
    
    try:
        # Load training report
        with open("data/models/training_report.json", 'r') as f:
            training_report = json.load(f)
        
        # Load test results
        with open("data/models/test_results.json", 'r') as f:
            test_results = json.load(f)
        
        print("[SUCCESS] Multi-Aircraft Models Trained Successfully")
        print(f"          Training Time: {training_report['training_timestamp']}")
        print(f"          Models Trained: {training_report['total_models']}")
        print(f"          System Version: {training_report['system_version']}")
        
        print("\n[PERFORMANCE] Model Performance:")
        for aircraft_type, results in training_report['results'].items():
            print(f"              {aircraft_type.upper()}:")
            print(f"              - Training Accuracy: {results['training_accuracy']:.3f}")
            print(f"              - Features: {results['feature_count']}")
            print(f"              - Samples: {results['samples_trained']}")
        
        print("\n[TEST] Test Results:")
        for aircraft_type, results in test_results.items():
            print(f"       {aircraft_type.upper()}:")
            print(f"       - Detection: {results['detected_type']} ({results['confidence']:.2f})")
            print(f"       - Risk Level: {results['risk_level']}")
        
        print("\n[FILES] Files Created:")
        print("        - data/models/fixed_wing_model.pkl")
        print("        - data/models/multirotor_model.pkl") 
        print("        - data/models/vtol_model.pkl")
        print("        - data/models/training_report.json")
        print("        - data/models/test_results.json")
        print("        - data/training_data/*.csv")
        
        print("\n[NEXT] Next Steps:")
        print("       1. Deploy system: python deploy.py")
        print("       2. Test API: curl http://localhost:8000/api/v2/model/info")
        print("       3. Analyze flight: POST /api/v2/analyze")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Summary generation failed: {e}")
        return False

def main():
    """Main training function"""
    print("[START] DBX AI Multi-Aircraft Model Training")
    print("=" * 60)
    
    try:
        # Install dependencies first
        if not install_dependencies():
            print("[ERROR] Failed to install dependencies")
            return False
        
        # Setup
        setup_directories()
        
        # Train models
        training_results = train_multi_aircraft_models()
        
        # Test models
        test_results = test_trained_models()
        
        # Generate summary
        generate_training_summary()
        
        print("\n[SUCCESS] Training Completed Successfully!")
        print("Your multi-aircraft models are ready for deployment.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Training process failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)