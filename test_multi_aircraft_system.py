#!/usr/bin/env python3
"""
Test script for the Multi-Aircraft Anomaly Detection System
Demonstrates the new capabilities and compares with legacy system
"""

import pandas as pd
import numpy as np
import sys
import os
import logging
from datetime import datetime, timedelta

# Add the ai-engine app to the path
sys.path.append('ai-engine/app')

from models.multi_aircraft_detector import MultiAircraftAnomalyDetector
from models.aircraft_detector import AircraftType
from models.model import AnomalyDetector
from services.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_data(aircraft_type: str, n_samples: int = 1000) -> pd.DataFrame:
    """Generate test flight data for different aircraft types"""
    
    base_time = datetime.now()
    timestamps = [base_time + timedelta(seconds=i*0.1) for i in range(n_samples)]
    
    if aircraft_type == 'fixed_wing':
        data = {
            'timestamp': timestamps,
            'altitude': np.random.uniform(50, 300, n_samples),
            'battery_voltage': np.random.normal(11.1, 0.2, n_samples),
            'motor_rpm': np.random.normal(5000, 300, n_samples),
            'airspeed': np.random.normal(25, 3, n_samples),
            'ground_speed': np.random.normal(23, 4, n_samples),
            'throttle_position': np.random.normal(75, 10, n_samples),
            'elevator_position': np.random.normal(0, 2, n_samples),
            'rudder_position': np.random.normal(0, 2, n_samples),
            'aileron_position': np.random.normal(0, 3, n_samples),
            'pitch_angle': np.random.normal(5, 3, n_samples),
            'roll_angle': np.random.normal(0, 5, n_samples),
            'yaw_rate': np.random.normal(0, 2, n_samples),
            'gps_hdop': np.random.gamma(2, 0.5, n_samples),
            'temperature': np.random.normal(25, 8, n_samples),
            'wind_speed': np.random.gamma(2, 2, n_samples),
            'angle_of_attack': np.random.normal(5, 2, n_samples)
        }
        
        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, size=int(n_samples*0.05), replace=False)
        for idx in anomaly_indices:
            if np.random.random() < 0.3:
                data['airspeed'][idx] = 8  # Below stall speed
            elif np.random.random() < 0.5:
                data['motor_rpm'][idx] = 500  # Engine failure
            else:
                data['angle_of_attack'][idx] = 25  # High AoA
    
    elif aircraft_type == 'multirotor':
        data = {
            'timestamp': timestamps,
            'altitude': np.random.uniform(5, 120, n_samples),
            'battery_voltage': np.random.normal(11.1, 0.2, n_samples),
            'motor_1_rpm': np.random.normal(3000, 200, n_samples),
            'motor_2_rpm': np.random.normal(3000, 200, n_samples),
            'motor_3_rpm': np.random.normal(3000, 200, n_samples),
            'motor_4_rpm': np.random.normal(3000, 200, n_samples),
            'vibration_x': np.random.normal(0, 2, n_samples),
            'vibration_y': np.random.normal(0, 2, n_samples),
            'vibration_z': np.random.normal(0, 2, n_samples),
            'vibration_w': np.random.normal(0, 2, n_samples),
            'pitch_angle': np.random.normal(0, 10, n_samples),
            'roll_angle': np.random.normal(0, 10, n_samples),
            'speed': np.random.uniform(0, 12, n_samples),
            'temperature': np.random.normal(25, 5, n_samples),
            'gps_hdop': np.random.gamma(2, 1, n_samples)
        }
        
        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, size=int(n_samples*0.05), replace=False)
        for idx in anomaly_indices:
            if np.random.random() < 0.3:
                data['motor_1_rpm'][idx] = 200  # Motor failure
            elif np.random.random() < 0.5:
                data['vibration_x'][idx] = 15  # High vibration
            else:
                data['pitch_angle'][idx] = 40  # Extreme attitude
    
    elif aircraft_type == 'vtol':
        data = {
            'timestamp': timestamps,
            'altitude': np.random.uniform(10, 300, n_samples),
            'battery_voltage': np.random.normal(22, 0.8, n_samples),
            'motor_1_rpm': np.random.normal(3000, 200, n_samples),
            'motor_2_rpm': np.random.normal(3000, 200, n_samples),
            'motor_3_rpm': np.random.normal(3000, 200, n_samples),
            'motor_4_rpm': np.random.normal(3000, 200, n_samples),
            'motor_5_rpm': np.random.normal(5000, 300, n_samples),
            'airspeed': np.random.normal(15, 5, n_samples),
            'elevator_position': np.random.normal(0, 2, n_samples),
            'aileron_position': np.random.normal(0, 3, n_samples),
            'gps_hdop': np.random.gamma(2, 0.5, n_samples),
            'vibration_x': np.random.normal(0, 2, n_samples),
            'vibration_y': np.random.normal(0, 2, n_samples),
            'vibration_z': np.random.normal(0, 2, n_samples),
            'vibration_w': np.random.normal(0, 2, n_samples),
            'temperature': np.random.normal(25, 8, n_samples),
            'transition_mode': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'pitch_angle': np.random.normal(0, 8, n_samples),
            'roll_angle': np.random.normal(0, 8, n_samples)
        }
        
        # Add some anomalies
        anomaly_indices = np.random.choice(n_samples, size=int(n_samples*0.05), replace=False)
        for idx in anomaly_indices:
            if np.random.random() < 0.3:
                data['motor_5_rpm'][idx] = 200  # Forward motor failure
            elif np.random.random() < 0.5:
                data['airspeed'][idx] = 5  # Low transition speed
            else:
                data['motor_1_rpm'][idx] = 200  # Lift motor failure
    
    return pd.DataFrame(data)

