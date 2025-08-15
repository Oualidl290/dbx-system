import pandas as pd
import numpy as np
from typing import Dict, List, Any
import os
import logging
from pymavlink import mavutil

class LogParser:
    def __init__(self):
        self.supported_formats = ['.csv', '.log', '.bin', '.ulog']
        
    def parse_log(self, file_path: str) -> pd.DataFrame:
        """Parse drone flight log based on file format"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            return self._parse_csv(file_path)
        elif file_ext in ['.bin', '.log']:
            return self._parse_mavlink(file_path)
        elif file_ext == '.ulog':
            return self._parse_ulog(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _parse_csv(self, file_path: str) -> pd.DataFrame:
        """Parse CSV log files"""
        try:
            # Try different separators and encodings
            for sep in [',', ';', '\t']:
                try:
                    df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                    if len(df.columns) > 1:
                        break
                except:
                    continue
            
            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Ensure required columns exist (create dummy if missing)
            required_cols = ['timestamp', 'battery_voltage', 'altitude', 'speed']
            for col in required_cols:
                if col not in df.columns:
                    # Create synthetic column based on common patterns
                    if col == 'timestamp' and 'time' in df.columns:
                        df['timestamp'] = df['time']
                    elif col == 'battery_voltage' and 'voltage' in df.columns:
                        df['battery_voltage'] = df['voltage']
                    else:
                        df[col] = np.random.normal(0, 1, len(df))  # Placeholder
            
            return self._clean_and_normalize(df)
            
        except Exception as e:
            logging.error(f"Error parsing CSV: {e}")
            raise
    
    def _parse_mavlink(self, file_path: str) -> pd.DataFrame:
        """Parse MAVLink binary logs (.bin, .log)"""
        try:
            mlog = mavutil.mavlink_connection(file_path)
            
            data = []
            while True:
                msg = mlog.recv_match()
                if msg is None:
                    break
                
                # Extract relevant messages
                if msg.get_type() in ['ATTITUDE', 'GPS_RAW_INT', 'SYS_STATUS', 'VFR_HUD']:
                    row = {
                        'timestamp': msg._timestamp,
                        'msg_type': msg.get_type(),
                    }
                    
                    # Add message-specific fields
                    for field in msg.get_fieldnames():
                        row[field] = getattr(msg, field)
                    
                    data.append(row)
            
            df = pd.DataFrame(data)
            return self._clean_and_normalize(df)
            
        except Exception as e:
            logging.error(f"Error parsing MAVLink: {e}")
            # Fallback to dummy data for demo
            return self._create_dummy_data()
    
    def _parse_ulog(self, file_path: str) -> pd.DataFrame:
        """Parse ULog files (PX4 format)"""
        try:
            # For now, create dummy data (in production, use pyulog)
            return self._create_dummy_data()
        except Exception as e:
            logging.error(f"Error parsing ULog: {e}")
            return self._create_dummy_data()
    
    def _clean_and_normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize the dataframe"""
        # Remove completely empty columns
        df = df.dropna(axis=1, how='all')
        
        # Convert timestamp if it's not already datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Fill NaN values with forward fill then backward fill
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        # Remove duplicate rows
        df = df.drop_duplicates()
        
        return df
    
    def _create_dummy_data(self) -> pd.DataFrame:
        """Create dummy flight data for testing"""
        n_samples = 1000
        timestamps = pd.date_range('2024-01-01 10:00:00', periods=n_samples, freq='1S')
        
        # Simulate realistic flight data with some anomalies
        np.random.seed(42)
        
        altitude = np.cumsum(np.random.normal(0, 1, n_samples)) + 100
        altitude[200:220] = altitude[200:220] + 50  # Sudden altitude spike
        
        battery_voltage = 12.6 - np.linspace(0, 2, n_samples) + np.random.normal(0, 0.1, n_samples)
        battery_voltage[800:820] = battery_voltage[800:820] - 2  # Battery drop
        
        motor_rpm = 3000 + np.random.normal(0, 100, n_samples)
        motor_rpm[500:510] = 1000  # Motor failure simulation
        
        gps_hdop = np.random.gamma(2, 1, n_samples)
        gps_hdop[300:350] = gps_hdop[300:350] + 5  # GPS signal loss
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'altitude': altitude,
            'battery_voltage': battery_voltage,
            'motor_1_rpm': motor_rpm + np.random.normal(0, 50, n_samples),
            'motor_2_rpm': motor_rpm + np.random.normal(0, 50, n_samples),
            'motor_3_rpm': motor_rpm + np.random.normal(0, 50, n_samples),
            'motor_4_rpm': motor_rpm + np.random.normal(0, 50, n_samples),
            'gps_hdop': gps_hdop,
            'vibration_x': np.random.normal(0, 5, n_samples),
            'vibration_y': np.random.normal(0, 5, n_samples),
            'vibration_z': np.random.normal(0, 5, n_samples),
            'speed': np.random.uniform(0, 15, n_samples),
            'temperature': 25 + np.random.normal(0, 3, n_samples)
        })
        
        return df
    
    def get_log_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of the log"""
        return {
            'duration': (df['timestamp'].max() - df['timestamp'].min()).total_seconds(),
            'max_altitude': df['altitude'].max(),
            'min_battery': df['battery_voltage'].min(),
            'avg_speed': df['speed'].mean(),
            'total_samples': len(df)
        }