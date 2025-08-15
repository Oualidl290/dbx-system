import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import pickle
import os
from typing import Tuple, List, Dict, Any
import logging
from .multi_aircraft_detector import MultiAircraftAnomalyDetector

class AnomalyDetector:
    """Legacy interface for backward compatibility - now uses multi-aircraft system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize the new multi-aircraft system
        self.multi_aircraft_detector = MultiAircraftAnomalyDetector()
        
        # Legacy attributes for backward compatibility
        self.feature_columns = [
            'altitude', 'battery_voltage', 'motor_1_rpm', 'motor_2_rpm', 
            'motor_3_rpm', 'motor_4_rpm', 'gps_hdop', 'vibration_x',
            'vibration_y', 'vibration_z', 'vibration_w', 'speed', 'temperature'
        ]
        self.model_path = "data/models/"
        os.makedirs(self.model_path, exist_ok=True)
        
        # Train the multi-aircraft models
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the multi-aircraft detection system"""
        try:
            self.multi_aircraft_detector.train_models()
            self.logger.info("Multi-aircraft anomaly detection system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize multi-aircraft system: {e}")
            # Fallback to legacy single model
            self._load_or_train_legacy_model()
    
    def _load_or_train_legacy_model(self):
        """Load existing legacy model or train a new one (fallback)"""
        model_file = os.path.join(self.model_path, "xgboost_model.pkl")
        scaler_file = os.path.join(self.model_path, "scaler.pkl")
        
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            # Load existing model
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
            self.logger.info("Loaded existing legacy model")
        else:
            # Train new model
            self._train_initial_model()
    
    def _train_initial_model(self):
        """Train initial legacy model (fallback only)"""
        self.logger.info("Training fallback legacy model...")
        
        try:
            from .aircraft_detector import AircraftType
            # Use multi-aircraft detector's multirotor data as fallback
            X_train, y_train = self.multi_aircraft_detector.generate_training_data(AircraftType.MULTIROTOR)
            
            # Initialize scaler if not exists
            if not hasattr(self, 'scaler'):
                self.scaler = StandardScaler()
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            
            # Train XGBoost model
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Save model and scaler
            with open(os.path.join(self.model_path, "xgboost_model.pkl"), 'wb') as f:
                pickle.dump(self.model, f)
            with open(os.path.join(self.model_path, "scaler.pkl"), 'wb') as f:
                pickle.dump(self.scaler, f)
            
            self.logger.info("Fallback legacy model trained and saved")
            
        except Exception as e:
            self.logger.error(f"Failed to train fallback model: {e}")
            # Create minimal fallback
            self.model = None
            self.scaler = StandardScaler()
    
    def predict(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """Predict anomalies in flight log using multi-aircraft system"""
        try:
            # Use the new multi-aircraft system
            analysis_result = self.multi_aircraft_detector.analyze_flight_log(df)
            
            # Extract legacy format results
            risk_score = analysis_result['risk_score']
            anomalies = analysis_result['anomalies']
            
            # Add aircraft type information to anomalies for enhanced context
            for anomaly in anomalies:
                anomaly['aircraft_type'] = analysis_result['aircraft_type']
                anomaly['aircraft_confidence'] = analysis_result['aircraft_confidence']
            
            return risk_score, anomalies
            
        except Exception as e:
            self.logger.error(f"Error in multi-aircraft prediction: {e}")
            # Fallback to legacy prediction if available
            if hasattr(self, 'model') and self.model is not None:
                return self._legacy_predict(df)
            return 0.5, []  # Default moderate risk
    
    def _legacy_predict(self, df: pd.DataFrame) -> Tuple[float, List[Dict]]:
        """Legacy prediction method as fallback"""
        try:
            # Prepare features
            X = self._prepare_features(df)
            X_scaled = self.scaler.transform(X)
            
            # Get predictions
            predictions = self.model.predict_proba(X_scaled)[:, 1]  # Probability of anomaly
            
            # Calculate overall risk score
            risk_score = np.mean(predictions)
            
            # Find specific anomalies
            anomalies = self._find_anomalies(df, predictions)
            
            return risk_score, anomalies
            
        except Exception as e:
            self.logger.error(f"Error in legacy prediction: {e}")
            return 0.5, []  # Default moderate risk
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediction"""
        # Ensure all required columns exist
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0  # Default value
        
        # Select and return feature columns
        return df[self.feature_columns].fillna(0)
    
    def _find_anomalies(self, df: pd.DataFrame, predictions: np.ndarray) -> List[Dict]:
        """Find and describe specific anomalies"""
        anomalies = []
        threshold = 0.7  # Anomaly threshold
        
        anomaly_indices = np.where(predictions > threshold)[0]
        
        for idx in anomaly_indices[:10]:  # Limit to top 10 anomalies
            timestamp = df.iloc[idx]['timestamp'] if 'timestamp' in df.columns else idx
            
            # Find the most unusual feature
            features = self._prepare_features(df.iloc[[idx]])
            feature_values = features.iloc[0]
            
            # Simple anomaly description
            anomaly_desc = self._describe_anomaly(feature_values)
            
            anomalies.append({
                'timestamp': str(timestamp),
                'risk_score': float(predictions[idx]),
                'description': anomaly_desc,
                'features': feature_values.to_dict()
            })
        
        return anomalies
    
    def _describe_anomaly(self, features: pd.Series) -> str:
        """Generate human-readable anomaly description"""
        descriptions = []
        
        if features['battery_voltage'] < 10:
            descriptions.append("Critical battery voltage")
        if features['altitude'] < 0 or features['altitude'] > 400:
            descriptions.append("Extreme altitude")
        if features['motor_1_rpm'] < 1000:
            descriptions.append("Motor failure detected")
        if features['gps_hdop'] > 5:
            descriptions.append("Poor GPS signal")
        if abs(features['vibration_x']) > 8:
            descriptions.append("High vibration levels")
        
        return "; ".join(descriptions) if descriptions else "Anomalous flight behavior"
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names used by the model"""
        return self.feature_columns
    
    def retrain(self, df: pd.DataFrame, labels: np.ndarray):
        """Retrain model with new data"""
        try:
            # Retrain the multi-aircraft system
            self.multi_aircraft_detector.train_models()
            self.logger.info("Multi-aircraft models retrained successfully")
        except Exception as e:
            self.logger.error(f"Failed to retrain multi-aircraft models: {e}")
            # Fallback to legacy retraining
            if hasattr(self, 'model') and self.model is not None:
                X = self._prepare_features(df)
                X_scaled = self.scaler.transform(X)
                self.model.fit(X_scaled, labels)
                with open(os.path.join(self.model_path, "xgboost_model.pkl"), 'wb') as f:
                    pickle.dump(self.model, f)
                self.logger.info("Legacy model retrained successfully")
    
    def get_comprehensive_analysis(self, df: pd.DataFrame) -> Dict:
        """Get comprehensive multi-aircraft analysis (new feature)"""
        try:
            return self.multi_aircraft_detector.analyze_flight_log(df)
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            # Return basic analysis as fallback
            risk_score, anomalies = self.predict(df)
            return {
                'aircraft_type': 'unknown',
                'aircraft_confidence': 0.0,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'anomalies': anomalies,
                'flight_phases': {},
                'performance_metrics': {},
                'total_data_points': len(df),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level"""
        if risk_score > 0.9:
            return "CRITICAL"
        elif risk_score > 0.7:
            return "WARNING"
        elif risk_score > 0.3:
            return "ELEVATED"
        else:
            return "NORMAL"
    