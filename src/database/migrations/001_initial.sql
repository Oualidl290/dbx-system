-- ============================================
-- DBX AI Multi-Aircraft System Database Schema
-- Production PostgreSQL Setup
-- ============================================

-- Create database (run as superuser)
-- CREATE DATABASE dbx_aviation WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';

-- Connect to the database and create schemas
-- \c dbx_aviation;

-- ============================================
-- SCHEMAS: Logical separation
-- ============================================
CREATE SCHEMA IF NOT EXISTS dbx_aviation;
CREATE SCHEMA IF NOT EXISTS dbx_analytics;
CREATE SCHEMA IF NOT EXISTS dbx_audit;
CREATE SCHEMA IF NOT EXISTS dbx_archive;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy search
-- CREATE EXTENSION IF NOT EXISTS "timescaledb"; -- For time-series (install separately)
-- CREATE EXTENSION IF NOT EXISTS "postgis"; -- For geospatial data (install separately)

-- ============================================
-- TABLE: organizations (Multi-tenant support)
-- ============================================
CREATE TABLE dbx_aviation.organizations (
    org_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_code VARCHAR(50) UNIQUE NOT NULL,
    org_name VARCHAR(255) NOT NULL,
    org_type VARCHAR(50) NOT NULL CHECK (org_type IN ('enterprise', 'commercial', 'private', 'government', 'training')),
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'basic',
    api_key_hash VARCHAR(255) NOT NULL,
    api_rate_limit INTEGER DEFAULT 1000,
    storage_quota_gb INTEGER DEFAULT 100,
    
    -- Compliance & Security
    compliance_level VARCHAR(50) DEFAULT 'standard', -- 'standard', 'enhanced', 'regulatory'
    data_retention_days INTEGER DEFAULT 365,
    encryption_enabled BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT check_rate_limit CHECK (api_rate_limit > 0),
    CONSTRAINT check_storage_quota CHECK (storage_quota_gb > 0)
);

CREATE INDEX idx_org_api_key ON dbx_aviation.organizations USING hash(api_key_hash);
CREATE INDEX idx_org_active ON dbx_aviation.organizations(is_active) WHERE is_active = true;

-- ============================================
-- TABLE: aircraft_registry
-- ============================================
CREATE TABLE dbx_aviation.aircraft_registry (
    aircraft_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES dbx_aviation.organizations(org_id) ON DELETE CASCADE,
    
    -- Aircraft Identification
    registration_number VARCHAR(20) NOT NULL,
    serial_number VARCHAR(100),
    call_sign VARCHAR(20),
    
    -- Aircraft Classification
    aircraft_type VARCHAR(50) NOT NULL CHECK (aircraft_type IN ('fixed_wing', 'multirotor', 'vtol', 'helicopter', 'hybrid')),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    model_year INTEGER,
    
    -- Technical Specifications
    specifications JSONB NOT NULL DEFAULT '{}'::jsonb,
    /* Expected structure:
    {
        "motors": {"count": 4, "type": "brushless", "max_rpm": 15000},
        "dimensions": {"length_m": 2.5, "wingspan_m": 3.0, "height_m": 0.8},
        "weight": {"empty_kg": 25, "max_takeoff_kg": 50},
        "performance": {
            "max_speed_ms": 45,
            "cruise_speed_ms": 30,
            "stall_speed_ms": 12,
            "max_altitude_m": 5000,
            "endurance_minutes": 120
        },
        "sensors": ["gps", "imu", "barometer", "magnetometer", "lidar"],
        "control_surfaces": ["elevator", "aileron", "rudder"]
    }
    */
    
    -- Operational Status
    operational_status VARCHAR(50) DEFAULT 'active',
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    total_flight_hours DECIMAL(10,2) DEFAULT 0,
    total_flight_cycles INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    
    -- Unique constraint per organization
    CONSTRAINT uk_aircraft_reg_per_org UNIQUE(org_id, registration_number)
);

CREATE INDEX idx_aircraft_org ON dbx_aviation.aircraft_registry(org_id);
CREATE INDEX idx_aircraft_type ON dbx_aviation.aircraft_registry(aircraft_type);
CREATE INDEX idx_aircraft_status ON dbx_aviation.aircraft_registry(operational_status);
CREATE INDEX idx_aircraft_specs_gin ON dbx_aviation.aircraft_registry USING gin(specifications);

