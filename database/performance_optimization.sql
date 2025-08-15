-- ============================================
-- DBX AI Aviation System - Performance Optimization
-- Advanced Indexing, Query Optimization & Connection Management
-- ============================================

-- ============================================
-- ADVANCED INDEXING STRATEGY
-- ============================================

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flight_sessions_org_status_time 
    ON dbx_aviation.flight_sessions(org_id, session_status, actual_departure DESC)
    WHERE session_status IN ('completed', 'in_progress');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flight_sessions_aircraft_time
    ON dbx_aviation.flight_sessions(aircraft_id, actual_departure DESC)
    WHERE actual_departure IS NOT NULL;

-- Partial indexes for active records only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aircraft_active_by_org
    ON dbx_aviation.aircraft_registry(org_id, aircraft_type, operational_status)
    WHERE is_active = true AND operational_status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_sessions
    ON dbx_aviation.users(org_id, role, last_login_at DESC)
    WHERE is_active = true AND is_suspended = false;

-- GIN indexes for JSONB columns (specifications, metadata, etc.)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_aircraft_specs_performance
    ON dbx_aviation.aircraft_registry USING gin((specifications->'performance'));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_analysis_shap_values
    ON dbx_aviation.ml_analysis_results USING gin(shap_values);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ml_analysis_anomalies
    ON dbx_aviation.ml_analysis_results USING gin(anomalies);

-- Time-series optimized indexes for telemetry
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_telemetry_session_time_brin
    ON dbx_aviation.flight_telemetry USING brin(session_id, timestamp)
    WITH (pages_per_range = 128);

-- Covering indexes for common SELECT patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_flight_sessions_summary
    ON dbx_aviation.flight_sessions(org_id, session_status, actual_departure)
    INCLUDE (session_id, aircraft_id, flight_number, flight_duration_seconds);

-- ============================================
-- QUERY OPTIMIZATION VIEWS
-- ============================================

-- Materialized view for flight statistics (refreshed periodically)
CREATE MATERIALIZED VIEW dbx_aviation.flight_statistics AS
SELECT 
    org_id,
    aircraft_id,
    DATE_TRUNC('day', actual_departure) as flight_date,
    COUNT(*) as total_flights,
    AVG(flight_duration_seconds) as avg_duration_seconds,
    SUM(flight_duration_seconds) as total_flight_time_seconds,
    AVG(max_altitude_m) as avg_max_altitude,
    AVG(total_distance_km) as avg_distance_km,
    COUNT(*) FILTER (WHERE session_status = 'completed') as completed_flights,
    COUNT(*) FILTER (WHERE session_status = 'aborted') as aborted_flights
FROM dbx_aviation.flight_sessions
WHERE actual_departure IS NOT NULL
GROUP BY org_id, aircraft_id, DATE_TRUNC('day', actual_departure);

-- Create indexes on materialized view
CREATE UNIQUE INDEX idx_flight_stats_unique 
    ON dbx_aviation.flight_statistics(org_id, aircraft_id, flight_date);

CREATE INDEX idx_flight_stats_org_date 
    ON dbx_aviation.flight_statistics(org_id, flight_date DESC);

-- Materialized view for ML analysis summary
CREATE MATERIALIZED VIEW dbx_aviation.ml_analysis_summary AS
SELECT 
    org_id,
    detected_aircraft_type,
    DATE_TRUNC('day', analysis_timestamp) as analysis_date,
    COUNT(*) as total_analyses,
    AVG(aircraft_confidence) as avg_confidence,
    AVG(risk_score) as avg_risk_score,
    COUNT(*) FILTER (WHERE anomaly_detected = true) as anomaly_count,
    COUNT(*) FILTER (WHERE risk_level = 'high') as high_risk_count,
    COUNT(*) FILTER (WHERE risk_level = 'critical') as critical_risk_count,
    AVG(processing_time_ms) as avg_processing_time_ms
FROM dbx_aviation.ml_analysis_results
WHERE analysis_timestamp > NOW() - INTERVAL '90 days'
GROUP BY org_id, detected_aircraft_type, DATE_TRUNC('day', analysis_timestamp);

-- Create indexes on ML analysis summary
CREATE UNIQUE INDEX idx_ml_analysis_summary_unique
    ON dbx_aviation.ml_analysis_summary(org_id, detected_aircraft_type, analysis_date);

-- ============================================
-- PERFORMANCE MONITORING TABLES
-- ============================================

