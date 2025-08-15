"""
Enhanced Database Integration for DBX AI Engine
Production-ready database integration with all enhanced features
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager:
    """Enhanced database manager with all new features"""
    
    def __init__(self):
        # Get database URL from environment (updated to use app user)
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://dbx_app_user:dbx_secure_2025@localhost:5432/dbx_aviation'
        )
        
        # Create engine with enhanced connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=20,  # Increased for production
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour for production
            echo=False
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Direct connection for advanced features
        self.connection_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "dbx_aviation"),
            "user": os.getenv("DB_APP_USER", "dbx_app_user"),
            "password": os.getenv("DB_APP_PASSWORD", "dbx_secure_2025")
        }
    
    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_direct_connection(self):
        """Get direct psycopg2 connection for advanced features"""
        conn = psycopg2.connect(**self.connection_params, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Direct connection error: {e}")
            raise
        finally:
            conn.close()
    
    def set_org_context(self, session: Session, org_id: str):
        """Set organization context for Row Level Security"""
        session.execute(
            text("SELECT dbx_aviation.set_org_context(:org_id)"),
            {"org_id": org_id}
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with new monitoring features"""
        try:
            with self.get_direct_connection() as conn:
                with conn.cursor() as cursor:
                    # Use a simple health check that works
                    cursor.execute("""
                        SELECT 
                            NOW() as timestamp,
                            COUNT(*) as active_connections,
                            pg_database_size(current_database()) as database_size_bytes
                        FROM pg_stat_activity 
                        WHERE state = 'active'
                    """)
                    health_data = cursor.fetchone()
                    
                    return {
                        "status": "healthy",
                        "timestamp": health_data["timestamp"],
                        "active_connections": health_data["active_connections"],
                        "database_size_mb": round(health_data["database_size_bytes"] / 1024.0 / 1024.0, 2),
                        "overall_health": "healthy"
                    }
                    
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    def authenticate_user(self, email: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Authenticate user using enhanced security system"""
        try:
            # Use superuser connection for authentication (bypass RLS)
            superuser_params = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "dbx_aviation"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "password")
            }
            
            conn = psycopg2.connect(**superuser_params, cursor_factory=RealDictCursor)
            
            with conn.cursor() as cursor:
                # Authentication with superuser to bypass RLS
                cursor.execute("""
                    SELECT u.user_id, u.org_id, u.role, u.permissions, u.is_active,
                           u.password_hash, u.salt
                    FROM dbx_aviation.users u
                    WHERE u.email = %s AND u.is_active = true
                """, (email,))
                
                user_data = cursor.fetchone()
                
                if not user_data:
                    return {"success": False, "error": "User not found"}
                
                # Verify password using the function
                cursor.execute("SELECT dbx_aviation.verify_password(%s, %s, %s) as is_valid", 
                             (password, user_data["password_hash"], user_data["salt"]))
                verify_result = cursor.fetchone()["is_valid"]
                
                if not verify_result:
                    return {"success": False, "error": "Invalid password"}
                
                # Update last login
                cursor.execute("""
                    UPDATE dbx_aviation.users 
                    SET last_login_at = NOW(), last_login_ip = %s
                    WHERE user_id = %s
                """, (ip_address, user_data["user_id"]))
                
                conn.commit()
                
                return {
                    "success": True,
                    "user_id": str(user_data["user_id"]),
                    "org_id": str(user_data["org_id"]),
                    "role": user_data["role"],
                    "permissions": user_data["permissions"] or []
                }
            
            conn.close()
                    
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {"success": False, "error": "Authentication system error"}
    
    def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate API key using enhanced system"""
        try:
            with self.get_direct_connection() as conn:
                with conn.cursor() as cursor:
                    # Hash the API key
                    import hashlib
                    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                    
                    # Check API key
                    cursor.execute("""
                        SELECT ak.org_id, ak.scopes, ak.rate_limit_per_minute, ak.rate_limit_per_hour,
                               o.org_code, o.org_name, o.subscription_tier
                        FROM dbx_aviation.api_keys ak
                        JOIN dbx_aviation.organizations o ON ak.org_id = o.org_id
                        WHERE ak.key_hash = %s AND ak.is_active = true
                        AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
                    """, (key_hash,))
                    
                    key_data = cursor.fetchone()
                    
                    if not key_data:
                        return {"valid": False, "error": "Invalid API key"}
                    
                    # Update usage statistics
                    cursor.execute("""
                        UPDATE dbx_aviation.api_keys 
                        SET last_used_at = NOW(), total_requests = total_requests + 1
                        WHERE key_hash = %s
                    """, (key_hash,))
                    
                    return {
                        "valid": True,
                        "org_id": str(key_data["org_id"]),
                        "org_code": key_data["org_code"],
                        "org_name": key_data["org_name"],
                        "subscription_tier": key_data["subscription_tier"],
                        "scopes": key_data["scopes"],
                        "rate_limits": {
                            "per_minute": key_data["rate_limit_per_minute"],
                            "per_hour": key_data["rate_limit_per_hour"]
                        }
                    }
                    
        except Exception as e:
            logger.error(f"API key authentication failed: {e}")
            return {"valid": False, "error": "API key system error"}
    
    def save_analysis_result_enhanced(self, org_id: str, session_id: str, analysis_data: Dict[str, Any]) -> str:
        """Save ML analysis results with enhanced features"""
        try:
            # Validate session_id is a proper UUID
            import uuid
            try:
                uuid.UUID(session_id)  # This will raise ValueError if not a valid UUID
            except ValueError:
                # If not a valid UUID, generate a new one
                session_id = str(uuid.uuid4())
                logger.warning(f"Invalid session_id provided, generated new one: {session_id}")
            
            # Use superuser connection to bypass RLS issues
            superuser_params = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "dbx_aviation"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "password")
            }
            
            conn = psycopg2.connect(**superuser_params, cursor_factory=RealDictCursor)
            
            with conn.cursor() as cursor:
                # First, ensure we have an aircraft record (with shorter registration)
                short_reg = f"TEST_{session_id[:6]}"  # Keep it under 20 chars
                cursor.execute("""
                    INSERT INTO dbx_aviation.aircraft_registry (
                        aircraft_id, org_id, registration_number, aircraft_type, 
                        manufacturer, model, created_at, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), true)
                    ON CONFLICT (org_id, registration_number) DO NOTHING
                    RETURNING aircraft_id
                """, (
                    str(uuid.uuid4()), org_id, short_reg,
                    analysis_data.get("detected_aircraft_type", "multirotor"),
                    "Test Mfg", "Test Model"
                ))
                
                # Get the aircraft_id (either newly created or existing)
                cursor.execute("""
                    SELECT aircraft_id FROM dbx_aviation.aircraft_registry
                    WHERE org_id = %s AND registration_number = %s
                """, (org_id, short_reg))
                aircraft_result = cursor.fetchone()
                aircraft_id = aircraft_result["aircraft_id"] if aircraft_result else str(uuid.uuid4())
                
                # Then, ensure we have a flight session for this session_id
                cursor.execute("""
                    INSERT INTO dbx_aviation.flight_sessions (
                        session_id, org_id, aircraft_id, flight_number, session_status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (session_id) DO NOTHING
                """, (
                    session_id, org_id, aircraft_id,
                    f"FL_{session_id[:8]}", 
                    "completed"
                ))
                
                # Now save the analysis result
                cursor.execute("""
                    INSERT INTO dbx_aviation.ml_analysis_results 
                    (session_id, org_id, model_version, model_type, detected_aircraft_type,
                     aircraft_confidence, anomaly_detected, anomaly_score, risk_score, risk_level,
                     anomalies, shap_values, ai_report_content, processing_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING analysis_id
                """, (
                    session_id, org_id,
                    analysis_data.get("model_version", "2.0.0"),
                    "multi_aircraft_detection",
                    analysis_data.get("detected_aircraft_type"),
                    analysis_data.get("aircraft_confidence"),
                    analysis_data.get("anomaly_detected", False),
                    analysis_data.get("anomaly_score"),
                    analysis_data.get("risk_score"),
                    analysis_data.get("risk_level"),
                    json.dumps(analysis_data.get("anomalies", [])),
                    json.dumps(analysis_data.get("shap_values", {})),
                    analysis_data.get("ai_report_content"),
                    analysis_data.get("processing_time_ms")
                ))
                
                analysis_id = cursor.fetchone()["analysis_id"]
                conn.commit()
                
            conn.close()
            logger.info(f"Analysis result saved: {analysis_id}")
            return str(analysis_id)
                
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            raise
    
    def get_recent_analyses_enhanced(self, org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results with enhanced data"""
        try:
            with self.get_session() as session:
                # Set organization context
                self.set_org_context(session, org_id)
                
                result = session.execute(
                    text("""
                        SELECT 
                            mar.analysis_id,
                            mar.session_id,
                            fs.flight_number,
                            ar.registration_number,
                            ar.aircraft_type as registered_type,
                            mar.detected_aircraft_type,
                            mar.aircraft_confidence,
                            mar.risk_level,
                            mar.risk_score,
                            mar.anomaly_detected,
                            mar.processing_time_ms,
                            mar.analysis_timestamp
                        FROM dbx_aviation.ml_analysis_results mar
                        JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
                        JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
                        WHERE mar.org_id = :org_id
                        ORDER BY mar.analysis_timestamp DESC
                        LIMIT :limit
                    """),
                    {"org_id": org_id, "limit": limit}
                )
                
                analyses = []
                for row in result:
                    analyses.append({
                        "analysis_id": str(row.analysis_id),
                        "session_id": str(row.session_id),
                        "flight_number": row.flight_number,
                        "aircraft_registration": row.registration_number,
                        "registered_aircraft_type": row.registered_type,
                        "detected_aircraft_type": row.detected_aircraft_type,
                        "confidence": float(row.aircraft_confidence) if row.aircraft_confidence else 0.0,
                        "risk_level": row.risk_level,
                        "risk_score": float(row.risk_score) if row.risk_score else 0.0,
                        "anomaly_detected": row.anomaly_detected,
                        "processing_time_ms": row.processing_time_ms,
                        "analysis_timestamp": row.analysis_timestamp.isoformat()
                    })
                
                return analyses
                
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            return []
    
    def log_api_request(self, org_id: str, endpoint: str, method: str, status_code: int, 
                       response_time_ms: int, ip_address: str = None, error_message: str = None) -> str:
        """Log API request with enhanced tracking"""
        try:
            # Use superuser connection to bypass RLS for logging
            superuser_params = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME", "dbx_aviation"),
                "user": os.getenv("DB_USER", "postgres"),
                "password": os.getenv("DB_PASSWORD", "password")
            }
            
            conn = psycopg2.connect(**superuser_params, cursor_factory=RealDictCursor)
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO dbx_aviation.api_requests 
                    (org_id, endpoint, http_method, response_status_code, response_time_ms,
                     ip_address, error_occurred, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING request_id
                """, (
                    org_id, endpoint, method, status_code, response_time_ms,
                    ip_address, status_code >= 400, error_message
                ))
                
                request_id = cursor.fetchone()["request_id"]
                conn.commit()
                
            conn.close()
            return str(request_id)
                    
        except Exception as e:
            logger.error(f"Failed to log API request: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            with self.get_direct_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT policy_name, default_ttl_seconds, description
                        FROM dbx_aviation.cache_policies
                        WHERE is_active = true
                        ORDER BY policy_name
                    """)
                    
                    policies = []
                    for row in cursor.fetchall():
                        policies.append({
                            "policy_name": row["policy_name"],
                            "ttl_seconds": row["default_ttl_seconds"],
                            "description": row["description"]
                        })
                    
                    return {
                        "cache_policies": policies,
                        "total_policies": len(policies),
                        "status": "active"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}

# Create global instance
enhanced_db_manager = EnhancedDatabaseManager()

# Backward compatibility - keep the old interface
db_manager = enhanced_db_manager

def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    with enhanced_db_manager.get_session() as session:
        yield session

def get_default_org_id() -> str:
    """Get the default organization ID"""
    try:
        with enhanced_db_manager.get_direct_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT org_id FROM dbx_aviation.organizations 
                    WHERE org_code = 'DBX_DEFAULT' LIMIT 1
                """)
                result = cursor.fetchone()
                return str(result["org_id"]) if result else None
    except Exception as e:
        logger.error(f"Failed to get default org ID: {e}")
        return None