-- ============================================
-- TABLE: flight_sessions (Main flight tracking)
-- ============================================
CREATE TABLE dbx_aviation.flight_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES dbx_aviation.organizations(org_id),
    aircraft_id UUID NOT NULL REFERENCES dbx_aviation.aircraft_registry(aircraft_id),
    
    -- Session Identification
    flight_number VARCHAR(50),
    mission_type VARCHAR(50),
    pilot_id VARCHAR(100), -- External reference
    
    -- Temporal Data
    scheduled_departure TIMESTAMPTZ,
    actual_departure TIMESTAMPTZ,
    scheduled_arrival TIMESTAMPTZ,
    actual_arrival TIMESTAMPTZ,
    flight_duration_seconds INTEGER,
    
    -- Geospatial Data (simplified without PostGIS for now)
    departure_latitude DECIMAL(10, 8),
    departure_longitude DECIMAL(11, 8),
    arrival_latitude DECIMAL(10, 8),
    arrival_longitude DECIMAL(11, 8),
    max_altitude_m DECIMAL(10,2),
    total_distance_km DECIMAL(10,2),
    
    -- Flight Conditions
    weather_conditions JSONB,
    visibility_m INTEGER,
    wind_speed_ms DECIMAL(5,2),
    temperature_celsius DECIMAL(5,2),
    
    -- Session Status
    session_status VARCHAR(50) DEFAULT 'scheduled',
    data_quality_score DECIMAL(3,2),
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    uploaded_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    
    CONSTRAINT check_departure_before_arrival CHECK (actual_departure < actual_arrival),
    CONSTRAINT check_quality_score CHECK (data_quality_score BETWEEN 0 AND 1)
);

-- Indexes for performance
CREATE INDEX idx_flight_session_org ON dbx_aviation.flight_sessions(org_id);
CREATE INDEX idx_flight_session_aircraft ON dbx_aviation.flight_sessions(aircraft_id);
CREATE INDEX idx_flight_session_temporal ON dbx_aviation.flight_sessions(actual_departure, actual_arrival);
CREATE INDEX idx_flight_session_status ON dbx_aviation.flight_sessions(session_status);

