"""
Database integration for DBX AI Engine
IMMEDIATE INTEGRATION - Connect the Ferrari database to the Toyota API
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        # Get database URL from environment
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:password@localhost:5432/dbx_aviation'
        )
        
        # Create engine with proper connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,  # Start smaller for development
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,  # 5 minutes for cloud databases
            echo=False
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
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
    
    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and basic stats"""
        try:
            with self.get_session() as session:
                # Test connection
                result = session.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                
                # Get basic stats
                stats = session.execute(text("""
                    SELECT 
                        (SELECT count(*) FROM dbx_aviation.organizations) as orgs,
                        (SELECT count(*) FROM dbx_aviation.aircraft_registry) as aircraft,
                        (SELECT count(*) FROM dbx_aviation.flight_sessions) as flights,
                        (SELECT count(*) FROM dbx_aviation.ml_analysis_results) as analyses
                """)).fetchone()
                
                return {
                    "status": "healthy",
                    "version": version[:50],
                    "organizations": stats[0],
                    "aircraft": stats[1],
                    "flights": stats[2],
                    "analyses": stats[3]
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    with db_manager.get_session() as session:
        yield session

def get_default_org_id() -> str:
    """Get the default organization ID for development"""
    try:
        with db_manager.get_session() as session:
            result = session.execute(text("""
                SELECT org_id FROM dbx_aviation.organizations 
                WHERE org_code = 'DBX_DEFAULT' LIMIT 1
            """))
            org_id = result.fetchone()
            return str(org_id[0]) if org_id else None
    except Exception as e:
        logger.error(f"Failed to get default org ID: {e}")
        return None

def create_flight_session(
    session: Session,
    org_id: str,
    aircraft_id: str,
    flight_data: Dict[str, Any]
) -> str:
    """Create a new flight session in the database"""
    session_id = str(uuid.uuid4())
    
    try:
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

def save_analysis_result(
    session: Session,
    session_id: str,
    org_id: str,
    analysis_data: Dict[str, Any]
) -> str:
    """Save ML analysis results to the database"""
    analysis_id = str(uuid.uuid4())
    
    try:
        session.execute(text("""
            INSERT INTO dbx_aviation.ml_analysis_results (
                analysis_id, session_id, org_id, model_version, model_type,
                detected_aircraft_type, aircraft_confidence,
                anomaly_detected, anomaly_score, risk_score, risk_level,
                anomalies, shap_values, ai_report_content,
                created_at
            ) VALUES (
                :analysis_id, :session_id, :org_id, :model_version, :model_type,
                :aircraft_type, :confidence, :anomaly_detected, :anomaly_score,
                :risk_score, :risk_level, :anomalies, :shap_values, :ai_report,
                :created_at
            )
        """), {
            "analysis_id": analysis_id,
            "session_id": session_id,
            "org_id": org_id,
            "model_version": analysis_data.get("model_version", "v2.0.0"),
            "model_type": "multi_aircraft_detection",
            "aircraft_type": analysis_data.get("detected_aircraft_type"),
            "confidence": analysis_data.get("aircraft_confidence", 0.0),
            "anomaly_detected": analysis_data.get("anomaly_detected", False),
            "anomaly_score": analysis_data.get("anomaly_score", 0.0),
            "risk_score": analysis_data.get("risk_score", 0.0),
            "risk_level": analysis_data.get("risk_level", "low"),
            "anomalies": json.dumps(analysis_data.get("anomalies", [])),
            "shap_values": json.dumps(analysis_data.get("shap_values", {})),
            "ai_report": analysis_data.get("ai_report", ""),
            "created_at": datetime.now()
        })
        
        logger.info(f"Saved analysis result: {analysis_id}")
        return analysis_id
        
    except Exception as e:
        logger.error(f"Failed to save analysis result: {e}")
        raise

def get_or_create_aircraft(
    session: Session,
    org_id: str,
    aircraft_data: Dict[str, Any]
) -> str:
    """Get existing aircraft or create new one"""
    
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
        return str(existing[0])
    
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

def get_recent_analyses(session: Session, org_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent analysis results for an organization"""
    try:
        result = session.execute(text("""
            SELECT 
                mar.analysis_id,
                mar.session_id,
                fs.flight_number,
                ar.registration_number,
                mar.detected_aircraft_type,
                mar.aircraft_confidence,
                mar.risk_level,
                mar.risk_score,
                mar.anomaly_detected,
                mar.created_at
            FROM dbx_aviation.ml_analysis_results mar
            JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
            JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
            WHERE mar.org_id = :org_id
            ORDER BY mar.created_at DESC
            LIMIT :limit
        """), {"org_id": org_id, "limit": limit})
        
        analyses = []
        for row in result:
            analyses.append({
                "analysis_id": str(row[0]),
                "session_id": str(row[1]),
                "flight_number": row[2],
                "aircraft_registration": row[3],
                "detected_aircraft_type": row[4],
                "confidence": float(row[5]) if row[5] else 0.0,
                "risk_level": row[6],
                "risk_score": float(row[7]) if row[7] else 0.0,
                "anomaly_detected": row[8],
                "created_at": row[9].isoformat()
            })
        
        return analyses
        
    except Exception as e:
        logger.error(f"Failed to get recent analyses: {e}")
        return []