-- Query performance tracking
CREATE TABLE dbx_aviation.query_performance (
    query_id BIGSERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL, -- MD5 hash of normalized query
    query_type VARCHAR(50) NOT NULL, -- 'select', 'insert', 'update', 'delete'
    table_name VARCHAR(100),
    
    -- Performance Metrics
    execution_time_ms DECIMAL(10,3) NOT NULL,
    rows_examined BIGINT,
    rows_returned BIGINT,
    
    -- Resource Usage
    shared_blks_hit BIGINT,
    shared_blks_read BIGINT,
    temp_blks_read BIGINT,
    temp_blks_written BIGINT,
    
    -- Context
    org_id UUID REFERENCES dbx_aviation.organizations(org_id),
    user_id UUID REFERENCES dbx_aviation.users(user_id),
    
    -- Timing
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Query Details (for analysis)
    query_plan JSONB,
    query_text TEXT -- Store for slow queries only
);

-- Indexes for query performance analysis
CREATE INDEX idx_query_perf_hash_time ON dbx_aviation.query_performance(query_hash, executed_at DESC);
CREATE INDEX idx_query_perf_slow ON dbx_aviation.query_performance(execution_time_ms DESC, executed_at DESC) 
    WHERE execution_time_ms > 1000; -- Queries slower than 1 second
CREATE INDEX idx_query_perf_org ON dbx_aviation.query_performance(org_id, executed_at DESC);

-- Connection pool monitoring
CREATE TABLE dbx_aviation.connection_pool_stats (
    stat_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Pool Statistics
    total_connections INTEGER NOT NULL,
    active_connections INTEGER NOT NULL,
    idle_connections INTEGER NOT NULL,
    waiting_connections INTEGER NOT NULL,
    
    -- Performance Metrics
    avg_checkout_time_ms DECIMAL(8,2),
    max_checkout_time_ms DECIMAL(8,2),
    connection_errors_count INTEGER DEFAULT 0,
    
    -- Pool Configuration
    pool_name VARCHAR(50) NOT NULL,
    max_pool_size INTEGER NOT NULL,
    min_pool_size INTEGER NOT NULL,
    
    -- Health Indicators
    pool_health_score DECIMAL(3,2) GENERATED ALWAYS AS (
        CASE 
            WHEN total_connections = 0 THEN 0
            ELSE (active_connections::decimal / total_connections) * 
                 (1 - LEAST(waiting_connections::decimal / GREATEST(total_connections, 1), 1))
        END
    ) STORED
);

-- ============================================
-- PERFORMANCE OPTIMIZATION FUNCTIONS
-- ============================================