-- ============================================
-- TABLE: flight_telemetry (Time-series data)
-- ============================================
CREATE TABLE dbx_aviation.flight_telemetry (
    telemetry_id BIGSERIAL,
    session_id UUID NOT NULL REFERENCES dbx_aviation.flight_sessions(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Core Telemetry Data
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    altitude_m DECIMAL(10,2),
    heading_degrees DECIMAL(5,2),
    
    -- Motion Data
    airspeed_ms DECIMAL(6,2),
    groundspeed_ms DECIMAL(6,2),
    vertical_speed_ms DECIMAL(6,2),
    
    -- Attitude
    pitch_degrees DECIMAL(5,2),
    roll_degrees DECIMAL(5,2),
    yaw_degrees DECIMAL(5,2),
    
    -- Motor/Engine Data (array for multi-motor)
    motor_rpm DECIMAL[] DEFAULT '{}',
    motor_temperature DECIMAL[] DEFAULT '{}',
    motor_current DECIMAL[] DEFAULT '{}',
    throttle_percent DECIMAL(5,2),
    
    -- Control Surfaces (for fixed-wing)
    elevator_position DECIMAL(5,2),
    aileron_position DECIMAL(5,2),
    rudder_position DECIMAL(5,2),
    flaps_position DECIMAL(5,2),
    
    -- Vibration Data (for multirotors)
    vibration_x DECIMAL(6,3),
    vibration_y DECIMAL(6,3),
    vibration_z DECIMAL(6,3),
    
    -- System Health
    battery_voltage DECIMAL(5,2),
    battery_current DECIMAL(6,2),
    battery_remaining_percent DECIMAL(5,2),
    system_warnings JSONB DEFAULT '[]'::jsonb,
    
    -- Raw sensor data (for replay/debugging)
    raw_sensor_data JSONB,
    
    PRIMARY KEY (session_id, timestamp)
);

-- Indexes for telemetry queries
CREATE INDEX idx_telemetry_session_time ON dbx_aviation.flight_telemetry(session_id, timestamp DESC);
CREATE INDEX idx_telemetry_altitude ON dbx_aviation.flight_telemetry(altitude_m);

-- ============================================
-- TABLE: ml_analysis_results
-- ============================================
CREATE TABLE dbx_aviation.ml_analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES dbx_aviation.flight_sessions(session_id),
    org_id UUID NOT NULL REFERENCES dbx_aviation.organizations(org_id),
    
    -- Model Information
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'aircraft_detection', 'anomaly_detection', 'risk_assessment'
    analysis_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_time_ms INTEGER,
    
    -- Aircraft Detection Results
    detected_aircraft_type VARCHAR(50),
    aircraft_confidence DECIMAL(5,4),
    aircraft_probabilities JSONB, -- {"fixed_wing": 0.95, "multirotor": 0.03, "vtol": 0.02}
    
    -- Anomaly Detection Results
    anomaly_detected BOOLEAN DEFAULT false,
    anomaly_score DECIMAL(5,4),
    anomaly_threshold DECIMAL(5,4),
    anomalies JSONB DEFAULT '[]'::jsonb,
    
    -- Risk Assessment
    risk_score DECIMAL(5,4),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    risk_factors JSONB DEFAULT '[]'::jsonb,
    
    -- SHAP Explainability
    shap_values JSONB,
    feature_importance JSONB,
    top_features JSONB, -- Top 5 most important features
    
    -- Flight Phases Analysis
    flight_phases JSONB,
    
    -- Performance Metrics
    performance_metrics JSONB,
    
    -- AI Report (from Gemini or other AI service)
    ai_report_generated BOOLEAN DEFAULT false,
    ai_report_content TEXT,
    ai_report_summary TEXT,
    ai_recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Quality Metrics
    data_completeness DECIMAL(5,4),
    confidence_score DECIMAL(5,4),
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    
    CONSTRAINT check_confidence CHECK (aircraft_confidence BETWEEN 0 AND 1),
    CONSTRAINT check_risk_score CHECK (risk_score BETWEEN 0 AND 1)
);

-- Indexes for analysis queries
CREATE INDEX idx_analysis_session ON dbx_aviation.ml_analysis_results(session_id);
CREATE INDEX idx_analysis_org ON dbx_aviation.ml_analysis_results(org_id);
CREATE INDEX idx_analysis_timestamp ON dbx_aviation.ml_analysis_results(analysis_timestamp DESC);
CREATE INDEX idx_analysis_risk ON dbx_aviation.ml_analysis_results(risk_level, risk_score);
CREATE INDEX idx_analysis_anomaly ON dbx_aviation.ml_analysis_results(anomaly_detected) WHERE anomaly_detected = true;
CREATE INDEX idx_analysis_aircraft_type ON dbx_aviation.ml_analysis_results(detected_aircraft_type);

-- ============================================
-- TABLE: api_requests (For monitoring and billing)
-- ============================================
CREATE TABLE dbx_aviation.api_requests (
    request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES dbx_aviation.organizations(org_id),
    
    -- Request Details
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    request_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Response
    response_status_code INTEGER,
    response_time_ms INTEGER,
    
    -- Payload Size
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    
    -- Analysis Details (if applicable)
    session_id UUID REFERENCES dbx_aviation.flight_sessions(session_id),
    analysis_id UUID REFERENCES dbx_aviation.ml_analysis_results(analysis_id),
    
    -- Rate Limiting
    rate_limit_remaining INTEGER,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    api_version VARCHAR(20),
    
    -- Error Tracking
    error_occurred BOOLEAN DEFAULT false,
    error_message TEXT
);

CREATE INDEX idx_api_request_org ON dbx_aviation.api_requests(org_id, request_timestamp DESC);
CREATE INDEX idx_api_request_endpoint ON dbx_aviation.api_requests(endpoint, http_method);
CREATE INDEX idx_api_request_error ON dbx_aviation.api_requests(error_occurred) WHERE error_occurred = true;