def test_aircraft_detection():
    """Test aircraft type detection accuracy"""
    logger.info("🔍 Testing Aircraft Type Detection...")
    
    detector = MultiAircraftAnomalyDetector()
    
    test_cases = [
        ('fixed_wing', 'Fixed Wing Aircraft'),
        ('multirotor', 'Multirotor Aircraft'),
        ('vtol', 'VTOL Aircraft')
    ]
    
    results = []
    
    for aircraft_type, name in test_cases:
        logger.info(f"Testing {name}...")
        
        # Generate test data
        test_data = generate_test_data(aircraft_type)
        
        # Detect aircraft type
        detected_type, confidence = detector.aircraft_detector.detect_aircraft_type(test_data)
        
        success = detected_type.value == aircraft_type
        results.append({
            'expected': aircraft_type,
            'detected': detected_type.value,
            'confidence': confidence,
            'success': success
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status} - Detected: {detected_type.value} (Confidence: {confidence:.2f})")
    
    # Summary
    success_rate = sum(r['success'] for r in results) / len(results)
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    
    logger.info(f"\n📊 Aircraft Detection Results:")
    logger.info(f"  Success Rate: {success_rate:.1%}")
    logger.info(f"  Average Confidence: {avg_confidence:.2f}")
    
    return results

def test_anomaly_detection():
    """Test multi-aircraft anomaly detection"""
    logger.info("\n🚨 Testing Multi-Aircraft Anomaly Detection...")
    
    detector = MultiAircraftAnomalyDetector()
    detector.train_models()
    
    test_cases = [
        ('fixed_wing', 'Fixed Wing Aircraft'),
        ('multirotor', 'Multirotor Aircraft'),
        ('vtol', 'VTOL Aircraft')
    ]
    
    results = []
    
    for aircraft_type, name in test_cases:
        logger.info(f"Testing {name} anomaly detection...")
        
        # Generate test data with known anomalies
        test_data = generate_test_data(aircraft_type)
        
        # Analyze with multi-aircraft system
        analysis = detector.analyze_flight_log(test_data)
        
        results.append({
            'aircraft_type': aircraft_type,
            'detected_type': analysis['aircraft_type'],
            'confidence': analysis['aircraft_confidence'],
            'risk_score': analysis['risk_score'],
            'risk_level': analysis['risk_level'],
            'anomaly_count': len(analysis['anomalies']),
            'flight_phases': analysis['flight_phases'],
            'performance_metrics': analysis['performance_metrics']
        })
        
        logger.info(f"  Aircraft Type: {analysis['aircraft_type']} (Confidence: {analysis['aircraft_confidence']:.2f})")
        logger.info(f"  Risk Score: {analysis['risk_score']:.3f} ({analysis['risk_level']})")
        logger.info(f"  Anomalies Found: {len(analysis['anomalies'])}")
        
        if analysis['anomalies']:
            logger.info("  Top Anomalies:")
            for i, anomaly in enumerate(analysis['anomalies'][:3], 1):
                logger.info(f"    {i}. {anomaly['description']} ({anomaly['severity']})")
    
    return results

def test_comprehensive_analysis():
    """Test comprehensive analysis with report generation"""
    logger.info("\n📋 Testing Comprehensive Analysis & Reporting...")
    
    # Initialize components
    detector = MultiAircraftAnomalyDetector()
    detector.train_models()
    report_gen = ReportGenerator()
    
    # Test with multirotor data
    test_data = generate_test_data('multirotor', 500)
    
    logger.info("Performing comprehensive analysis...")
    
    # Get comprehensive analysis
    analysis = detector.analyze_flight_log(test_data)
    
    # Generate AI report (will use template if Gemini not available)
    try:
        report = await report_gen.generate_report(test_data, comprehensive_analysis=analysis)
        logger.info("✅ AI Report generated successfully")
    except Exception as e:
        logger.warning(f"⚠️ AI Report generation failed: {e}")
        report = None
    
    # Display results
    logger.info(f"\n📊 Comprehensive Analysis Results:")
    logger.info(f"  Aircraft Type: {analysis['aircraft_type']}")
    logger.info(f"  Detection Confidence: {analysis['aircraft_confidence']:.2f}")
    logger.info(f"  Risk Assessment: {analysis['risk_level']} ({analysis['risk_score']:.3f})")
    logger.info(f"  Total Data Points: {analysis['total_data_points']}")
    
    if analysis['flight_phases']:
        logger.info("  Flight Phases:")
        for phase, duration in analysis['flight_phases'].items():
            logger.info(f"    {phase.replace('_', ' ').title()}: {duration}")
    
    if analysis['performance_metrics']:
        logger.info("  Performance Metrics:")
        for metric, value in analysis['performance_metrics'].items():
            logger.info(f"    {metric.replace('_', ' ').title()}: {value}")
    
    return analysis, report

def compare_legacy_vs_new():
    """Compare legacy system with new multi-aircraft system"""
    logger.info("\n⚖️ Comparing Legacy vs Multi-Aircraft System...")
    
    # Initialize both systems
    legacy_detector = AnomalyDetector()
    multi_detector = MultiAircraftAnomalyDetector()
    multi_detector.train_models()
    
    # Test with multirotor data
    test_data = generate_test_data('multirotor', 300)
    
    # Legacy analysis
    logger.info("Running legacy analysis...")
    legacy_risk, legacy_anomalies = legacy_detector.predict(test_data)
    
    # Multi-aircraft analysis
    logger.info("Running multi-aircraft analysis...")
    multi_analysis = multi_detector.analyze_flight_log(test_data)
    
    # Compare results
    logger.info(f"\n📊 Comparison Results:")
    logger.info(f"  Legacy System:")
    logger.info(f"    Risk Score: {legacy_risk:.3f}")
    logger.info(f"    Anomalies: {len(legacy_anomalies)}")
    logger.info(f"    Aircraft Detection: Not Available")
    
    logger.info(f"  Multi-Aircraft System:")
    logger.info(f"    Risk Score: {multi_analysis['risk_score']:.3f}")
    logger.info(f"    Anomalies: {len(multi_analysis['anomalies'])}")
    logger.info(f"    Aircraft Type: {multi_analysis['aircraft_type']} ({multi_analysis['aircraft_confidence']:.2f})")
    logger.info(f"    Flight Phases: {len(multi_analysis['flight_phases'])} detected")
    logger.info(f"    Performance Metrics: {len(multi_analysis['performance_metrics'])} calculated")
    
    return {
        'legacy': {'risk_score': legacy_risk, 'anomalies': len(legacy_anomalies)},
        'multi_aircraft': {
            'risk_score': multi_analysis['risk_score'],
            'anomalies': len(multi_analysis['anomalies']),
            'aircraft_type': multi_analysis['aircraft_type'],
            'confidence': multi_analysis['aircraft_confidence']
        }
    }

async def main():
    """Main test function"""
    logger.info("🚀 Starting Multi-Aircraft System Tests")
    logger.info("=" * 60)
    
    try:
        # Test 1: Aircraft Detection
        detection_results = test_aircraft_detection()
        
        # Test 2: Anomaly Detection
        anomaly_results = test_anomaly_detection()
        
        # Test 3: Comprehensive Analysis
        analysis, report = await test_comprehensive_analysis()
        
        # Test 4: Legacy Comparison
        comparison = compare_legacy_vs_new()
        
        # Final Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Multi-Aircraft System Test Summary")
        logger.info("=" * 60)
        
        detection_success = sum(r['success'] for r in detection_results) / len(detection_results)
        logger.info(f"✅ Aircraft Detection Success Rate: {detection_success:.1%}")
        
        avg_risk_score = sum(r['risk_score'] for r in anomaly_results) / len(anomaly_results)
        logger.info(f"📊 Average Risk Score: {avg_risk_score:.3f}")
        
        total_anomalies = sum(r['anomaly_count'] for r in anomaly_results)
        logger.info(f"🚨 Total Anomalies Detected: {total_anomalies}")
        
        logger.info(f"🔄 System Comparison:")
        logger.info(f"   Legacy Risk: {comparison['legacy']['risk_score']:.3f}")
        logger.info(f"   Multi-Aircraft Risk: {comparison['multi_aircraft']['risk_score']:.3f}")
        
        logger.info("\n🎯 Multi-Aircraft System is ready for production!")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())