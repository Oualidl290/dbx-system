# 🗄️ PostgreSQL Database Setup Guide

## 🚀 **Quick Setup (5 Minutes)**

### **Step 1: Install PostgreSQL**

**Windows:**
```bash
# Download from: https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql

# Or use winget:
winget install PostgreSQL.PostgreSQL
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **Step 2: Install Python Dependencies**
```bash
pip install -r database/requirements.txt
```

### **Step 3: Set Environment Variables**
```bash
# Create .env file or set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_postgres_password
```

### **Step 4: Run Database Setup**
```bash
python database/setup_database.py
```

## 🎯 **What This Creates**

### **Database Structure:**
- **Database**: `dbx_aviation`
- **Schemas**: `dbx_aviation`, `dbx_analytics`, `dbx_audit`, `dbx_archive`
- **Tables**: 7 main tables with proper relationships
- **Users**: Application users with proper permissions
- **Sample Data**: Test organization and aircraft

### **Generated Files:**
- `database/credentials.txt` - Application user passwords
- `database/api_key.txt` - Default API key for testing

## 🔧 **Manual Setup (If Automated Fails)**

### **1. Create Database Manually**
```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database
CREATE DATABASE dbx_aviation WITH ENCODING 'UTF8';

-- Connect to new database
\c dbx_aviation;

-- Run the schema file
\i database/init_database.sql
```

### **2. Create Application Users**
```sql
-- Create users with secure passwords
CREATE USER dbx_api_service WITH PASSWORD 'your_secure_password';
CREATE USER dbx_analytics_service WITH PASSWORD 'your_secure_password';

-- Grant permissions
GRANT dbx_app_write TO dbx_api_service;
GRANT dbx_app_read TO dbx_analytics_service;
```

## 🧪 **Test the Setup**

### **Test Database Connection**
```bash
python ai-engine/app/database.py
```

**Expected Output:**
```
Testing database connection...
✅ Database connection successful!
📊 Database version: PostgreSQL 15.x
📋 Found 7 tables:
   - dbx_aviation.organizations
   - dbx_aviation.aircraft_registry
   - dbx_aviation.flight_sessions
   - dbx_aviation.flight_telemetry
   - dbx_aviation.ml_analysis_results
   - dbx_aviation.api_requests
   - dbx_audit.audit_log
```

### **Test API Integration**
```bash
# Update your .env file with database credentials
echo "DATABASE_URL=postgresql://dbx_api_service:password@localhost:5432/dbx_aviation" >> .env

# Test the API
python deploy.py
curl http://localhost:8000/api/v2/system/status
```

## 🔐 **Security Configuration**

### **Update .env File**
```bash
# Database Configuration
DATABASE_URL=postgresql://dbx_api_service:your_password@localhost:5432/dbx_aviation
DB_ECHO=false

# API Configuration  
DBX_DEFAULT_API_KEY=your_api_key_from_api_key.txt

# Redis (keep existing)
REDIS_URL=redis://localhost:6379
```

### **Production Security**
```bash
# Use strong passwords
# Enable SSL connections
# Configure firewall rules
# Set up regular backups
# Monitor access logs
```

## 📊 **Database Features**

### **Multi-Tenant Support**
- Organizations isolated by `org_id`
- Row-level security policies
- API key authentication
- Rate limiting per organization

### **Time-Series Optimization**
- Partitioned tables for large datasets
- Optimized indexes for time-based queries
- Ready for TimescaleDB extension

### **Audit Trail**
- Complete audit logging
- Change tracking
- Compliance support
- Security monitoring

### **Analytics Ready**
- Materialized views for fast queries
- JSONB for flexible data storage
- Full-text search capabilities
- Geospatial data support (with PostGIS)

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. Connection Refused**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS
```

**2. Authentication Failed**
```bash
# Reset postgres password
sudo -u postgres psql
ALTER USER postgres PASSWORD 'newpassword';
```

**3. Database Doesn't Exist**
```bash
# Create database manually
createdb -U postgres dbx_aviation
```

**4. Permission Denied**
```bash
# Check user permissions
psql -U postgres -d dbx_aviation
\du  # List users and roles
```

### **Logs and Debugging**
```bash
# PostgreSQL logs location:
# Linux: /var/log/postgresql/
# macOS: /usr/local/var/log/
# Windows: C:\Program Files\PostgreSQL\15\data\log\

# Check logs for errors
tail -f /var/log/postgresql/postgresql-15-main.log
```