-- ============================================
-- AUDIT SCHEMA: Complete audit trail
-- ============================================
CREATE TABLE dbx_audit.audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Actor Information
    org_id UUID,
    user_id UUID,
    api_key_used VARCHAR(255),
    
    -- Action Details
    action_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'access'
    table_name VARCHAR(100),
    record_id UUID,
    
    -- Change Details
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Compliance
    compliance_relevant BOOLEAN DEFAULT false,
    data_classification VARCHAR(50) -- 'public', 'internal', 'confidential', 'restricted'
);

CREATE INDEX idx_audit_org ON dbx_audit.audit_log(org_id, timestamp DESC);
CREATE INDEX idx_audit_action ON dbx_audit.audit_log(action_type, table_name);
CREATE INDEX idx_audit_compliance ON dbx_audit.audit_log(compliance_relevant) WHERE compliance_relevant = true;

-- ============================================
-- FUNCTIONS: Utility functions
-- ============================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON dbx_aviation.organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_aircraft_updated_at BEFORE UPDATE ON dbx_aviation.aircraft_registry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON dbx_aviation.flight_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate API key hash
CREATE OR REPLACE FUNCTION dbx_aviation.generate_api_key_hash(api_key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(digest(api_key, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INITIAL DATA: Create default organization
-- ============================================
INSERT INTO dbx_aviation.organizations (
    org_code, 
    org_name, 
    org_type, 
    api_key_hash,
    created_by
) VALUES (
    'DBX_DEFAULT',
    'DBX AI Default Organization',
    'private',
    dbx_aviation.generate_api_key_hash('dbx_default_api_key_change_me'),
    uuid_generate_v4()
) ON CONFLICT (org_code) DO NOTHING;

-- ============================================
-- VIEWS: Useful views for common queries
-- ============================================

-- Active flights view
CREATE VIEW dbx_aviation.active_flights AS
SELECT 
    fs.session_id,
    fs.org_id,
    fs.flight_number,
    ar.registration_number,
    ar.aircraft_type,
    fs.actual_departure,
    fs.session_status,
    EXTRACT(EPOCH FROM (NOW() - fs.actual_departure))/60 as flight_duration_minutes
FROM dbx_aviation.flight_sessions fs
JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
WHERE fs.session_status = 'in_progress';

-- Recent analysis results view
CREATE VIEW dbx_aviation.recent_analysis AS
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
    mar.analysis_timestamp
FROM dbx_aviation.ml_analysis_results mar
JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
WHERE mar.analysis_timestamp > NOW() - INTERVAL '7 days'
ORDER BY mar.analysis_timestamp DESC;

-- ============================================
-- PERMISSIONS: Basic security setup
-- ============================================

-- Create application roles
CREATE ROLE dbx_app_read;
CREATE ROLE dbx_app_write;
CREATE ROLE dbx_app_admin;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA dbx_aviation TO dbx_app_read, dbx_app_write, dbx_app_admin;
GRANT USAGE ON SCHEMA dbx_analytics TO dbx_app_read, dbx_app_write, dbx_app_admin;
GRANT USAGE ON SCHEMA dbx_audit TO dbx_app_admin;

GRANT SELECT ON ALL TABLES IN SCHEMA dbx_aviation TO dbx_app_read;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA dbx_aviation TO dbx_app_write;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dbx_aviation TO dbx_app_admin;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dbx_aviation TO dbx_app_write, dbx_app_admin;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'DBX AI Database Schema Created Successfully!';
    RAISE NOTICE 'Schemas: dbx_aviation, dbx_analytics, dbx_audit, dbx_archive';
    RAISE NOTICE 'Tables: organizations, aircraft_registry, flight_sessions, flight_telemetry, ml_analysis_results, api_requests, audit_log';
    RAISE NOTICE 'Default organization created with code: DBX_DEFAULT';
    RAISE NOTICE 'Next steps: 1) Create application users 2) Set up connection pooling 3) Configure backups';
END $$;
-- =======
=====================================
-- CREATE APPLICATION USER FOR LOCAL DEVELOPMENT
-- ============================================

-- Create application user with limited privileges
DO $
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dbx_app_user') THEN
        CREATE USER dbx_app_user WITH PASSWORD 'dbx_secure_2025';
        RAISE NOTICE 'Created application user: dbx_app_user';
    END IF;
END $;

-- Grant necessary permissions to the application user
GRANT CONNECT ON DATABASE dbx_aviation TO dbx_app_user;
GRANT USAGE ON SCHEMA dbx_aviation TO dbx_app_user;
GRANT USAGE ON SCHEMA dbx_analytics TO dbx_app_user;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dbx_aviation TO dbx_app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA dbx_analytics TO dbx_app_user;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA dbx_aviation TO dbx_app_user;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA dbx_aviation GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO dbx_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA dbx_aviation GRANT USAGE, SELECT ON SEQUENCES TO dbx_app_user;

-- ============================================
-- SAMPLE DATA FOR LOCAL DEVELOPMENT
-- ============================================

-- Create some sample aircraft for testing
DO $
DECLARE
    default_org_id UUID;
BEGIN
    -- Get default organization ID
    SELECT org_id INTO default_org_id 
    FROM dbx_aviation.organizations 
    WHERE org_code = 'DBX_DEFAULT';
    
    IF default_org_id IS NOT NULL THEN
        -- Create sample aircraft
        INSERT INTO dbx_aviation.aircraft_registry (
            org_id, registration_number, aircraft_type, manufacturer, model,
            specifications, operational_status
        ) VALUES 
        (
            default_org_id, 'TEST-001', 'multirotor', 'DJI', 'Phantom 4 Pro',
            '{
                "motors": {"count": 4, "type": "brushless", "max_rpm": 15000},
                "dimensions": {"length_m": 0.35, "wingspan_m": 0.35, "height_m": 0.20},
                "weight": {"empty_kg": 1.4, "max_takeoff_kg": 1.8},
                "performance": {
                    "max_speed_ms": 20,
                    "cruise_speed_ms": 15,
                    "max_altitude_m": 6000,
                    "endurance_minutes": 30
                },
                "sensors": ["gps", "imu", "barometer", "magnetometer", "camera"]
            }'::jsonb,
            'active'
        ),
        (
            default_org_id, 'TEST-002', 'fixed_wing', 'Cessna', 'C172',
            '{
                "motors": {"count": 1, "type": "piston", "max_rpm": 2700},
                "dimensions": {"length_m": 8.28, "wingspan_m": 11.0, "height_m": 2.72},
                "weight": {"empty_kg": 767, "max_takeoff_kg": 1157},
                "performance": {
                    "max_speed_ms": 67,
                    "cruise_speed_ms": 56,
                    "stall_speed_ms": 24,
                    "max_altitude_m": 4267,
                    "endurance_minutes": 240
                },
                "sensors": ["gps", "attitude_indicator", "altimeter", "airspeed"],
                "control_surfaces": ["elevator", "aileron", "rudder", "flaps"]
            }'::jsonb,
            'active'
        ),
        (
            default_org_id, 'TEST-003', 'vtol', 'Bell', 'V-280 Valor',
            '{
                "motors": {"count": 2, "type": "turboshaft", "max_rpm": 6000},
                "dimensions": {"length_m": 15.5, "wingspan_m": 18.3, "height_m": 4.6},
                "weight": {"empty_kg": 6800, "max_takeoff_kg": 12700},
                "performance": {
                    "max_speed_ms": 139,
                    "cruise_speed_ms": 111,
                    "hover_ceiling_m": 1829,
                    "max_altitude_m": 7620,
                    "endurance_minutes": 180
                },
                "sensors": ["gps", "radar", "lidar", "eo_ir_camera", "weather_radar"],
                "control_surfaces": ["elevator", "aileron", "rudder"],
                "vtol_capability": true
            }'::jsonb,
            'active'
        )
        ON CONFLICT (org_id, registration_number) DO NOTHING;
        
        RAISE NOTICE '🛩️  Sample aircraft created: TEST-001 (Multirotor), TEST-002 (Fixed Wing), TEST-003 (VTOL)';
    END IF;
END $;

-- ============================================
-- LOCAL DEVELOPMENT COMPLETION
-- ============================================
DO $
BEGIN
    RAISE NOTICE '🎉 DBX AI Database Setup Complete for Local Development!';
    RAISE NOTICE '👤 Application user: dbx_app_user / dbx_secure_2025';
    RAISE NOTICE '🏢 Default organization: DBX_DEFAULT';
    RAISE NOTICE '🛩️  Sample aircraft: TEST-001, TEST-002, TEST-003';
    RAISE NOTICE '🚀 Ready for local development!';
END $;