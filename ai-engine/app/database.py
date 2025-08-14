"""
Database connection and models for DBX AI Multi-Aircraft System
Production PostgreSQL integration
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, DECIMAL, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://dbx_api_service:password@localhost:5432/dbx_aviation"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# Database Models
# ============================================

class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "dbx_aviation"}
    
    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_code = Column(String(50), unique=True, nullable=False)
    org_name = Column(String(255), nullable=False)
    org_type = Column(String(50), nullable=False)
    subscription_tier = Column(String(50), default="basic")
    api_key_hash = Column(String(255), nullable=False)
    api_rate_limit = Column(Integer, default=1000)
    storage_quota_gb = Column(Integer, default=100)
    
    # Compliance & Security
    compliance_level = Column(String(50), default="standard")
    data_retention_days = Column(Integer, default=365)
    encryption_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default={})

class AircraftRegistry(Base):
    __tablename__ = "aircraft_registry"
    __table_args__ = {"schema": "dbx_aviation"}
    
    aircraft_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Aircraft Identification
    registration_number = Column(String(20), nullable=False)
    serial_number = Column(String(100))
    call_sign = Column(String(20))
    
    # Aircraft Classification
    aircraft_type = Column(String(50), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    model_year = Column(Integer)
    
    # Technical Specifications
    specifications = Column(JSONB, default={})
    
    # Operational Status
    operational_status = Column(String(50), default="active")
    last_maintenance_date = Column(DateTime)
    next_maintenance_date = Column(DateTime)
    total_flight_hours = Column(DECIMAL(10, 2), default=0)
    total_flight_cycles = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

class FlightSession(Base):
    __tablename__ = "flight_sessions"
    __table_args__ = {"schema": "dbx_aviation"}
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    aircraft_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Session Identification
    flight_number = Column(String(50))
    mission_type = Column(String(50))
    pilot_id = Column(String(100))
    
    # Temporal Data
    scheduled_departure = Column(DateTime(timezone=True))
    actual_departure = Column(DateTime(timezone=True))
    scheduled_arrival = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    flight_duration_seconds = Column(Integer)
    
    # Geospatial Data
    departure_latitude = Column(DECIMAL(10, 8))
    departure_longitude = Column(DECIMAL(11, 8))
    arrival_latitude = Column(DECIMAL(10, 8))
    arrival_longitude = Column(DECIMAL(11, 8))
    max_altitude_m = Column(DECIMAL(10, 2))
    total_distance_km = Column(DECIMAL(10, 2))
    
    # Flight Conditions
    weather_conditions = Column(JSONB)
    visibility_m = Column(Integer)
    wind_speed_ms = Column(DECIMAL(5, 2))
    temperature_celsius = Column(DECIMAL(5, 2))
    
    # Session Status
    session_status = Column(String(50), default="scheduled")
    data_quality_score = Column(DECIMAL(3, 2))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    uploaded_at = Column(DateTime(timezone=True))
    processed_at = Column(DateTime(timezone=True))

class FlightTelemetry(Base):
    __tablename__ = "flight_telemetry"
    __table_args__ = {"schema": "dbx_aviation"}
    
    telemetry_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Core Telemetry Data
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    altitude_m = Column(DECIMAL(10, 2))
    heading_degrees = Column(DECIMAL(5, 2))
    
    # Motion Data
    airspeed_ms = Column(DECIMAL(6, 2))
    groundspeed_ms = Column(DECIMAL(6, 2))
    vertical_speed_ms = Column(DECIMAL(6, 2))
    
    # Attitude
    pitch_degrees = Column(DECIMAL(5, 2))
    roll_degrees = Column(DECIMAL(5, 2))
    yaw_degrees = Column(DECIMAL(5, 2))
    
    # Motor/Engine Data
    motor_rpm = Column(ARRAY(DECIMAL))
    motor_temperature = Column(ARRAY(DECIMAL))
    motor_current = Column(ARRAY(DECIMAL))
    throttle_percent = Column(DECIMAL(5, 2))
    
    # Control Surfaces
    elevator_position = Column(DECIMAL(5, 2))
    aileron_position = Column(DECIMAL(5, 2))
    rudder_position = Column(DECIMAL(5, 2))
    flaps_position = Column(DECIMAL(5, 2))
    
    # Vibration Data
    vibration_x = Column(DECIMAL(6, 3))
    vibration_y = Column(DECIMAL(6, 3))
    vibration_z = Column(DECIMAL(6, 3))
    
    # System Health
    battery_voltage = Column(DECIMAL(5, 2))
    battery_current = Column(DECIMAL(6, 2))
    battery_remaining_percent = Column(DECIMAL(5, 2))
    system_warnings = Column(JSONB, default=[])
    
    # Raw sensor data
    raw_sensor_data = Column(JSONB)

class MLAnalysisResult(Base):
    __tablename__ = "ml_analysis_results"
    __table_args__ = {"schema": "dbx_aviation"}
    
    analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Model Information
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_time_ms = Column(Integer)
    
    # Aircraft Detection Results
    detected_aircraft_type = Column(String(50))
    aircraft_confidence = Column(DECIMAL(5, 4))
    aircraft_probabilities = Column(JSONB)
    
    # Anomaly Detection Results
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(DECIMAL(5, 4))
    anomaly_threshold = Column(DECIMAL(5, 4))
    anomalies = Column(JSONB, default=[])
    
    # Risk Assessment
    risk_score = Column(DECIMAL(5, 4))
    risk_level = Column(String(20))
    risk_factors = Column(JSONB, default=[])
    
    # SHAP Explainability
    shap_values = Column(JSONB)
    feature_importance = Column(JSONB)
    top_features = Column(JSONB)
    
    # Flight Phases Analysis
    flight_phases = Column(JSONB)
    
    # Performance Metrics
    performance_metrics = Column(JSONB)
    
    # AI Report
    ai_report_generated = Column(Boolean, default=False)
    ai_report_content = Column(Text)
    ai_report_summary = Column(Text)
    ai_recommendations = Column(JSONB, default=[])
    
    # Quality Metrics
    data_completeness = Column(DECIMAL(5, 4))
    confidence_score = Column(DECIMAL(5, 4))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    review_notes = Column(Text)

class APIRequest(Base):
    __tablename__ = "api_requests"
    __table_args__ = {"schema": "dbx_aviation"}
    
    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Request Details
    endpoint = Column(String(255), nullable=False)
    http_method = Column(String(10), nullable=False)
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Response
    response_status_code = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Payload Size
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    
    # Analysis Details
    session_id = Column(UUID(as_uuid=True))
    analysis_id = Column(UUID(as_uuid=True))
    
    # Rate Limiting
    rate_limit_remaining = Column(Integer)
    
    # Metadata
    ip_address = Column(INET)
    user_agent = Column(Text)
    api_version = Column(String(20))
    
    # Error Tracking
    error_occurred = Column(Boolean, default=False)
    error_message = Column(Text)

# ============================================
# Database Utilities
# ============================================

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_organization_by_api_key(db: Session, api_key_hash: str) -> Optional[Organization]:
    """Get organization by API key hash"""
    return db.query(Organization).filter(
        Organization.api_key_hash == api_key_hash,
        Organization.is_active == True
    ).first()

def create_flight_session(
    db: Session, 
    org_id: uuid.UUID, 
    aircraft_id: uuid.UUID,
    flight_data: Dict[str, Any]
) -> FlightSession:
    """Create a new flight session"""
    session = FlightSession(
        org_id=org_id,
        aircraft_id=aircraft_id,
        **flight_data
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def save_analysis_result(
    db: Session,
    session_id: uuid.UUID,
    org_id: uuid.UUID,
    analysis_data: Dict[str, Any]
) -> MLAnalysisResult:
    """Save ML analysis result"""
    result = MLAnalysisResult(
        session_id=session_id,
        org_id=org_id,
        **analysis_data
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def log_api_request(
    db: Session,
    org_id: uuid.UUID,
    request_data: Dict[str, Any]
) -> APIRequest:
    """Log API request for monitoring"""
    request = APIRequest(
        org_id=org_id,
        **request_data
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

# ============================================
# Connection Testing
# ============================================

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        result = db.execute("SELECT 1").fetchone()
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_info():
    """Get database information"""
    try:
        db = SessionLocal()
        
        # Get PostgreSQL version
        version_result = db.execute("SELECT version()").fetchone()
        
        # Get schema info
        schema_result = db.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit')
            ORDER BY schemaname, tablename
        """).fetchall()
        
        db.close()
        
        return {
            "version": version_result[0] if version_result else "Unknown",
            "tables": [{"schema": row[0], "table": row[1]} for row in schema_result]
        }
        
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return None

if __name__ == "__main__":
    # Test the database connection
    print("Testing database connection...")
    if test_connection():
        print("✅ Database connection successful!")
        
        info = get_database_info()
        if info:
            print(f"📊 Database version: {info['version']}")
            print(f"📋 Found {len(info['tables'])} tables:")
            for table in info['tables']:
                print(f"   - {table['schema']}.{table['table']}")
    else:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running and credentials are correct.")