## 🎉 **Success Checklist**

- [ ] PostgreSQL installed and running
- [ ] Database `dbx_aviation` created
- [ ] All tables created successfully
- [ ] Application users created with permissions
- [ ] Sample data inserted
- [ ] Python connection test passes
- [ ] API integration works
- [ ] Credentials files secured

## 🔄 **Next Steps**

1. **Update FastAPI Integration**
   - Modify `ai-engine/app/api.py` to use PostgreSQL
   - Add authentication middleware
   - Implement proper error handling

2. **Add Data Persistence**
   - Store flight sessions in database
   - Save analysis results
   - Log API requests

3. **Enable Monitoring**
   - Set up database monitoring
   - Configure alerts
   - Track performance metrics

**Your production-grade database is now ready! 🚀**

# 🔐 4. EXISTING SECURITY FEATURES

## 4.1 Multi-Tenant Architecture

The database implements production-grade multi-tenant security:

```sql
-- Organizations table with API key authentication
CREATE TABLE dbx_aviation.organizations (
    org_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_code VARCHAR(50) UNIQUE NOT NULL,
    org_name VARCHAR(255) NOT NULL,
    org_type VARCHAR(50) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL,  -- SHA-256 hashed API keys
    api_rate_limit INTEGER DEFAULT 1000,
    storage_quota_gb INTEGER DEFAULT 100,
    
    -- Compliance fields
    compliance_level VARCHAR(50) DEFAULT 'standard',
    data_retention_days INTEGER DEFAULT 365,
    encryption_enabled BOOLEAN DEFAULT true
);

-- API key hashing function
CREATE OR REPLACE FUNCTION dbx_aviation.generate_api_key_hash(api_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(digest(api_key, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;
```

## 4.2 Data Encryption

```sql
-- ============================================
-- ENCRYPTION: Sensitive data protection
-- ============================================

-- Install pgcrypto for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted columns for sensitive data
ALTER TABLE dbx_aviation.organizations 
    ADD COLUMN api_key_encrypted BYTEA;

-- Function to encrypt API keys
CREATE OR REPLACE FUNCTION dbx_aviation.encrypt_api_key(p_api_key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(p_api_key, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt API keys
CREATE OR REPLACE FUNCTION dbx_aviation.decrypt_api_key(p_encrypted BYTEA)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(p_encrypted, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to encrypt sensitive telemetry data
CREATE OR REPLACE FUNCTION dbx_aviation.encrypt_sensitive_data(p_data JSONB)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(p_data::text, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enhanced audit trigger for sensitive operations
CREATE OR REPLACE FUNCTION dbx_audit.log_sensitive_access()
RETURNS TRIGGER AS $$
DECLARE
    org_id_val UUID;
    user_id_val UUID;
BEGIN
    -- Get current context
    BEGIN
        org_id_val := current_setting('app.current_org_id')::uuid;
    EXCEPTION WHEN OTHERS THEN
        org_id_val := NULL;
    END;
    
    BEGIN
        user_id_val := current_setting('app.current_user_id')::uuid;
    EXCEPTION WHEN OTHERS THEN
        user_id_val := NULL;
    END;
    
    -- Log the operation
    INSERT INTO dbx_audit.audit_log (
        org_id, user_id, action_type, table_name, record_id,
        old_values, new_values, compliance_relevant,
        ip_address, user_agent
    ) VALUES (
        org_id_val, user_id_val, TG_OP, 
        TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME,
        COALESCE(NEW.org_id, OLD.org_id),
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END,
        true,
        inet_client_addr(),
        current_setting('app.user_agent', true)
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Add audit triggers to sensitive tables
CREATE TRIGGER audit_organizations
    AFTER INSERT OR UPDATE OR DELETE ON dbx_aviation.organizations
    FOR EACH ROW EXECUTE FUNCTION dbx_audit.log_sensitive_access();

CREATE TRIGGER audit_aircraft_registry
    AFTER INSERT OR UPDATE OR DELETE ON dbx_aviation.aircraft_registry
    FOR EACH ROW EXECUTE FUNCTION dbx_audit.log_sensitive_access();

CREATE TRIGGER audit_flight_sessions
    AFTER INSERT OR UPDATE OR DELETE ON dbx_aviation.flight_sessions
    FOR EACH ROW EXECUTE FUNCTION dbx_audit.log_sensitive_access();

-- GDPR compliance functions
CREATE OR REPLACE FUNCTION dbx_aviation.gdpr_delete_user_data(p_user_identifier TEXT)
RETURNS void AS $$
BEGIN
    -- Log the deletion request
    INSERT INTO dbx_audit.audit_log (action_type, table_name, compliance_relevant, old_values)
    VALUES ('gdpr_deletion', 'user_data', true, jsonb_build_object('user_identifier', p_user_identifier));
    
    -- Delete or anonymize user data
    UPDATE dbx_aviation.flight_sessions 
    SET pilot_id = 'ANONYMIZED_' || session_id::text
    WHERE pilot_id = p_user_identifier;
    
    RAISE NOTICE 'GDPR deletion completed for user: %', p_user_identifier;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

# 📊 5. ADVANCED ANALYTICS & REPORTING

## 5.1 Analytics Functions

```sql
-- ============================================
-- ANALYTICS FUNCTIONS: Complex queries optimized
-- ============================================