-- Function to analyze and suggest index improvements
CREATE OR REPLACE FUNCTION dbx_aviation.analyze_query_performance(
    time_window_hours INTEGER DEFAULT 24,
    min_execution_time_ms DECIMAL DEFAULT 100
)
RETURNS TABLE (
    query_hash VARCHAR(64),
    avg_execution_time_ms DECIMAL,
    total_executions BIGINT,
    table_name VARCHAR(100),
    suggested_index TEXT,
    priority_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        qp.query_hash,
        AVG(qp.execution_time_ms) as avg_execution_time_ms,
        COUNT(*) as total_executions,
        qp.table_name,
        CASE 
            WHEN qp.table_name = 'flight_sessions' AND AVG(qp.execution_time_ms) > 500 THEN
                'Consider index on (org_id, session_status, actual_departure)'
            WHEN qp.table_name = 'flight_telemetry' AND AVG(qp.execution_time_ms) > 200 THEN
                'Consider BRIN index on (session_id, timestamp)'
            WHEN qp.table_name = 'ml_analysis_results' AND AVG(qp.execution_time_ms) > 300 THEN
                'Consider index on (org_id, analysis_timestamp, risk_level)'
            ELSE 'Review query execution plan'
        END as suggested_index,
        -- Priority score: higher for frequent, slow queries
        (COUNT(*) * AVG(qp.execution_time_ms) / 1000.0) as priority_score
    FROM dbx_aviation.query_performance qp
    WHERE qp.executed_at > NOW() - (time_window_hours || ' hours')::INTERVAL
    AND qp.execution_time_ms >= min_execution_time_ms
    GROUP BY qp.query_hash, qp.table_name
    HAVING COUNT(*) > 5 -- Only queries executed more than 5 times
    ORDER BY priority_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views efficiently
CREATE OR REPLACE FUNCTION dbx_aviation.refresh_analytics_views()
RETURNS JSONB AS $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    result JSONB;
BEGIN
    start_time := NOW();
    
    -- Refresh flight statistics (incremental if possible)
    REFRESH MATERIALIZED VIEW CONCURRENTLY dbx_aviation.flight_statistics;
    
    -- Refresh ML analysis summary
    REFRESH MATERIALIZED VIEW CONCURRENTLY dbx_aviation.ml_analysis_summary;
    
    end_time := NOW();
    
    result := jsonb_build_object(
        'refresh_started_at', start_time,
        'refresh_completed_at', end_time,
        'duration_seconds', EXTRACT(EPOCH FROM (end_time - start_time)),
        'views_refreshed', ARRAY['flight_statistics', 'ml_analysis_summary']
    );
    
    -- Log the refresh
    INSERT INTO dbx_audit.audit_log (
        action_type, table_name, new_values, compliance_relevant
    ) VALUES (
        'refresh', 'materialized_views', result, false
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to optimize table statistics
CREATE OR REPLACE FUNCTION dbx_aviation.update_table_statistics()
RETURNS JSONB AS $$
DECLARE
    table_record RECORD;
    updated_tables TEXT[] := '{}';
    start_time TIMESTAMPTZ;
BEGIN
    start_time := NOW();
    
    -- Update statistics for main tables
    FOR table_record IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'dbx_aviation'
        AND tablename IN ('flight_sessions', 'flight_telemetry', 'ml_analysis_results', 'aircraft_registry')
    LOOP
        EXECUTE format('ANALYZE %I.%I', table_record.schemaname, table_record.tablename);
        updated_tables := array_append(updated_tables, table_record.tablename);
    END LOOP;
    
    RETURN jsonb_build_object(
        'updated_at', start_time,
        'duration_seconds', EXTRACT(EPOCH FROM (NOW() - start_time)),
        'tables_analyzed', updated_tables
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- CONNECTION POOL MANAGEMENT
-- ============================================

-- Function to monitor connection pool health
CREATE OR REPLACE FUNCTION dbx_aviation.record_connection_pool_stats(
    p_pool_name TEXT,
    p_total_connections INTEGER,
    p_active_connections INTEGER,
    p_idle_connections INTEGER,
    p_waiting_connections INTEGER,
    p_max_pool_size INTEGER,
    p_min_pool_size INTEGER,
    p_avg_checkout_time_ms DECIMAL DEFAULT NULL,
    p_max_checkout_time_ms DECIMAL DEFAULT NULL,
    p_connection_errors INTEGER DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO dbx_aviation.connection_pool_stats (
        pool_name, total_connections, active_connections, idle_connections,
        waiting_connections, max_pool_size, min_pool_size,
        avg_checkout_time_ms, max_checkout_time_ms, connection_errors_count
    ) VALUES (
        p_pool_name, p_total_connections, p_active_connections, p_idle_connections,
        p_waiting_connections, p_max_pool_size, p_min_pool_size,
        p_avg_checkout_time_ms, p_max_checkout_time_ms, p_connection_errors
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PERFORMANCE MONITORING VIEWS
-- ============================================

-- Real-time database performance view
CREATE VIEW dbx_aviation.database_performance AS
SELECT 
    'active_connections' as metric,
    COUNT(*) as value,
    'connections' as unit
FROM pg_stat_activity 
WHERE state = 'active'
UNION ALL
SELECT 
    'slow_queries_last_hour' as metric,
    COUNT(*) as value,
    'queries' as unit
FROM dbx_aviation.query_performance 
WHERE execution_time_ms > 1000 
AND executed_at > NOW() - INTERVAL '1 hour'
UNION ALL
SELECT 
    'cache_hit_ratio' as metric,
    ROUND((sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100)::numeric, 2) as value,
    'percent' as unit
FROM pg_statio_user_tables
UNION ALL
SELECT 
    'index_usage_ratio' as metric,
    ROUND((sum(idx_scan) / NULLIF(sum(idx_scan) + sum(seq_scan), 0) * 100)::numeric, 2) as value,
    'percent' as unit
FROM pg_stat_user_tables;

-- Table size and growth monitoring
CREATE VIEW dbx_aviation.table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    pg_stat_get_live_tuples(c.oid) as estimated_rows
FROM pg_tables t
JOIN pg_class c ON c.relname = t.tablename
WHERE schemaname = 'dbx_aviation'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage statistics
CREATE VIEW dbx_aviation.index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'dbx_aviation'
ORDER BY idx_scan DESC;

-- ============================================
-- AUTOMATED MAINTENANCE PROCEDURES
-- ============================================

-- Function for daily maintenance tasks
CREATE OR REPLACE FUNCTION dbx_aviation.daily_maintenance()
RETURNS JSONB AS $$
DECLARE
    maintenance_start TIMESTAMPTZ;
    stats_result JSONB;
    views_result JSONB;
    cleanup_result JSONB;
    result JSONB;
BEGIN
    maintenance_start := NOW();
    
    -- Update table statistics
    stats_result := dbx_aviation.update_table_statistics();
    
    -- Refresh materialized views
    views_result := dbx_aviation.refresh_analytics_views();
    
    -- Cleanup old performance data (keep 30 days)
    DELETE FROM dbx_aviation.query_performance 
    WHERE executed_at < NOW() - INTERVAL '30 days';
    
    DELETE FROM dbx_aviation.connection_pool_stats 
    WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- Vacuum analyze critical tables
    VACUUM ANALYZE dbx_aviation.flight_telemetry;
    VACUUM ANALYZE dbx_aviation.api_requests;
    
    result := jsonb_build_object(
        'maintenance_started_at', maintenance_start,
        'maintenance_completed_at', NOW(),
        'total_duration_seconds', EXTRACT(EPOCH FROM (NOW() - maintenance_start)),
        'statistics_update', stats_result,
        'views_refresh', views_result,
        'status', 'completed'
    );
    
    -- Log maintenance completion
    INSERT INTO dbx_audit.audit_log (
        action_type, table_name, new_values, compliance_relevant
    ) VALUES (
        'maintenance', 'database_performance', result, false
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PERFORMANCE ALERTING
-- ============================================

-- Function to check for performance issues
CREATE OR REPLACE FUNCTION dbx_aviation.check_performance_alerts()
RETURNS JSONB AS $$
DECLARE
    alerts JSONB := '[]'::jsonb;
    slow_query_count INTEGER;
    connection_pool_health DECIMAL;
    cache_hit_ratio DECIMAL;
BEGIN
    -- Check for slow queries in the last hour
    SELECT COUNT(*) INTO slow_query_count
    FROM dbx_aviation.query_performance
    WHERE execution_time_ms > 2000 
    AND executed_at > NOW() - INTERVAL '1 hour';
    
    IF slow_query_count > 10 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'slow_queries',
            'severity', 'warning',
            'message', format('Found %s slow queries (>2s) in the last hour', slow_query_count),
            'count', slow_query_count
        );
    END IF;
    
    -- Check connection pool health
    SELECT AVG(pool_health_score) INTO connection_pool_health
    FROM dbx_aviation.connection_pool_stats
    WHERE timestamp > NOW() - INTERVAL '15 minutes';
    
    IF connection_pool_health < 0.7 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'connection_pool',
            'severity', 'critical',
            'message', format('Connection pool health is poor: %.2f', connection_pool_health),
            'health_score', connection_pool_health
        );
    END IF;
    
    -- Check cache hit ratio
    SELECT ROUND((sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100)::numeric, 2)
    INTO cache_hit_ratio
    FROM pg_statio_user_tables
    WHERE schemaname = 'dbx_aviation';
    
    IF cache_hit_ratio < 90 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'cache_hit_ratio',
            'severity', 'warning',
            'message', format('Cache hit ratio is low: %.2f%%', cache_hit_ratio),
            'hit_ratio', cache_hit_ratio
        );
    END IF;
    
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'alerts', alerts,
        'alert_count', jsonb_array_length(alerts)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '⚡ Performance Optimization System Created!';
    RAISE NOTICE '✅ Advanced indexing strategy with composite and partial indexes';
    RAISE NOTICE '✅ Materialized views for flight and ML analysis statistics';
    RAISE NOTICE '✅ Query performance monitoring and analysis';
    RAISE NOTICE '✅ Connection pool health monitoring';
    RAISE NOTICE '✅ Automated maintenance procedures';
    RAISE NOTICE '✅ Performance alerting system';
    RAISE NOTICE '📊 Views: database_performance, table_sizes, index_usage';
    RAISE NOTICE '🔧 Functions: analyze_query_performance, daily_maintenance, check_performance_alerts';
    RAISE NOTICE '⏰ Schedule daily_maintenance() to run automatically';
END $$;