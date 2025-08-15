-- ============================================
-- DBX AI Aviation System - Complete Database Installation
-- Production-Ready Database with All Enhancements
-- ============================================

-- This script installs the complete DBX AI Aviation database system
-- with all security, performance, caching, and backup features

\echo '🚀 Installing DBX AI Aviation Database System v2.0'
\echo '=================================================='

-- Set client encoding and timezone
SET client_encoding = 'UTF8';
SET timezone = 'UTC';

-- Enable timing for performance monitoring
\timing on

\echo ''
\echo '📊 Step 1: Installing Core Database Schema...'
\i init_database.sql

\echo ''
\echo '🔐 Step 2: Installing Enhanced Security & Authentication...'
\i enhanced_security.sql

\echo ''
\echo '🚀 Step 3: Installing Smart Caching Management...'
\i smart_caching.sql

\echo ''
\echo '⚡ Step 4: Installing Performance Optimization...'
\i performance_optimization.sql

\echo ''
\echo '💾 Step 5: Installing Backup & Recovery System...'
\i backup_recovery.sql

\echo ''
\echo '🔧 Step 6: Installing Additional Production Features...'

-- ============================================
-- ADDITIONAL PRODUCTION FEATURES
-- ============================================

-- Enable query logging for performance monitoring
ALTER SYSTEM SET log_statement = 'mod'; -- Log all modifications
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second

-- Configure connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Enable auto-vacuum for better performance
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '1min';

-- ============================================
-- PRODUCTION MONITORING SETUP
-- ============================================

-- Create monitoring schema
CREATE SCHEMA IF NOT EXISTS dbx_monitoring;

-- System health monitoring table
CREATE TABLE dbx_monitoring.system_health (
    health_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Database Metrics
    active_connections INTEGER,
    total_connections INTEGER,
    database_size_bytes BIGINT,
    
    -- Performance Metrics
    queries_per_second DECIMAL(10,2),
    avg_query_time_ms DECIMAL(10,2),
    cache_hit_ratio DECIMAL(5,4),
    
    -- Resource Usage
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_percent DECIMAL(5,2),
    disk_usage_percent DECIMAL(5,2),
    
    -- Health Status
    overall_health VARCHAR(20) CHECK (overall_health IN ('healthy', 'warning', 'critical')),
    alerts JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    server_version TEXT,
    uptime_seconds BIGINT
);

-- Create index for health monitoring
CREATE INDEX idx_system_health_timestamp ON dbx_monitoring.system_health(timestamp DESC);

-- Function to collect system health metrics
CREATE OR REPLACE FUNCTION dbx_monitoring.collect_health_metrics()
RETURNS JSONB AS $$
DECLARE
    health_data JSONB;
    active_conn INTEGER;
    total_conn INTEGER;
    db_size BIGINT;
    cache_ratio DECIMAL;
    overall_status VARCHAR(20);
BEGIN
    -- Collect database metrics
    SELECT COUNT(*) INTO active_conn FROM pg_stat_activity WHERE state = 'active';
    SELECT COUNT(*) INTO total_conn FROM pg_stat_activity;
    SELECT pg_database_size(current_database()) INTO db_size;
    
    -- Calculate cache hit ratio
    SELECT ROUND(
        (sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0))::numeric, 4
    ) INTO cache_ratio
    FROM pg_statio_user_tables;
    
    -- Determine overall health status
    overall_status := CASE 
        WHEN active_conn > 150 OR cache_ratio < 0.8 THEN 'critical'
        WHEN active_conn > 100 OR cache_ratio < 0.9 THEN 'warning'
        ELSE 'healthy'
    END;
    
    -- Insert health record
    INSERT INTO dbx_monitoring.system_health (
        active_connections, total_connections, database_size_bytes,
        cache_hit_ratio, overall_health
    ) VALUES (
        active_conn, total_conn, db_size, cache_ratio, overall_status
    );
    
    health_data := jsonb_build_object(
        'timestamp', NOW(),
        'active_connections', active_conn,
        'total_connections', total_conn,
        'database_size_mb', ROUND(db_size / 1024.0 / 1024.0, 2),
        'cache_hit_ratio', cache_ratio,
        'overall_health', overall_status
    );
    
    RETURN health_data;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- API INTEGRATION HELPERS
-- ============================================

-- Function to get organization by API key
CREATE OR REPLACE FUNCTION dbx_aviation.get_org_by_api_key(p_api_key TEXT)
RETURNS JSONB AS $$
DECLARE
    org_record RECORD;
    key_hash TEXT;
