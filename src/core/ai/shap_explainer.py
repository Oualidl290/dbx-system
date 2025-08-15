import shap
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from .aircraft_detector import AircraftType

class SHAPExplainer:
    def __init__(self):
        self.explainers = {}  # Store explainers for each aircraft type
        
    def explain(self, df: pd.DataFrame, model, aircraft_type: AircraftType = None, feature_columns: List[str] = None) -> Dict[str, Any]:
        """Generate SHAP explanations for the prediction with aircraft-specific features"""
        try:
            # Use provided feature columns or default multirotor features
            if feature_columns is None:
                feature_columns = self._get_feature_columns(aircraft_type)
            
            # Ensure all columns exist
            for col in feature_columns:
                if col not in df.columns:
                    df[col] = 0
            
            X = df[feature_columns].fillna(0)
            
            # Take sample for SHAP (SHAP can be slow on large datasets)
            sample_size = min(100, len(X))
            X_sample = X.sample(n=sample_size, random_state=42) if len(X) > 1 else X
            
            # Create aircraft-specific explainer
            explainer_key = aircraft_type.value if aircraft_type else 'default'
            if explainer_key not in self.explainers:
                self.explainers[explainer_key] = shap.TreeExplainer(model)
            
            explainer = self.explainers[explainer_key]
            
            # Get SHAP values
            shap_values = explainer.shap_values(X_sample)
            
            # If binary classification, take positive class
            if len(shap_values.shape) == 3:
                shap_values = shap_values[:, :, 1]
            
            # Calculate feature importance
            feature_importance = np.abs(shap_values).mean(axis=0)
            
            # Get top contributing features
            top_features = []
            feature_indices = np.argsort(feature_importance)[::-1][:5]  # Top 5
            
            for idx in feature_indices:
                if idx < len(feature_columns):
                    feature_name = feature_columns[idx]
                    importance = float(feature_importance[idx])
                    avg_value = float(X_sample.iloc[:, idx].mean())
                    
                    top_features.append({
                        'feature': feature_name,
                        'importance': importance,
                        'average_value': avg_value,
                        'impact': 'positive' if importance > 0 else 'negative',
                        'aircraft_specific': aircraft_type.value if aircraft_type else 'unknown'
                    })
            
            return {
                'top_features': top_features,
                'overall_impact': float(np.sum(feature_importance)),
                'sample_size': len(X_sample),
                'aircraft_type': aircraft_type.value if aircraft_type else 'unknown',
                'explanation': self._generate_aircraft_explanation(top_features, aircraft_type)
            }
            
        except Exception as e:
            logging.error(f"Error in SHAP explanation: {e}")
            return {
                'top_features': [],
                'overall_impact': 0.0,
                'sample_size': 0,
                'aircraft_type': aircraft_type.value if aircraft_type else 'unknown',
                'explanation': "Unable to generate explanation"
            }
    
    def _get_feature_columns(self, aircraft_type: AircraftType) -> List[str]:
        """Get feature columns based on aircraft type"""
        if aircraft_type == AircraftType.FIXED_WING:
            return [
                'altitude', 'battery_voltage', 'motor_rpm', 'airspeed',
                'ground_speed', 'throttle_position', 'elevator_position',
                'rudder_position', 'aileron_position', 'pitch_angle',
                'roll_angle', 'yaw_rate', 'gps_hdop', 'temperature',
                'wind_speed', 'angle_of_attack'
            ]
        elif aircraft_type == AircraftType.MULTIROTOR:
            return [
                'altitude', 'battery_voltage', 'motor_1_rpm', 'motor_2_rpm',
                'motor_3_rpm', 'motor_4_rpm', 'vibration_x', 'vibration_y',
                'vibration_z', 'vibration_w', 'pitch_angle', 'roll_angle',
                'speed', 'temperature', 'gps_hdop'
            ]
        elif aircraft_type == AircraftType.VTOL:
            return [
                'altitude', 'battery_voltage', 'motor_1_rpm', 'motor_2_rpm',
                'motor_3_rpm', 'motor_4_rpm', 'motor_5_rpm', 'airspeed',
                'elevator_position', 'aileron_position', 'gps_hdop',
                'vibration_x', 'vibration_y', 'vibration_z', 'vibration_w',
                'temperature', 'transition_mode', 'pitch_angle', 'roll_angle'
            ]
        else:
            # Default to multirotor features
            return [
                'altitude', 'battery_voltage', 'motor_1_rpm', 'motor_2_rpm', 
                'motor_3_rpm', 'motor_4_rpm', 'gps_hdop', 'vibration_x',
                'vibration_y', 'vibration_z', 'vibration_w', 'speed', 'temperature'
            ]
    
    def _generate_explanation(self, top_features: List[Dict]) -> str:
        """Generate human-readable explanation from SHAP values (legacy)"""
        return self._generate_aircraft_explanation(top_features, None)
    
    def _generate_aircraft_explanation(self, top_features: List[Dict], aircraft_type: AircraftType) -> str:
        """Generate aircraft-specific human-readable explanation from SHAP values"""
        if not top_features:
            return "No significant features found"
        
        explanations = []
        aircraft_context = f" for {aircraft_type.value}" if aircraft_type else ""
        
        for feature in top_features[:3]:  # Top 3 features
            name = feature['feature'].replace('_', ' ').title()
            importance = feature['importance']
            
            # Aircraft-specific interpretations
            if aircraft_type == AircraftType.FIXED_WING:
                if 'airspeed' in feature['feature'].lower():
                    explanations.append(f"Airspeed variations significantly impact flight safety")
                elif 'motor' in feature['feature'].lower() or 'engine' in feature['feature'].lower():
                    explanations.append(f"Engine performance is a critical factor")
                elif 'elevator' in feature['feature'].lower() or 'aileron' in feature['feature'].lower():
                    explanations.append(f"Control surface deflections indicate flight dynamics issues")
                elif importance > 0.1:
                    explanations.append(f"{name} shows significant impact on fixed-wing performance")
                    
            elif aircraft_type == AircraftType.MULTIROTOR:
                if 'motor' in feature['feature'].lower():
                    explanations.append(f"Motor performance asymmetry detected")
                elif 'vibration' in feature['feature'].lower():
                    explanations.append(f"Vibration levels indicate mechanical issues")
                elif 'pitch' in feature['feature'].lower() or 'roll' in feature['feature'].lower():
                    explanations.append(f"Attitude control instability detected")
                elif importance > 0.1:
                    explanations.append(f"{name} shows significant impact on multirotor stability")
                    
            elif aircraft_type == AircraftType.VTOL:
                if 'transition' in feature['feature'].lower():
                    explanations.append(f"Transition mode operations affecting flight safety")
                elif 'motor_5' in feature['feature'].lower():
                    explanations.append(f"Forward propulsion system performance critical")
                elif importance > 0.1:
                    explanations.append(f"{name} significantly impacts VTOL operations")
                    
            else:
                if importance > 0.1:
                    explanations.append(f"{name} shows significant impact")
                elif importance > 0.05:
                    explanations.append(f"{name} shows moderate impact")
        
        if explanations:
            return f"Key factors{aircraft_context}: " + ", ".join(explanations)
        else:
            return f"Low overall feature impact detected{aircraft_context}"