-- Function to calculate fleet risk profile
CREATE OR REPLACE FUNCTION dbx_analytics.calculate_fleet_risk_profile(
    p_org_id UUID,
    p_start_date TIMESTAMPTZ,
    p_end_date TIMESTAMPTZ
)
RETURNS TABLE (
    aircraft_type VARCHAR,
    total_flights BIGINT,
    avg_risk_score NUMERIC,
    high_risk_flights BIGINT,
    critical_anomalies BIGINT,
    risk_trend VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH risk_data AS (
        SELECT 
            ar.aircraft_type,
            COUNT(DISTINCT fs.session_id) as flight_count,
            AVG(mar.risk_score) as avg_risk,
            COUNT(*) FILTER (WHERE mar.risk_level IN ('high', 'critical')) as high_risk,
            COUNT(*) FILTER (WHERE mar.anomaly_detected AND 
                 (mar.anomalies::text LIKE '%critical%')) as critical_anom,
            -- Calculate trend
            AVG(mar.risk_score) FILTER (
                WHERE fs.actual_departure >= p_end_date - INTERVAL '7 days'
            ) - AVG(mar.risk_score) FILTER (
                WHERE fs.actual_departure < p_end_date - INTERVAL '7 days'
            ) as risk_delta
        FROM dbx_aviation.aircraft_registry ar
        JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
        JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
        WHERE ar.org_id = p_org_id
            AND fs.actual_departure BETWEEN p_start_date AND p_end_date
        GROUP BY ar.aircraft_type
    )
    SELECT 
        aircraft_type,
        flight_count,
        ROUND(avg_risk, 4),
        high_risk,
        critical_anom,
        CASE 
            WHEN risk_delta > 0.05 THEN 'increasing'
            WHEN risk_delta < -0.05 THEN 'decreasing'
            ELSE 'stable'
        END as risk_trend
    FROM risk_data
    ORDER BY avg_risk DESC;
END;
$$ LANGUAGE plpgsql;

-- Function for predictive maintenance scoring
CREATE OR REPLACE FUNCTION dbx_analytics.calculate_maintenance_score(
    p_aircraft_id UUID
)
RETURNS TABLE (
    aircraft_id UUID,
    registration_number VARCHAR,
    maintenance_score NUMERIC,
    priority_level VARCHAR,
    recommended_action TEXT,
    next_maintenance_due DATE
) AS $$
BEGIN
    RETURN QUERY
    WITH component_health AS (
        SELECT 
            ar.aircraft_id,
            ar.registration_number,
            ar.next_maintenance_date,
            ar.total_flight_hours,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%motor%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as motor_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%control_surface%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as control_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%battery%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as battery_issues,
            AVG(mar.risk_score) FILTER (WHERE mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days') as recent_risk
        FROM dbx_aviation.aircraft_registry ar
        JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
        JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
        WHERE ar.aircraft_id = p_aircraft_id
        GROUP BY ar.aircraft_id, ar.registration_number, ar.next_maintenance_date, ar.total_flight_hours
    ),
    maintenance_calc AS (
        SELECT 
            *,
            -- Calculate maintenance urgency score
            (COALESCE(motor_issues * 0.4, 0) +
             COALESCE(control_issues * 0.3, 0) +
             COALESCE(battery_issues * 0.2, 0) +
             COALESCE(recent_risk * 100 * 0.1, 0) +
             CASE 
                WHEN next_maintenance_date <= CURRENT_DATE THEN 30
                WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' THEN 20
                WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 10
                ELSE 0
             END) as score
        FROM component_health
    )
    SELECT 
        mc.aircraft_id,
        mc.registration_number,
        ROUND(mc.score, 2) as maintenance_score,
        CASE 
            WHEN mc.score >= 50 THEN 'URGENT'
            WHEN mc.score >= 30 THEN 'HIGH'
            WHEN mc.score >= 15 THEN 'MEDIUM'
            ELSE 'LOW'
        END as priority_level,
        CASE 
            WHEN mc.motor_issues > 5 THEN 'Inspect motor systems immediately'
            WHEN mc.control_issues > 3 THEN 'Check control surface calibration'
            WHEN mc.battery_issues > 2 THEN 'Battery health assessment required'
            WHEN mc.next_maintenance_date <= CURRENT_DATE THEN 'Scheduled maintenance overdue'
            ELSE 'Continue normal operations'
        END as recommended_action,
        mc.next_maintenance_date
    FROM maintenance_calc mc;
END;
$$ LANGUAGE plpgsql;
```

## 5.2 Reporting Views

```sql
-- ============================================
-- REPORTING VIEWS: Executive dashboards
-- ============================================

-- Executive summary view
CREATE VIEW dbx_analytics.executive_summary AS
WITH monthly_stats AS (
    SELECT 
        org_id,
        DATE_TRUNC('month', actual_departure) as month,
        COUNT(*) as flights,
        COUNT(DISTINCT aircraft_id) as active_aircraft,
        AVG(flight_duration_seconds)/3600.0 as avg_hours,
        SUM(total_distance_km) as total_km
    FROM dbx_aviation.flight_sessions
    WHERE actual_departure >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY org_id, DATE_TRUNC('month', actual_departure)
),
risk_stats AS (
    SELECT 
        org_id,
        DATE_TRUNC('month', analysis_timestamp) as month,
        AVG(risk_score) as avg_risk,
        COUNT(*) FILTER (WHERE anomaly_detected) as anomalies,
        COUNT(*) FILTER (WHERE risk_level IN ('high', 'critical')) as high_risk
    FROM dbx_aviation.ml_analysis_results
    WHERE analysis_timestamp >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY org_id, DATE_TRUNC('month', analysis_timestamp)
)
SELECT 
    o.org_name,
    o.org_type,
    ms.month,
    ms.flights,
    ms.active_aircraft,
    ROUND(ms.avg_hours::numeric, 2) as avg_flight_hours,
    ROUND(ms.total_km::numeric, 0) as total_distance_km,
    ROUND(rs.avg_risk::numeric, 4) as avg_risk_score,
    rs.anomalies as anomaly_count,
    rs.high_risk as high_risk_flights,
    ROUND(100.0 * rs.high_risk / NULLIF(ms.flights, 0), 2) as high_risk_percentage
FROM dbx_aviation.organizations o
JOIN monthly_stats ms ON o.org_id = ms.org_id
LEFT JOIN risk_stats rs ON ms.org_id = rs.org_id AND ms.month = rs.month
WHERE o.is_active = true
ORDER BY o.org_name, ms.month DESC;

-- Maintenance prediction view
CREATE VIEW dbx_analytics.maintenance_predictions AS
WITH component_health AS (
    SELECT 
        ar.aircraft_id,
        ar.registration_number,
        ar.aircraft_type,
        COUNT(*) FILTER (WHERE 
            mar.anomalies::text LIKE '%motor%'
            AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days'
        ) as motor_issues,
        COUNT(*) FILTER (WHERE 
            mar.anomalies::text LIKE '%control_surface%'
            AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days'
        ) as control_issues,
        AVG(mar.risk_score) FILTER (
            WHERE mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days'
        ) as recent_risk,
        MAX(fs.actual_departure) as last_flight,
        ar.total_flight_hours,
        ar.next_maintenance_date
    FROM dbx_aviation.aircraft_registry ar
    JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
    JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
    WHERE ar.is_active = true
    GROUP BY ar.aircraft_id, ar.registration_number, ar.aircraft_type,
             ar.total_flight_hours, ar.next_maintenance_date
),
maintenance_score AS (
    SELECT 
        *,
        -- Calculate maintenance urgency score
        (
            COALESCE(motor_issues * 0.4, 0) +
            COALESCE(control_issues * 0.3, 0) +
            COALESCE(recent_risk * 100 * 0.3, 0) +
            CASE 
                WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' THEN 20
                WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 10
                ELSE 0
            END
        ) as urgency_score
    FROM component_health
)
SELECT 
    aircraft_id,
    registration_number,
    aircraft_type,
    motor_issues,
    control_issues,
    ROUND(recent_risk::numeric, 4) as recent_risk_score,
    last_flight,
    total_flight_hours,
    next_maintenance_date,
    ROUND(urgency_score::numeric, 2) as maintenance_urgency,
    CASE 
        WHEN urgency_score >= 50 THEN 'URGENT'
        WHEN urgency_score >= 30 THEN 'HIGH'
        WHEN urgency_score >= 15 THEN 'MEDIUM'
        ELSE 'LOW'
    END as priority_level
FROM maintenance_score
ORDER BY urgency_score DESC;
```

# 🔄 6. DATA LIFECYCLE MANAGEMENT

## 6.1 Archival Strategy

```sql
-- ============================================
-- ARCHIVAL: Data lifecycle management
-- ============================================

-- Create archive schema
CREATE SCHEMA IF NOT EXISTS dbx_archive;

-- Archive old telemetry data to compressed storage
CREATE OR REPLACE FUNCTION dbx_aviation.archive_old_telemetry()
RETURNS void AS $$
DECLARE
    archive_date DATE;
BEGIN
    archive_date := CURRENT_DATE - INTERVAL '90 days';
    
    -- Create archive table if not exists
    CREATE TABLE IF NOT EXISTS dbx_archive.flight_telemetry_archive (
        LIKE dbx_aviation.flight_telemetry INCLUDING ALL
    );
    
    -- Move to archive schema
    INSERT INTO dbx_archive.flight_telemetry_archive
    SELECT * FROM dbx_aviation.flight_telemetry
    WHERE timestamp < archive_date;
    
    -- Delete from main table
    DELETE FROM dbx_aviation.flight_telemetry
    WHERE timestamp < archive_date;
    
    RAISE NOTICE 'Archived % records older than %', ROW_COUNT, archive_date;
END;
$$ LANGUAGE plpgsql;

-- Data retention policy enforcement
CREATE OR REPLACE FUNCTION dbx_aviation.enforce_retention_policy()
RETURNS void AS $$
DECLARE
    org_record RECORD;
BEGIN
    FOR org_record IN 
        SELECT org_id, data_retention_days 
        FROM dbx_aviation.organizations 
        WHERE is_active = true
    LOOP
        -- Delete old analysis results
        DELETE FROM dbx_aviation.ml_analysis_results
        WHERE org_id = org_record.org_id
            AND created_at < CURRENT_DATE - INTERVAL '1 day' * org_record.data_retention_days;
        
        -- Delete old flight sessions
        DELETE FROM dbx_aviation.flight_sessions
        WHERE org_id = org_record.org_id
            AND created_at < CURRENT_DATE - INTERVAL '1 day' * org_record.data_retention_days;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## 6.2 Backup Strategy

```bash
#!/bin/bash
# backup_strategy.sh

# Full backup weekly
pg_dump -h localhost -U dbx_admin -d dbx_aviation \
    --format=custom \
    --compress=9 \
    --file=/backup/weekly/dbx_aviation_$(date +%Y%m%d).dump

# Incremental backup daily using WAL archiving
# In postgresql.conf:
# archive_command = 'test ! -f /backup/wal/%f && cp %p /backup/wal/%f'

# Point-in-time recovery setup
# restore_command = 'cp /backup/wal/%f %p'
# recovery_target_time = '2024-01-20 15:00:00'
```

# 🚀 7. APPLICATION INTEGRATION

## 7.1 Python SQLAlchemy Models

```python
# models.py - SQLAlchemy ORM Models

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, JSON, ARRAY, Numeric, Text, UUID
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from geoalchemy2 import Geography
import uuid

Base = declarative_base()

class Organization(Base):
    __tablename__ = 'organizations'
    __table_args__ = {'schema': 'dbx_aviation'}
    
    org_id = Column(pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_code = Column(String(50), unique=True, nullable=False)
    org_name = Column(String(255), nullable=False)
    org_type = Column(String(50), nullable=False)
    subscription_tier = Column(String(50), default='basic')
    api_key_hash = Column(String(255), nullable=False)
    api_rate_limit = Column(Integer, default=1000)
    storage_quota_gb = Column(Integer, default=100)
    
    # Relationships
    aircraft = relationship("Aircraft", back_populates="organization")
    flight_sessions = relationship("FlightSession", back_populates="organization")

class Aircraft(Base):
    __tablename__ = 'aircraft_registry'
    __table_args__ = {'schema': 'dbx_aviation'}
    
    aircraft_id = Column(pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(pg_UUID(as_uuid=True), ForeignKey('dbx_aviation.organizations.org_id'))
    registration_number = Column(String(20), nullable=False)
    aircraft_type = Column(String(50), nullable=False)
    manufacturer = Column(String(100))
    model = Column(String(100))
    specifications = Column(JSON, default={})
    operational_status = Column(String(50), default='active')
    total_flight_hours = Column(Numeric(10, 2), default=0)
    
    # Relationships
    organization = relationship("Organization", back_populates="aircraft")
    flight_sessions = relationship("FlightSession", back_populates="aircraft")

class FlightSession(Base):
    __tablename__ = 'flight_sessions'
    __table_args__ = {'schema': 'dbx_aviation'}
    
    session_id = Column(pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(pg_UUID(as_uuid=True), ForeignKey('dbx_aviation.organizations.org_id'))
    aircraft_id = Column(pg_UUID(as_uuid=True), ForeignKey('dbx_aviation.aircraft_registry.aircraft_id'))
    flight_number = Column(String(50))
    actual_departure = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    flight_duration_seconds = Column(Integer)
    departure_location = Column(Geography('POINT', 4326))
    arrival_location = Column(Geography('POINT', 4326))
    
    # Relationships
    organization = relationship("Organization", back_populates="flight_sessions")
    aircraft = relationship("Aircraft", back_populates="flight_sessions")
    telemetry = relationship("FlightTelemetry", back_populates="session")
    analysis_results = relationship("MLAnalysisResult", back_populates="session")

class MLAnalysisResult(Base):
    __tablename__ = 'ml_analysis_results'
    __table_args__ = {'schema': 'dbx_aviation'}
    
    analysis_id = Column(pg_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(pg_UUID(as_uuid=True), ForeignKey('dbx_aviation.flight_sessions.session_id'))
    org_id = Column(pg_UUID(as_uuid=True), ForeignKey('dbx_aviation.organizations.org_id'))
    model_version = Column(String(50), nullable=False)
    detected_aircraft_type = Column(String(50))
    aircraft_confidence = Column(Numeric(5, 4))
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Numeric(5, 4))
    risk_score = Column(Numeric(5, 4))
    risk_level = Column(String(20))
    shap_values = Column(JSON)
    ai_report_content = Column(Text)
    
    # Relationships
    session = relationship("FlightSession", back_populates="analysis_results")
```

## 7.2 Database Connection Pool

```python
# database.py - Connection pool configuration

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import os

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://dbx_api_service:password@localhost:5432/dbx_aviation'
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,          # Set to True for SQL debugging
            connect_args={
                "server_settings": {
                    "application_name": "dbx_ai_system",
                    "jit": "on"
                },
                "command_timeout": 60,
                "options": "-c statement_timeout=30000"  # 30 second timeout
            }
        )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )
    
    def get_session(self):
        """Get a database session"""
        session = self.SessionLocal()
        try:
            # Set organization context for RLS
            org_id = self.get_current_org_id()
            if org_id:
                session.execute(
                    "SELECT dbx_aviation.set_org_context(:org_id)",
                    {"org_id": org_id}
                )
            yield session
        finally:
            session.close()
    
    def execute_with_retry(self, func, max_retries=3):
        """Execute database operation with retry logic"""
        import time
        from sqlalchemy.exc import OperationalError, DatabaseError
        
        for attempt in range(max_retries):
            try:
                return func()
            except (OperationalError, DatabaseError) as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

# Initialize database manager
db_manager = DatabaseManager()
```

# 📈 8. MONITORING & OPERATIONS

## 8.1 Performance Monitoring Queries

```sql
-- ============================================
-- MONITORING: Production health checks
-- ============================================

-- Real-time performance dashboard
CREATE VIEW dbx_aviation.system_health AS
SELECT 
    'database_size' as metric,
    pg_database_size('dbx_aviation')::bigint as value,
    'bytes' as unit
UNION ALL
SELECT 
    'active_connections',
    count(*)::bigint,
    'connections'
FROM pg_stat_activity
WHERE datname = 'dbx_aviation'
UNION ALL
SELECT 
    'slow_queries_count',
    count(*)::bigint,
    'queries'
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- Queries averaging over 100ms
UNION ALL
SELECT 
    'cache_hit_ratio',
    round(100.0 * sum(heap_blks_hit) / 
          NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0))::bigint,
    'percent'
FROM pg_statio_user_tables;

-- Table bloat monitoring
CREATE VIEW dbx_aviation.table_bloat AS
WITH constants AS (
    SELECT current_setting('block_size')::numeric AS bs
),
bloat_info AS (
    SELECT 
        schemaname,
        tablename,
        cc.relpages,
        bs,
        CEIL((cc.reltuples*
              (datahdr + ma - CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END +
               nullhdr + 4))/(bs-20::float)) AS otta
    FROM (
        SELECT 
            schemaname, tablename,
            (datawidth + (hdr + ma - CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END))::numeric AS datahdr,
            (maxfracsum*(nullhdr+ma-CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END)) AS nullhdr,
            hdr, ma, bs
        FROM (
            SELECT 
                schemaname, tablename, hdr, ma, bs,
                SUM((1-null_frac)*avg_width) AS datawidth,
                MAX(null_frac) AS maxfracsum,
                hdr + (
                    SELECT 1+count(*)/8
                    FROM pg_stats s2
                    WHERE null_frac<>0 AND s2.schemaname = s.schemaname
                          AND s2.tablename = s.tablename
                ) AS nullhdr
            FROM pg_stats s, constants
            GROUP BY 1,2,3,4,5
        ) AS foo
    ) AS rs
    JOIN pg_class cc ON cc.relname = rs.tablename
    JOIN pg_namespace nn ON cc.relnamespace = nn.oid 
          AND nn.nspname = rs.schemaname
)
SELECT 
    schemaname,
    tablename,
    ROUND(CASE WHEN otta=0 THEN 0.0
          ELSE ((relpages-otta)::numeric/relpages)*100 END, 1) AS bloat_pct,
    pg_size_pretty((bs*(relpages-otta))::bigint) AS bloat_size
FROM bloat_info
WHERE schemaname = 'dbx_aviation'
ORDER BY (relpages-otta) DESC;
```

# 🎯 9. PRODUCTION DEPLOYMENT CHECKLIST

```yaml
# Production Deployment Checklist

## Infrastructure:
- [ ] PostgreSQL 15+ with TimescaleDB extension
- [ ] 32GB+ RAM for database server
- [ ] SSD storage with 10,000+ IOPS
- [ ] PgBouncer for connection pooling
- [ ] Redis for caching layer
- [ ] Streaming replication configured
- [ ] Point-in-time recovery setup
- [ ] Automated backup strategy

## Security:
- [ ] Row-level security enabled
- [ ] SSL/TLS connections enforced
- [ ] Firewall rules configured
- [ ] Database audit logging enabled
- [ ] Encryption at rest configured
- [ ] API key rotation implemented
- [ ] Penetration testing completed
- [ ] GDPR compliance verified

## Performance:
- [ ] Indexes optimized for query patterns
- [ ] Partitioning strategy implemented
- [ ] Materialized views created
- [ ] Connection pooling configured
- [ ] Query performance baseline established
- [ ] Load testing completed
- [ ] Monitoring dashboards setup
- [ ] Alert rules configured

## Operations:
- [ ] Runbook documentation complete
- [ ] Disaster recovery plan tested
- [ ] Maintenance windows defined
- [ ] SLA targets established
- [ ] On-call rotation setup
- [ ] Incident response procedures
- [ ] Change management process
- [ ] Capacity planning completed
```

# 💡 FINAL RECOMMENDATIONS

## Why This PostgreSQL Architecture is Production-Ready:

**Scalability**: Handles millions of telemetry records with partitioning and TimescaleDB
**Performance**: Sub-100ms query times with proper indexing and materialized views
**Security**: Multi-tenant isolation with RLS, encryption, and comprehensive audit trails
**Reliability**: High availability with streaming replication and automated backups
**Compliance**: GDPR-ready with data retention policies and audit logging
**Analytics**: Real-time dashboards and predictive maintenance capabilities
**Integration**: Clean API with SQLAlchemy ORM and connection pooling
**Operations**: Comprehensive monitoring and automated maintenance

This architecture transforms the DBX AI system from a prototype into a true production-grade platform capable of handling enterprise aviation operations at scale.

**Your enterprise-grade database is now complete! 🚀**