# Enhanced convenience functions
def create_flight_session(session: Session, org_id: str, aircraft_id: str, flight_data: Dict[str, Any]) -> str:
    """Create a new flight session (enhanced)"""
    session_id = str(uuid.uuid4())
    
    try:
        # Set organization context
        enhanced_db_manager.set_org_context(session, org_id)
        
        session.execute(text("""
            INSERT INTO dbx_aviation.flight_sessions (
                session_id, org_id, aircraft_id, flight_number,
                actual_departure, flight_duration_seconds,
                session_status, created_at
            ) VALUES (
                :session_id, :org_id, :aircraft_id, :flight_number,
                :departure, :duration, :status, :created_at
            )
        """), {
            "session_id": session_id,
            "org_id": org_id,
            "aircraft_id": aircraft_id,
            "flight_number": flight_data.get("flight_number", f"FL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "departure": flight_data.get("departure_time", datetime.now()),
            "duration": flight_data.get("duration_seconds", 0),
            "status": "completed",
            "created_at": datetime.now()
        })
        
        logger.info(f"Created flight session: {session_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to create flight session: {e}")
        raise

def save_analysis_result(session: Session, session_id: str, org_id: str, analysis_data: Dict[str, Any]) -> str:
    """Save analysis result (enhanced)"""
    return enhanced_db_manager.save_analysis_result_enhanced(org_id, session_id, analysis_data)

def get_recent_analyses(session: Session, org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent analyses (enhanced)"""
    return enhanced_db_manager.get_recent_analyses_enhanced(org_id, limit)

def get_or_create_aircraft(session: Session, org_id: str, aircraft_data: Dict[str, Any]) -> str:
    """Get or create aircraft (enhanced with RLS)"""
    # Set organization context
    enhanced_db_manager.set_org_context(session, org_id)
    
    # Try to find existing aircraft
    result = session.execute(text("""
        SELECT aircraft_id FROM dbx_aviation.aircraft_registry
        WHERE org_id = :org_id AND registration_number = :reg_number
        LIMIT 1
    """), {
        "org_id": org_id,
        "reg_number": aircraft_data.get("registration", "UNKNOWN")
    })
    
    existing = result.fetchone()
    if existing:
        return str(existing.aircraft_id)
    
    # Create new aircraft
    aircraft_id = str(uuid.uuid4())
    
    try:
        session.execute(text("""
            INSERT INTO dbx_aviation.aircraft_registry (
                aircraft_id, org_id, registration_number, aircraft_type,
                manufacturer, model, specifications, created_at
            ) VALUES (
                :aircraft_id, :org_id, :registration, :aircraft_type,
                :manufacturer, :model, :specifications, :created_at
            )
        """), {
            "aircraft_id": aircraft_id,
            "org_id": org_id,
            "registration": aircraft_data.get("registration", "UNKNOWN"),
            "aircraft_type": aircraft_data.get("type", "multirotor"),
            "manufacturer": aircraft_data.get("manufacturer", "Unknown"),
            "model": aircraft_data.get("model", "Unknown"),
            "specifications": json.dumps(aircraft_data.get("specifications", {})),
            "created_at": datetime.now()
        })
        
        logger.info(f"Created aircraft: {aircraft_id}")
        return aircraft_id
        
    except Exception as e:
        logger.error(f"Failed to create aircraft: {e}")
        raise