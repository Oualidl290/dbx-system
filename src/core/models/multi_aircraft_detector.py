import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import logging
from .aircraft_detector import AircraftType, AircraftTypeDetector

class MultiAircraftAnomalyDetector:
    """Multi-aircraft anomaly detection system with specialized models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.aircraft_detector = AircraftTypeDetector()
        self.models = {}
        self.scalers = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize specialized models for each aircraft type"""
        for aircraft_type in (AircraftType.FIXED_WING, AircraftType.MULTIROTOR, AircraftType.VTOL):
            self.models[aircraft_type] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            self.scalers[aircraft_type] = StandardScaler()
    
    def get_feature_set(self, aircraft_type: AircraftType) -> List[str]:
        """Return feature set for specific aircraft type"""
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
            return self.get_feature_set(AircraftType.MULTIROTOR)
    
    def generate_training_data(self, aircraft_type: AircraftType, n_samples: int = 10000) -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate aircraft-specific training data"""
        n_normal = int(n_samples * 0.8)
        n_anomaly = n_samples - n_normal
        
        if aircraft_type == AircraftType.FIXED_WING:
            normal_data = {
                'altitude': np.random.uniform(50, 500, n_normal),
                'battery_voltage': np.random.normal(11.1, 0.2, n_normal),
                'motor_rpm': np.random.normal(5000, 300, n_normal),
                'airspeed': np.random.normal(25, 3, n_normal),
                'ground_speed': np.random.normal(23, 4, n_normal),
                'throttle_position': np.random.normal(75, 10, n_normal),
                'elevator_position': np.random.normal(0, 2, n_normal),
                'rudder_position': np.random.normal(0, 2, n_normal),
                'aileron_position': np.random.normal(0, 3, n_normal),
                'pitch_angle': np.random.normal(5, 3, n_normal),
                'roll_angle': np.random.normal(0, 5, n_normal),
                'yaw_rate': np.random.normal(0, 2, n_normal),
                'gps_hdop': np.random.gamma(2, 0.5, n_normal),
                'temperature': np.random.normal(25, 8, n_normal),
                'wind_speed': np.random.gamma(2, 2, n_normal),
                'angle_of_attack': np.random.normal(5, 2, n_normal)
            }
            
            anomaly_data = {
                'altitude': np.concatenate([
                    np.random.uniform(-10, 5, n_anomaly//4),
                    np.random.uniform(600, 1000, n_anomaly//4),
                    np.random.normal(100, 50, n_anomaly - 2*(n_anomaly//4))
                ]),
                'battery_voltage': np.concatenate([
                    np.random.uniform(8, 10, n_anomaly//2),
                    np.random.uniform(13, 15, n_anomaly - n_anomaly//2)
                ]),
                'motor_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//3),
                    np.random.uniform(8000, 12000, n_anomaly//3),
                    np.random.normal(5000, 1000, n_anomaly - 2*(n_anomaly//3))
                ]),
                'airspeed': np.concatenate([
                    np.random.uniform(0, 12, n_anomaly//3),
                    np.random.uniform(50, 80, n_anomaly//3),
                    np.random.normal(25, 10, n_anomaly - 2*(n_anomaly//3))
                ]),
                'ground_speed': np.random.normal(23, 8, n_anomaly),
                'throttle_position': np.random.uniform(0, 100, n_anomaly),
                'elevator_position': np.random.uniform(-30, 30, n_anomaly),
                'rudder_position': np.random.uniform(-30, 30, n_anomaly),
                'aileron_position': np.random.uniform(-30, 30, n_anomaly),
                'pitch_angle': np.random.uniform(-30, 30, n_anomaly),
                'roll_angle': np.random.uniform(-45, 45, n_anomaly),
                'yaw_rate': np.random.uniform(-20, 20, n_anomaly),
                'gps_hdop': np.random.gamma(5, 1, n_anomaly),
                'temperature': np.random.normal(35, 10, n_anomaly),
                'wind_speed': np.random.gamma(5, 3, n_anomaly),
                'angle_of_attack': np.random.uniform(15, 45, n_anomaly)
            }
            
        elif aircraft_type == AircraftType.MULTIROTOR:
            base_rpm = 3000
            normal_data = {
                'altitude': np.random.uniform(5, 120, n_normal),
                'battery_voltage': np.random.normal(11.1, 0.2, n_normal),
                'motor_1_rpm': np.random.normal(base_rpm, 200, n_normal),
                'motor_2_rpm': np.random.normal(base_rpm, 200, n_normal),
                'motor_3_rpm': np.random.normal(base_rpm, 200, n_normal),
                'motor_4_rpm': np.random.normal(base_rpm, 200, n_normal),
                'vibration_x': np.random.normal(0, 2, n_normal),
                'vibration_y': np.random.normal(0, 2, n_normal),
                'vibration_z': np.random.normal(0, 2, n_normal),
                'vibration_w': np.random.normal(0, 2, n_normal),
                'pitch_angle': np.random.normal(0, 10, n_normal),
                'roll_angle': np.random.normal(0, 10, n_normal),
                'speed': np.random.uniform(0, 12, n_normal),
                'temperature': np.random.normal(25, 5, n_normal),
                'gps_hdop': np.random.gamma(2, 1, n_normal)
            }
            
            anomaly_data = {
                'altitude': np.random.uniform(0, 150, n_anomaly),
                'battery_voltage': np.concatenate([
                    np.random.uniform(9, 10.5, n_anomaly//2),
                    np.random.uniform(12.5, 14, n_anomaly - n_anomaly//2)
                ]),
                'motor_1_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//4),
                    np.random.uniform(5500, 8000, n_anomaly//4),
                    np.random.normal(base_rpm, 1000, n_anomaly - 2*(n_anomaly//4))
                ]),
                'motor_2_rpm': np.random.normal(base_rpm, 1500, n_anomaly),
                'motor_3_rpm': np.random.normal(base_rpm, 1500, n_anomaly),
                'motor_4_rpm': np.random.normal(base_rpm, 1500, n_anomaly),
                'vibration_x': np.random.normal(0, 12, n_anomaly),
                'vibration_y': np.random.normal(0, 12, n_anomaly),
                'vibration_z': np.random.normal(0, 12, n_anomaly),
                'vibration_w': np.random.normal(0, 12, n_anomaly),
                'pitch_angle': np.random.uniform(-45, 45, n_anomaly),
                'roll_angle': np.random.uniform(-45, 45, n_anomaly),
                'speed': np.random.uniform(0, 30, n_anomaly),
                'temperature': np.concatenate([
                    np.random.uniform(-10, 5, n_anomaly//2),
                    np.random.uniform(40, 60, n_anomaly - n_anomaly//2)
                ]),
                'gps_hdop': np.random.uniform(5, 20, n_anomaly)
            }
            
        else:  # VTOL
            normal_data = {
                'altitude': np.random.uniform(10, 300, n_normal),
                'battery_voltage': np.random.normal(22, 0.8, n_normal),
                'motor_1_rpm': np.random.normal(3000, 200, n_normal),
                'motor_2_rpm': np.random.normal(3000, 200, n_normal),
                'motor_3_rpm': np.random.normal(3000, 200, n_normal),
                'motor_4_rpm': np.random.normal(3000, 200, n_normal),
                'motor_5_rpm': np.random.normal(5000, 300, n_normal),
                'airspeed': np.random.normal(15, 5, n_normal),
                'elevator_position': np.random.normal(0, 2, n_normal),
                'aileron_position': np.random.normal(0, 3, n_normal),
                'gps_hdop': np.random.gamma(2, 0.5, n_normal),
                'vibration_x': np.random.normal(0, 2, n_normal),
                'vibration_y': np.random.normal(0, 2, n_normal),
                'vibration_z': np.random.normal(0, 2, n_normal),
                'vibration_w': np.random.normal(0, 2, n_normal),
                'temperature': np.random.normal(25, 8, n_normal),
                'transition_mode': np.random.choice([0, 1], n_normal, p=[0.8, 0.2]),
                'pitch_angle': np.random.normal(0, 8, n_normal),
                'roll_angle': np.random.normal(0, 8, n_normal)
            }
            
            anomaly_data = {
                'altitude': np.random.uniform(0, 400, n_anomaly),
                'battery_voltage': np.concatenate([
                    np.random.uniform(18, 20, n_anomaly//2),
                    np.random.uniform(26, 28, n_anomaly - n_anomaly//2)
                ]),
                'motor_1_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//5),
                    np.random.normal(3000, 1000, n_anomaly - n_anomaly//5)
                ]),
                'motor_2_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//5),
                    np.random.normal(3000, 1000, n_anomaly - n_anomaly//5)
                ]),
                'motor_3_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//5),
                    np.random.normal(3000, 1000, n_anomaly - n_anomaly//5)
                ]),
                'motor_4_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//5),
                    np.random.normal(3000, 1000, n_anomaly - n_anomaly//5)
                ]),
                'motor_5_rpm': np.concatenate([
                    np.random.uniform(0, 1000, n_anomaly//5),
                    np.random.normal(5000, 1000, n_anomaly - n_anomaly//5)
                ]),
                'airspeed': np.concatenate([
                    np.random.uniform(0, 8, n_anomaly//3),
                    np.random.uniform(35, 50, n_anomaly//3),
                    np.random.normal(15, 10, n_anomaly - 2*(n_anomaly//3))
                ]),
                'elevator_position': np.random.uniform(-25, 25, n_anomaly),
                'aileron_position': np.random.uniform(-25, 25, n_anomaly),
                'gps_hdop': np.random.gamma(5, 1, n_anomaly),
                'vibration_x': np.random.normal(0, 15, n_anomaly),
                'vibration_y': np.random.normal(0, 15, n_anomaly),
                'vibration_z': np.random.normal(0, 15, n_anomaly),
                'vibration_w': np.random.normal(0, 15, n_anomaly),
                'temperature': np.random.normal(35, 10, n_anomaly),
                'transition_mode': np.random.choice([0, 1], n_anomaly, p=[0.5, 0.5]),
                'pitch_angle': np.random.uniform(-30, 30, n_anomaly),
                'roll_angle': np.random.uniform(-30, 30, n_anomaly)
            }
        
        # Combine data
        all_data = {}
        for col in normal_data.keys():
            normal_vals = normal_data[col]
            anomaly_vals = anomaly_data.get(col, np.zeros(n_anomaly))
            all_data[col] = np.concatenate([normal_vals, anomaly_vals])
        
        df = pd.DataFrame(all_data)
        labels = np.concatenate([np.zeros(n_normal), np.ones(n_anomaly)])
        
        return df, labels
    
    def train_models(self):
        """Train all aircraft-specific models"""
        for aircraft_type in (AircraftType.FIXED_WING, AircraftType.MULTIROTOR, AircraftType.VTOL):
            X, y = self.generate_training_data(aircraft_type)
            X_scaled = self.scalers[aircraft_type].fit_transform(X)
            self.models[aircraft_type].fit(X_scaled, y)
            self.logger.info(f"{aircraft_type.value} model training completed")
    
    def analyze_flight_log(self, df: pd.DataFrame) -> Dict:
        """Comprehensive flight log analysis with aircraft type detection"""
        try:
            # Detect aircraft type
            detected_type, confidence = self.aircraft_detector.detect_aircraft_type(df)
            
            # Get appropriate feature set
            feature_cols = self.get_feature_set(detected_type)
            
            # Prepare features
            X = self._prepare_features(df, feature_cols)
            
            # Get appropriate model and scaler
            model = self.models.get(detected_type, self.models[AircraftType.MULTIROTOR])
            scaler = self.scalers.get(detected_type, self.scalers[AircraftType.MULTIROTOR])
            
            # Make predictions
            X_scaled = scaler.transform(X)
            predictions = model.predict_proba(X_scaled)[:, 1]
            risk_score = np.mean(predictions)
            
            # Find aircraft-specific anomalies
            anomalies = self._find_aircraft_specific_anomalies(df, predictions, detected_type)
            
            # Analyze flight phases
            flight_phases = self._analyze_flight_phases(df, detected_type)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(df, detected_type)
            
            return {
                'aircraft_type': detected_type.value,
                'aircraft_confidence': confidence,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'anomalies': anomalies,
                'flight_phases': flight_phases,
                'performance_metrics': performance_metrics,
                'total_data_points': len(df),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Flight log analysis failed: {e}")
            raise
    
    def _prepare_features(self, df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
        """Prepare features for analysis"""
        X = pd.DataFrame()
        for col in feature_cols:
            if col in df.columns:
                X[col] = df[col].fillna(0)
            else:
                X[col] = 0
        return X
    
    def _find_aircraft_specific_anomalies(self, df: pd.DataFrame, predictions: np.ndarray, aircraft_type: AircraftType) -> List[Dict]:
        """Find anomalies specific to aircraft type"""
        threshold = 0.7
        anomaly_indices = np.where(predictions > threshold)[0]
        anomalies = []
        
        for idx in anomaly_indices:
            row = df.iloc[idx]
            
            description = (
                self._describe_fixed_wing_anomaly(row) if aircraft_type == AircraftType.FIXED_WING else
                self._describe_multirotor_anomaly(row) if aircraft_type == AircraftType.MULTIROTOR else
                self._describe_vtol_anomaly(row) if aircraft_type == AircraftType.VTOL else
                "Anomaly detected - unknown aircraft type"
            )
            
            anomalies.append({
                'timestamp': str(row.get('timestamp', df.index[idx])),
                'risk_score': float(predictions[idx]),
                'severity': 'CRITICAL' if predictions[idx] > 0.9 else 'WARNING',
                'description': description,
                'aircraft_specific': True
            })
        
        return anomalies
    
    def _describe_fixed_wing_anomaly(self, row: pd.Series) -> str:
        """Generate fixed-wing specific anomaly descriptions"""
        issues = []
        
        airspeed = row.get('airspeed', 0)
        if airspeed < 12:  # FIXED_WING_STALL_SPEED
            issues.append("CRITICAL: Airspeed below stall speed")
        elif airspeed > 45:  # FIXED_WING_MAX_AIRSPEED
            issues.append("WARNING: Airspeed exceeds safe limits")
        
        motor_rpm = row.get('motor_rpm', 0)
        if motor_rpm < 1000:
            issues.append("CRITICAL: Engine failure or shutdown")
        elif motor_rpm > 8000:
            issues.append("WARNING: Engine overspeed")
        
        elevator = abs(row.get('elevator_position', 0))
        if elevator > 25:
            issues.append("WARNING: Extreme elevator deflection")
        
        aoa = row.get('angle_of_attack', 0)
        if aoa > 20:
            issues.append("CRITICAL: High angle of attack - stall risk")
        
        battery = row.get('battery_voltage', 12)
        if battery < 10:
            issues.append("CRITICAL: Battery voltage critically low")
        
        return ", ".join(issues) if issues else "Flight parameter anomaly detected"
    
    def _describe_multirotor_anomaly(self, row: pd.Series) -> str:
        """Generate multirotor specific anomaly descriptions"""
        issues = []
        
        motors = [row.get(f'motor_{i}_rpm', 0) for i in range(1, 7)]
        active_motors = [m for m in motors if m > 500]
        
        if len(active_motors) < 4:
            issues.append("CRITICAL: Insufficient motors operational")
        
        if len(active_motors) >= 4:
            motor_std = np.std(active_motors)
            if motor_std > 1000:  # MULTIROTOR_MOTOR_ASYMMETRY_THRESHOLD
                issues.append("WARNING: Severe motor RPM asymmetry")
        
        pitch = abs(row.get('pitch_angle', 0))
        roll = abs(row.get('roll_angle', 0))
        if pitch > 30 or roll > 30:  # MULTIROTOR_MAX_TILT_ANGLE
            issues.append("WARNING: Extreme aircraft attitude")
        
        vib_x = row.get('vibration_x', 0)
        vib_y = row.get('vibration_y', 0)
        vib_z = row.get('vibration_z', 0)
        vib_w = row.get('vibration_w', 0)
        total_vib = np.sqrt(vib_x**2 + vib_y**2 + vib_z**2 + vib_w**2)
        if total_vib > 10:  # MULTIROTOR_VIBRATION_THRESHOLD
            issues.append("WARNING: Excessive vibration detected")
        
        battery = row.get('battery_voltage', 12)
        if battery < 10.5:
            issues.append("CRITICAL: Battery voltage critically low")
        
        return ", ".join(issues) if issues else "Flight parameter anomaly detected"
    
    def _describe_vtol_anomaly(self, row: pd.Series) -> str:
        """Generate VTOL specific anomaly descriptions"""
        issues = []
        
        lift_motors = [row.get(f'motor_{i}_rpm', 0) for i in range(1, 5)]
        active_lift = [m for m in lift_motors if m > 500]
        
        if len(active_lift) < 4:
            issues.append("CRITICAL: Lift motor failure - vertical flight compromised")
        
        forward_motor = row.get('motor_5_rpm', 0)
        airspeed = row.get('airspeed', 0)
        
        if airspeed > 15 and forward_motor < 1000:
            issues.append("CRITICAL: Forward motor failure during cruise flight")
        
        transition_mode = row.get('transition_mode', 0)
        if transition_mode == 1:
            if airspeed < 8 or airspeed > 35:
                issues.append("WARNING: Unsafe transition airspeed")
        
        return ", ".join(issues) if issues else "Flight parameter anomaly detected"
    
    def _analyze_flight_phases(self, df: pd.DataFrame, aircraft_type: AircraftType) -> Dict:
        """Analyze flight phases based on aircraft type"""
        if aircraft_type == AircraftType.FIXED_WING:
            return self._analyze_fixed_wing_phases(df)
        elif aircraft_type == AircraftType.MULTIROTOR:
            return self._analyze_multirotor_phases(df)
        elif aircraft_type == AircraftType.VTOL:
            return self._analyze_vtol_phases(df)
        else:
            return {}
    
    def _analyze_fixed_wing_phases(self, df: pd.DataFrame) -> Dict:
        """Analyze fixed-wing flight phases"""
        if len(df) == 0:
            return {}
        
        time_factor = 0.1
        takeoff_duration = cruise_duration = approach_duration = 0
        
        if 'altitude' in df.columns and 'airspeed' in df.columns:
            takeoff_mask = (df['altitude'].diff() > 1) & (df['airspeed'] > 15)
            takeoff_duration = len(df[takeoff_mask]) * time_factor
            
            cruise_mask = (df['altitude'].rolling(20).std() < 3) & (df['airspeed'] > 20)
            cruise_duration = len(df[cruise_mask]) * time_factor
            
            approach_mask = (df['altitude'].diff() < -1) & (df['airspeed'] < 30)
            approach_duration = len(df[approach_mask]) * time_factor
        
        return {
            'takeoff_duration': f"{takeoff_duration:.1f} seconds",
            'cruise_duration': f"{cruise_duration/60:.1f} minutes",
            'approach_duration': f"{approach_duration:.1f} seconds",
            'total_flight_time': f"{len(df)*time_factor/60:.1f} minutes"
        }
    
    def _analyze_multirotor_phases(self, df: pd.DataFrame) -> Dict:
        """Analyze multirotor flight phases"""
        if len(df) == 0:
            return {}
        
        time_factor = 0.1
        hover_time = forward_time = aggressive_time = 0
        
        if 'speed' in df.columns and 'altitude' in df.columns:
            hover_mask = (df['speed'] < 2) & (df['altitude'].diff().abs() < 2)
            hover_time = len(df[hover_mask]) * time_factor
            
            forward_mask = df['speed'] > 5
            forward_time = len(df[forward_mask]) * time_factor
            
            if 'pitch_angle' in df.columns and 'roll_angle' in df.columns:
                aggressive_mask = (abs(df['pitch_angle']) > 15) | (abs(df['roll_angle']) > 15)
                aggressive_time = len(df[aggressive_mask]) * time_factor
        
        return {
            'hover_time': f"{hover_time:.1f} seconds",
            'forward_flight_time': f"{forward_time:.1f} seconds",
            'aggressive_maneuvers': f"{aggressive_time:.1f} seconds",
            'total_flight_time': f"{len(df)*time_factor/60:.1f} minutes"
        }
    
    def _analyze_vtol_phases(self, df: pd.DataFrame) -> Dict:
        """Analyze VTOL flight phases"""
        phases = self._analyze_multirotor_phases(df)
        
        if 'transition_mode' in df.columns:
            transition_mask = df['transition_mode'] == 1
            transition_time = len(df[transition_mask]) * 0.1
            phases['transition_time'] = f"{transition_time:.1f} seconds"
        
        return phases
    
    def _calculate_performance_metrics(self, df: pd.DataFrame, aircraft_type: AircraftType) -> Dict:
        """Calculate performance metrics specific to aircraft type"""
        metrics = {}
        
        if aircraft_type == AircraftType.FIXED_WING:
            if 'airspeed' in df.columns:
                metrics['average_airspeed'] = f"{df['airspeed'].mean():.1f} m/s"
                metrics['max_airspeed'] = f"{df['airspeed'].max():.1f} m/s"
            
            if 'motor_rpm' in df.columns:
                metrics['engine_performance'] = "Normal" if df['motor_rpm'].mean() > 1000 else "Below Normal"
            
            if 'throttle_position' in df.columns:
                metrics['average_throttle'] = f"{df['throttle_position'].mean():.1f}%"
            
            if 'battery_voltage' in df.columns and len(df) > 1:
                metrics['battery_consumption'] = f"{df['battery_voltage'].iloc[0] - df['battery_voltage'].iloc[-1]:.2f}V"
        
        elif aircraft_type == AircraftType.MULTIROTOR:
            motor_cols = [col for col in df.columns if 'motor' in col.lower() and 'rpm' in col.lower()]
            if motor_cols:
                motor_means = [df[col].mean() for col in motor_cols]
                metrics['motor_symmetry'] = f"{np.std(motor_means):.1f} RPM"
            
            if 'battery_voltage' in df.columns and len(df) > 1:
                metrics['battery_consumption'] = f"{df['battery_voltage'].iloc[0] - df['battery_voltage'].iloc[-1]:.2f}V"
            
            vib_cols = ['vibration_x', 'vibration_y', 'vibration_z', 'vibration_w']
            if all(col in df.columns for col in vib_cols):
                avg_vib = np.mean([df[col].abs().mean() for col in vib_cols])
                metrics['average_vibration'] = f"{avg_vib:.1f}"
        
        elif aircraft_type == AircraftType.VTOL:
            # Combine multirotor metrics
            metrics.update(self._calculate_performance_metrics(df, AircraftType.MULTIROTOR))
            
            if 'transition_mode' in df.columns:
                transition_time = len(df[df['transition_mode'] == 1]) * 0.1
                metrics['transition_efficiency'] = f"{transition_time:.1f} seconds"
        
        return metrics
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        if risk_score > 0.9:
            return "CRITICAL"
        elif risk_score > 0.7:
            return "WARNING"
        elif risk_score > 0.3:
            return "ELEVATED"
        else:
            return "NORMAL"