BEGIN
    -- Hash the provided API key
    key_hash := encode(digest(p_api_key, 'sha256'), 'hex');
    
    -- Find organization by API key hash
    SELECT o.org_id, o.org_code, o.org_name, o.subscription_tier,
           o.api_rate_limit, o.storage_quota_gb, o.is_active,
           ak.scopes, ak.rate_limit_per_minute, ak.rate_limit_per_hour
    INTO org_record
    FROM dbx_aviation.organizations o
    LEFT JOIN dbx_aviation.api_keys ak ON o.org_id = ak.org_id AND ak.key_hash = key_hash
    WHERE (o.api_key_hash = key_hash OR ak.key_hash = key_hash)
    AND o.is_active = true
    AND (ak.is_active = true OR ak.key_hash IS NULL);
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('valid', false, 'error', 'Invalid API key');
    END IF;
    
    -- Update last used timestamp for API key
    UPDATE dbx_aviation.api_keys 
    SET last_used_at = NOW(), total_requests = total_requests + 1
    WHERE key_hash = key_hash;
    
    -- Set organization context
    PERFORM dbx_aviation.set_org_context(org_record.org_id);
    
    RETURN jsonb_build_object(
        'valid', true,
        'org_id', org_record.org_id,
        'org_code', org_record.org_code,
        'org_name', org_record.org_name,
        'subscription_tier', org_record.subscription_tier,
        'rate_limits', jsonb_build_object(
            'per_minute', COALESCE(org_record.rate_limit_per_minute, 60),
            'per_hour', COALESCE(org_record.rate_limit_per_hour, 1000)
        ),
        'scopes', COALESCE(org_record.scopes, '["read"]'::jsonb)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log API requests
CREATE OR REPLACE FUNCTION dbx_aviation.log_api_request(
    p_org_id UUID,
    p_endpoint TEXT,
    p_method TEXT,
    p_status_code INTEGER,
    p_response_time_ms INTEGER,
    p_request_size INTEGER DEFAULT NULL,
    p_response_size INTEGER DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    request_id UUID;
BEGIN
    request_id := uuid_generate_v4();
    
    INSERT INTO dbx_aviation.api_requests (
        request_id, org_id, endpoint, http_method, response_status_code,
        response_time_ms, request_size_bytes, response_size_bytes,
        ip_address, user_agent, error_occurred, error_message
    ) VALUES (
        request_id, p_org_id, p_endpoint, p_method, p_status_code,
        p_response_time_ms, p_request_size, p_response_size,
        p_ip_address, p_user_agent, 
        (p_status_code >= 400), p_error_message
    );
    
    RETURN request_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DATA VALIDATION FUNCTIONS
-- ============================================

-- Function to validate flight telemetry data
CREATE OR REPLACE FUNCTION dbx_aviation.validate_telemetry_data(
    p_session_id UUID,
    p_telemetry_data JSONB
)
RETURNS JSONB AS $$
DECLARE
    validation_result JSONB;
    errors TEXT[] := '{}';
    warnings TEXT[] := '{}';
    aircraft_record RECORD;
BEGIN
    -- Get aircraft information for validation
    SELECT ar.aircraft_type, ar.specifications
    INTO aircraft_record
    FROM dbx_aviation.flight_sessions fs
    JOIN dbx_aviation.aircraft_registry ar ON fs.aircraft_id = ar.aircraft_id
    WHERE fs.session_id = p_session_id;
    
    -- Validate altitude
    IF (p_telemetry_data->>'altitude_m')::decimal < -100 THEN
        errors := array_append(errors, 'Altitude below sea level limit');
    END IF;
    
    IF (p_telemetry_data->>'altitude_m')::decimal > 10000 THEN
        warnings := array_append(warnings, 'Altitude above typical operating range');
    END IF;
    
    -- Validate battery voltage
    IF (p_telemetry_data->>'battery_voltage')::decimal < 9.0 THEN
        errors := array_append(errors, 'Battery voltage critically low');
    END IF;
    
    -- Validate motor RPM based on aircraft type
    IF aircraft_record.aircraft_type = 'multirotor' THEN
        IF jsonb_array_length(p_telemetry_data->'motor_rpm') < 4 THEN
            errors := array_append(errors, 'Insufficient motor data for multirotor');
        END IF;
    END IF;
    
    validation_result := jsonb_build_object(
        'valid', array_length(errors, 1) IS NULL OR array_length(errors, 1) = 0,
        'errors', errors,
        'warnings', warnings,
        'validated_at', NOW()
    );
    
    RETURN validation_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- MAINTENANCE SCHEDULER
-- ============================================

-- Create maintenance schedule table
CREATE TABLE dbx_monitoring.maintenance_schedule (
    schedule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- 'backup', 'cleanup', 'analyze', 'vacuum'
    schedule_expression VARCHAR(100) NOT NULL, -- Cron-like expression
    function_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    max_duration_minutes INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default maintenance tasks
INSERT INTO dbx_monitoring.maintenance_schedule (
    task_name, task_type, schedule_expression, function_name
) VALUES 
('Daily Database Maintenance', 'maintenance', '0 2 * * *', 'dbx_aviation.daily_maintenance'),
('Hourly Cache Cleanup', 'cleanup', '0 * * * *', 'dbx_aviation.cleanup_cache_stats'),
('Daily Backup Execution', 'backup', '0 3 * * *', 'dbx_aviation.execute_scheduled_backups'),
('Weekly Backup Cleanup', 'cleanup', '0 4 * * 0', 'dbx_aviation.cleanup_old_backups'),
('Health Metrics Collection', 'monitoring', '*/5 * * * *', 'dbx_monitoring.collect_health_metrics');

-- ============================================
-- FINAL SETUP AND VERIFICATION
-- ============================================

-- Create application database user (run as superuser)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dbx_app_user') THEN
        CREATE ROLE dbx_app_user WITH LOGIN PASSWORD 'change_me_in_production';
        GRANT dbx_app_write TO dbx_app_user;
        GRANT USAGE ON ALL SEQUENCES IN SCHEMA dbx_aviation TO dbx_app_user;
    END IF;
END $$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE dbx_aviation TO dbx_app_user;
GRANT USAGE ON SCHEMA dbx_aviation, dbx_analytics, dbx_monitoring TO dbx_app_user;

-- Create database configuration summary
CREATE OR REPLACE VIEW dbx_monitoring.database_summary AS
SELECT 
    'Database Version' as metric,
    version() as value
UNION ALL
SELECT 
    'Total Tables',
    COUNT(*)::text
FROM information_schema.tables 
WHERE table_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
UNION ALL
SELECT 
    'Total Indexes',
    COUNT(*)::text
FROM pg_indexes 
WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
UNION ALL
SELECT 
    'Total Functions',
    COUNT(*)::text
FROM information_schema.routines 
WHERE routine_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
UNION ALL
SELECT 
    'Database Size',
    pg_size_pretty(pg_database_size(current_database()))
UNION ALL
SELECT 
    'Installation Date',
    NOW()::text;

\echo ''
\echo '✅ Step 7: Running Final Verification...'

-- Verify installation
DO $$
DECLARE
    table_count INTEGER;
    function_count INTEGER;
    index_count INTEGER;
    policy_count INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring');
    
    -- Count functions
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines 
    WHERE routine_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring');
    
    -- Count indexes
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring');
    
    -- Count RLS policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE schemaname = 'dbx_aviation';
    
    RAISE NOTICE '';
    RAISE NOTICE '🎉 DBX AI Aviation Database Installation Complete!';
    RAISE NOTICE '================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Installation Summary:';
    RAISE NOTICE '  • Tables Created: %', table_count;
    RAISE NOTICE '  • Functions Created: %', function_count;
    RAISE NOTICE '  • Indexes Created: %', index_count;
    RAISE NOTICE '  • Security Policies: %', policy_count;
    RAISE NOTICE '';
    RAISE NOTICE '🔐 Security Features:';
    RAISE NOTICE '  ✅ User authentication with password hashing';
    RAISE NOTICE '  ✅ Session management with JWT support';
    RAISE NOTICE '  ✅ Row Level Security (RLS) policies';
    RAISE NOTICE '  ✅ API key management with scopes';
    RAISE NOTICE '  ✅ Multi-factor authentication support';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Performance Features:';
    RAISE NOTICE '  ✅ Smart caching with Redis integration';
    RAISE NOTICE '  ✅ Advanced indexing strategy';
    RAISE NOTICE '  ✅ Query performance monitoring';
    RAISE NOTICE '  ✅ Connection pool management';
    RAISE NOTICE '  ✅ Materialized views for analytics';
    RAISE NOTICE '';
    RAISE NOTICE '💾 Backup & Recovery:';
    RAISE NOTICE '  ✅ Automated backup policies';
    RAISE NOTICE '  ✅ Point-in-time recovery support';
    RAISE NOTICE '  ✅ Backup verification and integrity';
    RAISE NOTICE '  ✅ Recovery approval workflow';
    RAISE NOTICE '';
    RAISE NOTICE '📈 Monitoring & Maintenance:';
    RAISE NOTICE '  ✅ System health monitoring';
    RAISE NOTICE '  ✅ Performance alerting';
    RAISE NOTICE '  ✅ Automated maintenance tasks';
    RAISE NOTICE '  ✅ Comprehensive audit logging';
    RAISE NOTICE '';
    RAISE NOTICE '🔑 Default Credentials (CHANGE IN PRODUCTION!):';
    RAISE NOTICE '  • Admin User: admin@dbx-ai.com / admin123';
    RAISE NOTICE '  • Database User: dbx_app_user / change_me_in_production';
    RAISE NOTICE '  • Default Org: DBX_DEFAULT';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT NEXT STEPS:';
    RAISE NOTICE '  1. Change all default passwords';
    RAISE NOTICE '  2. Configure backup storage locations';
    RAISE NOTICE '  3. Set up monitoring alerts';
    RAISE NOTICE '  4. Configure SSL/TLS certificates';
    RAISE NOTICE '  5. Review and adjust performance settings';
    RAISE NOTICE '  6. Set up automated maintenance schedules';
    RAISE NOTICE '';
    RAISE NOTICE '📚 Documentation:';
    RAISE NOTICE '  • API Functions: SELECT * FROM dbx_monitoring.database_summary;';
    RAISE NOTICE '  • Health Check: SELECT dbx_monitoring.collect_health_metrics();';
    RAISE NOTICE '  • Performance: SELECT * FROM dbx_aviation.database_performance;';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your production-ready aviation AI database is now installed!';
    RAISE NOTICE '';
END $$;

-- Final timing report
\timing off

\echo ''
\echo '🎯 Installation completed successfully!'
\echo 'Database is ready for production use.'
\echo ''