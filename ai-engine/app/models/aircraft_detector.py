import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging
from dataclasses import dataclass

# Configuration constants
AIRCRAFT_DETECTION_CONFIDENCE_THRESHOLD = 0.8
FIXED_WING_STALL_SPEED = 12
FIXED_WING_MAX_AIRSPEED = 45
MULTIROTOR_MAX_TILT_ANGLE = 30
MULTIROTOR_VIBRATION_THRESHOLD = 10
MULTIROTOR_MOTOR_ASYMMETRY_THRESHOLD = 1000

class AircraftType(Enum):
    FIXED_WING = "fixed_wing"
    MULTIROTOR = "multirotor"
    VTOL = "vtol"
    UNKNOWN = "unknown"

@dataclass
class AircraftSignature:
    motor_count: int
    has_control_surfaces: bool
    vertical_takeoff_capable: bool
    cruise_speed_range: Tuple[float, float]
    typical_flight_pattern: str

class AircraftTypeDetector:
    """Intelligent aircraft type detection based on flight log characteristics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.signatures = self._initialize_signatures()
    
    def _initialize_signatures(self) -> Dict[AircraftType, AircraftSignature]:
        """Define aircraft type signatures"""
        return {
            AircraftType.FIXED_WING: AircraftSignature(
                motor_count=1,
                has_control_surfaces=True,
                vertical_takeoff_capable=False,
                cruise_speed_range=(15, 50),
                typical_flight_pattern="linear_cruise"
            ),
            AircraftType.MULTIROTOR: AircraftSignature(
                motor_count=4,
                has_control_surfaces=False,
                vertical_takeoff_capable=True,
                cruise_speed_range=(0, 20),
                typical_flight_pattern="hover_maneuver"
            ),
            AircraftType.VTOL: AircraftSignature(
                motor_count=5,
                has_control_surfaces=True,
                vertical_takeoff_capable=True,
                cruise_speed_range=(10, 35),
                typical_flight_pattern="transition_cruise"
            )
        }
    
    def detect_aircraft_type(self, df: pd.DataFrame, confidence_threshold: float = AIRCRAFT_DETECTION_CONFIDENCE_THRESHOLD) -> Tuple[AircraftType, float]:
        """Detect aircraft type from flight log data"""
        try:
            motor_analysis = self._analyze_motors(df)
            flight_patterns = self._analyze_flight_patterns(df)
            control_surfaces = self._analyze_control_surfaces(df)
            speed_analysis = self._analyze_speed_patterns(df)
            
            scores = {}
            
            # Fixed-wing scoring
            fw_score = 0.0
            if motor_analysis['active_motors'] == 1:
                fw_score += 0.3
            if control_surfaces.get('has_elevator', False) or control_surfaces.get('has_aileron', False):
                fw_score += 0.2
            if flight_patterns['cruise_ratio'] > 0.6:
                fw_score += 0.2
            if speed_analysis['avg_speed'] > 15:
                fw_score += 0.2
            if flight_patterns['vertical_transitions'] < 0.2:
                fw_score += 0.1
            scores[AircraftType.FIXED_WING] = fw_score
            
            # Multirotor scoring
            mr_score = 0.0
            if motor_analysis['active_motors'] >= 4:
                mr_score += 0.3
            if flight_patterns['hover_ratio'] > 0.3:
                mr_score += 0.2
            if flight_patterns['vertical_transitions'] > 0.4:
                mr_score += 0.2
            if speed_analysis['avg_speed'] < 15:
                mr_score += 0.1
            if motor_analysis['motor_symmetry'] > 0.7:
                mr_score += 0.2
            scores[AircraftType.MULTIROTOR] = mr_score
            
            # VTOL scoring
            vtol_score = 0.0
            if motor_analysis['active_motors'] >= 5:
                vtol_score += 0.2
            if flight_patterns['hover_ratio'] > 0.2 and flight_patterns['cruise_ratio'] > 0.3:
                vtol_score += 0.3
            if control_surfaces.get('has_elevator', False) and motor_analysis['active_motors'] >= 4:
                vtol_score += 0.2
            if flight_patterns['transition_events'] > 0:
                vtol_score += 0.3
            scores[AircraftType.VTOL] = vtol_score
            
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type]
            
            if confidence < confidence_threshold:
                self.logger.warning(f"Low confidence ({confidence:.2f}) in aircraft type detection")
                return AircraftType.UNKNOWN, confidence
            
            self.logger.info(f"Detected aircraft type: {best_type.value} (confidence: {confidence:.2f})")
            return best_type, confidence
            
        except Exception as e:
            self.logger.error(f"Aircraft type detection failed: {e}")
            return AircraftType.UNKNOWN, 0.0
    
    def _analyze_motors(self, df: pd.DataFrame) -> Dict:
        """Analyze motor configuration and performance"""
        motor_cols = [col for col in df.columns if 'motor' in col.lower() and 'rpm' in col.lower()]
        
        if not motor_cols:
            return {
                'active_motors': 0,
                'motor_symmetry': 0.0,
                'motor_balance': 0.0
            }
        
        active_motors = 0
        motor_values = []
        
        for col in motor_cols:
            motor_data = df[col].fillna(0)
            if motor_data.max() > 500:
                active_motors += 1
                motor_values.append(motor_data.mean())
        
        motor_symmetry = 0.0
        if len(motor_values) > 1:
            motor_std = np.std(motor_values)
            motor_mean = np.mean(motor_values)
            if motor_mean > 0:
                motor_symmetry = max(0.0, 1.0 - (motor_std / motor_mean))
        
        return {
            'active_motors': active_motors,
            'motor_symmetry': motor_symmetry,
            'motor_balance': np.std(motor_values) if motor_values else 0.0
        }
    
    def _analyze_flight_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze flight patterns characteristic of different aircraft types"""
        if 'altitude' not in df.columns or 'speed' not in df.columns:
            return {
                'hover_ratio': 0.0,
                'cruise_ratio': 0.0,
                'vertical_transitions': 0.0,
                'transition_events': 0
            }
        
        hover_mask = (df['speed'] < 2) & (df['altitude'].diff().abs() < 2)
        hover_ratio = len(df[hover_mask]) / len(df) if len(df) > 0 else 0.0
        
        cruise_mask = (df['speed'] > 10) & (df['altitude'].rolling(10).std() < 5)
        cruise_ratio = len(df[cruise_mask]) / len(df) if len(df) > 0 else 0.0
        
        alt_changes = df['altitude'].diff().abs()
        vertical_transitions = len(alt_changes[alt_changes > 5]) / len(df) if len(df) > 0 else 0.0
        
        transition_events = 0
        if len(df) > 10:
            for i in range(10, len(df)-5):
                alt_change = abs(df['altitude'].iloc[i+5] - df['altitude'].iloc[i])
                speed_change = abs(df['speed'].iloc[i+5] - df['speed'].iloc[i])
                if alt_change > 20 and speed_change > 5:
                    transition_events += 1
        
        return {
            'hover_ratio': hover_ratio,
            'cruise_ratio': cruise_ratio,
            'vertical_transitions': vertical_transitions,
            'transition_events': transition_events
        }
    
    def _analyze_control_surfaces(self, df: pd.DataFrame) -> Dict:
        """Detect presence and usage of control surfaces"""
        control_surface_cols = ['elevator', 'aileron', 'rudder', 'throttle']
        detected_surfaces = {}
        
        for surface in control_surface_cols:
            surface_cols = [col for col in df.columns if surface in col.lower()]
            if surface_cols:
                surface_data = df[surface_cols[0]].fillna(0)
                detected_surfaces[f'has_{surface}'] = surface_data.var() > 1.0
            else:
                detected_surfaces[f'has_{surface}'] = False
        
        return detected_surfaces
    
    def _analyze_speed_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze speed patterns"""
        if 'speed' not in df.columns:
            return {
                'avg_speed': 0.0,
                'max_speed': 0.0,
                'speed_variance': 0.0
            }
        
        speed_data = df['speed'].fillna(0)
        return {
            'avg_speed': speed_data.mean(),
            'max_speed': speed_data.max(),
            'speed_variance': speed_data.var()
        }