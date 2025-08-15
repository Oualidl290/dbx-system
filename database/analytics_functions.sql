-- ============================================
-- ADVANCED ANALYTICS: Complex queries optimized for production
-- ============================================

-- Enable required extensions for analytics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- ============================================
-- FLEET ANALYTICS FUNCTIONS
-- ============================================

-- Function to calculate fleet risk profile
CREATE OR REPLACE FUNCTION dbx_analytics.calculate_fleet_risk_profile(
    p_org_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    p_end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    aircraft_type VARCHAR,
    total_flights BIGINT,
    avg_risk_score NUMERIC,
    high_risk_flights BIGINT,
    critical_anomalies BIGINT,
    risk_trend VARCHAR,
    maintenance_due BIGINT,
    avg_flight_hours NUMERIC
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
            -- Calculate trend (recent vs older data)
            AVG(mar.risk_score) FILTER (
                WHERE fs.actual_departure >= p_end_date - INTERVAL '7 days'
            ) - AVG(mar.risk_score) FILTER (
                WHERE fs.actual_departure < p_end_date - INTERVAL '7 days'
            ) as risk_delta,
            COUNT(*) FILTER (WHERE ar.next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days') as maint_due,
            AVG(ar.total_flight_hours) as avg_hours
        FROM dbx_aviation.aircraft_registry ar
        JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
        LEFT JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
        WHERE ar.org_id = p_org_id
            AND fs.actual_departure BETWEEN p_start_date AND p_end_date
            AND ar.is_active = true
        GROUP BY ar.aircraft_type
    )
    SELECT 
        aircraft_type,
        flight_count,
        ROUND(COALESCE(avg_risk, 0), 4),
        COALESCE(high_risk, 0),
        COALESCE(critical_anom, 0),
        CASE 
            WHEN risk_delta > 0.05 THEN 'increasing'
            WHEN risk_delta < -0.05 THEN 'decreasing'
            ELSE 'stable'
        END as risk_trend,
        COALESCE(maint_due, 0),
        ROUND(COALESCE(avg_hours, 0), 2)
    FROM risk_data
    WHERE flight_count > 0
    ORDER BY avg_risk DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Function for anomaly pattern analysis
CREATE OR REPLACE FUNCTION dbx_analytics.analyze_anomaly_patterns(
    p_aircraft_id UUID DEFAULT NULL,
    p_org_id UUID DEFAULT NULL,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    anomaly_type VARCHAR,
    occurrence_count BIGINT,
    avg_severity NUMERIC,
    temporal_pattern VARCHAR,
    affected_aircraft BIGINT,
    correlation_score NUMERIC,
    recommended_action TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH anomaly_details AS (
        SELECT 
            jsonb_array_elements(mar.anomalies) as anomaly,
            fs.actual_departure,
            fs.aircraft_id,
            EXTRACT(hour FROM fs.actual_departure) as flight_hour,
            EXTRACT(dow FROM fs.actual_departure) as flight_dow,
            mar.risk_score
        FROM dbx_aviation.ml_analysis_results mar
        JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
        WHERE mar.anomaly_detected = true
            AND fs.actual_departure >= CURRENT_DATE - INTERVAL '1 day' * p_days_back
            AND (p_aircraft_id IS NULL OR fs.aircraft_id = p_aircraft_id)
            AND (p_org_id IS NULL OR fs.org_id = p_org_id)
    ),
    pattern_analysis AS (
        SELECT 
            anomaly->>'type' as anomaly_type,
            COUNT(*) as count,
            AVG((anomaly->>'confidence')::numeric) as avg_conf,
            COUNT(DISTINCT aircraft_id) as aircraft_count,
            STDDEV(flight_hour) as hour_stddev,
            STDDEV(flight_dow) as dow_stddev,
            AVG(risk_score) as avg_risk
        FROM anomaly_details
        WHERE anomaly->>'type' IS NOT NULL
        GROUP BY anomaly->>'type'
        HAVING COUNT(*) >= 2  -- Only patterns with multiple occurrences
    )
    SELECT 
        anomaly_type,
        count,
        ROUND(COALESCE(avg_conf, 0), 3),
        CASE 
            WHEN hour_stddev < 2 THEN 'time_specific'
            WHEN dow_stddev < 1 THEN 'day_specific'
            ELSE 'random'
        END as temporal_pattern,
        aircraft_count,
        ROUND(COALESCE(avg_conf * count::numeric / 100, 0), 3) as correlation_score,
        CASE 
            WHEN anomaly_type LIKE '%motor%' THEN 'Inspect motor systems and cooling'
            WHEN anomaly_type LIKE '%vibration%' THEN 'Check propeller balance and mounts'
            WHEN anomaly_type LIKE '%battery%' THEN 'Test battery health and connections'
            WHEN anomaly_type LIKE '%temperature%' THEN 'Verify cooling systems'
            ELSE 'Detailed inspection recommended'
        END as recommended_action
    FROM pattern_analysis
    ORDER BY correlation_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function for predictive maintenance scoring
CREATE OR REPLACE FUNCTION dbx_analytics.calculate_maintenance_score(
    p_aircraft_id UUID DEFAULT NULL,
    p_org_id UUID DEFAULT NULL
)
RETURNS TABLE (
    aircraft_id UUID,
    registration_number VARCHAR,
    aircraft_type VARCHAR,
    maintenance_score NUMERIC,
    priority_level VARCHAR,
    recommended_action TEXT,
    next_maintenance_due DATE,
    days_until_maintenance INTEGER,
    risk_factors TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH component_health AS (
        SELECT 
            ar.aircraft_id,
            ar.registration_number,
            ar.aircraft_type,
            ar.next_maintenance_date,
            ar.total_flight_hours,
            -- Count recent issues by type
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%motor%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as motor_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%control_surface%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as control_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%battery%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as battery_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%vibration%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as vibration_issues,
            COUNT(*) FILTER (WHERE mar.anomalies::text LIKE '%temperature%' 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '30 days') as temp_issues,
            -- Recent risk metrics
            AVG(mar.risk_score) FILTER (WHERE mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days') as recent_risk,
            COUNT(*) FILTER (WHERE mar.risk_level IN ('high', 'critical') 
                AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '14 days') as recent_high_risk
        FROM dbx_aviation.aircraft_registry ar
        LEFT JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
        LEFT JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
        WHERE ar.is_active = true
            AND (p_aircraft_id IS NULL OR ar.aircraft_id = p_aircraft_id)
            AND (p_org_id IS NULL OR ar.org_id = p_org_id)
        GROUP BY ar.aircraft_id, ar.registration_number, ar.aircraft_type, 
                 ar.next_maintenance_date, ar.total_flight_hours
    ),
    maintenance_calc AS (
        SELECT 
            *,
            -- Calculate maintenance urgency score (0-100)
            (
                COALESCE(motor_issues * 8.0, 0) +
                COALESCE(control_issues * 6.0, 0) +
                COALESCE(battery_issues * 5.0, 0) +
                COALESCE(vibration_issues * 7.0, 0) +
                COALESCE(temp_issues * 4.0, 0) +
                COALESCE(recent_risk * 30.0, 0) +
                COALESCE(recent_high_risk * 3.0, 0) +
                -- Time-based urgency
                CASE 
                    WHEN next_maintenance_date <= CURRENT_DATE THEN 40
                    WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' THEN 25
                    WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 15
                    WHEN next_maintenance_date <= CURRENT_DATE + INTERVAL '60 days' THEN 5
                    ELSE 0
                END +
                -- Flight hours factor
                CASE 
                    WHEN total_flight_hours > 1000 THEN 10
                    WHEN total_flight_hours > 500 THEN 5
                    ELSE 0
                END
            ) as score,
            -- Days until maintenance
            CASE 
                WHEN next_maintenance_date IS NOT NULL 
                THEN (next_maintenance_date - CURRENT_DATE)::integer
                ELSE NULL
            END as days_until,
            -- Build risk factors array
            ARRAY_REMOVE(ARRAY[
                CASE WHEN motor_issues > 0 THEN 'Motor anomalies detected (' || motor_issues || ')' END,
                CASE WHEN control_issues > 0 THEN 'Control surface issues (' || control_issues || ')' END,
                CASE WHEN battery_issues > 0 THEN 'Battery problems (' || battery_issues || ')' END,
                CASE WHEN vibration_issues > 0 THEN 'Vibration anomalies (' || vibration_issues || ')' END,
                CASE WHEN temp_issues > 0 THEN 'Temperature issues (' || temp_issues || ')' END,
                CASE WHEN recent_risk > 0.6 THEN 'High recent risk score (' || ROUND(recent_risk::numeric, 2) || ')' END,
                CASE WHEN recent_high_risk > 2 THEN 'Multiple high-risk flights (' || recent_high_risk || ')' END,
                CASE WHEN next_maintenance_date <= CURRENT_DATE THEN 'Maintenance overdue' END,
                CASE WHEN total_flight_hours > 1000 THEN 'High flight hours (' || total_flight_hours || ')' END
            ], NULL) as risk_factors_array
        FROM component_health
    )
    SELECT 
        mc.aircraft_id,
        mc.registration_number,
        mc.aircraft_type,
        ROUND(LEAST(mc.score, 100), 1) as maintenance_score,  -- Cap at 100
        CASE 
            WHEN mc.score >= 80 THEN 'CRITICAL'
            WHEN mc.score >= 60 THEN 'URGENT'
            WHEN mc.score >= 40 THEN 'HIGH'
            WHEN mc.score >= 20 THEN 'MEDIUM'
            ELSE 'LOW'
        END as priority_level,
        CASE 
            WHEN mc.score >= 80 THEN 'GROUND AIRCRAFT - Immediate inspection required'
            WHEN mc.score >= 60 THEN 'Schedule maintenance within 24 hours'
            WHEN mc.score >= 40 THEN 'Schedule maintenance within 1 week'
            WHEN mc.score >= 20 THEN 'Monitor closely, schedule routine maintenance'
            ELSE 'Continue normal operations'
        END as recommended_action,
        mc.next_maintenance_date,
        mc.days_until,
        mc.risk_factors_array
    FROM maintenance_calc mc
    ORDER BY mc.score DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- REPORTING VIEWS
-- ============================================

-- Executive summary view
CREATE OR REPLACE VIEW dbx_analytics.executive_summary AS
WITH monthly_stats AS (
    SELECT 
        o.org_id,
        o.org_name,
        o.org_type,
        DATE_TRUNC('month', fs.actual_departure) as month,
        COUNT(DISTINCT fs.session_id) as flights,
        COUNT(DISTINCT fs.aircraft_id) as active_aircraft,
        AVG(fs.flight_duration_seconds)/3600.0 as avg_hours,
        SUM(fs.total_distance_km) as total_km,
        COUNT(*) FILTER (WHERE fs.session_status = 'completed') as completed_flights,
        COUNT(*) FILTER (WHERE fs.session_status = 'cancelled') as cancelled_flights
    FROM dbx_aviation.organizations o
    LEFT JOIN dbx_aviation.flight_sessions fs ON o.org_id = fs.org_id
    WHERE o.is_active = true
        AND (fs.actual_departure IS NULL OR fs.actual_departure >= CURRENT_DATE - INTERVAL '12 months')
    GROUP BY o.org_id, o.org_name, o.org_type, DATE_TRUNC('month', fs.actual_departure)
),
risk_stats AS (
    SELECT 
        fs.org_id,
        DATE_TRUNC('month', mar.analysis_timestamp) as month,
        AVG(mar.risk_score) as avg_risk,
        COUNT(*) FILTER (WHERE mar.anomaly_detected) as anomalies,
        COUNT(*) FILTER (WHERE mar.risk_level IN ('high', 'critical')) as high_risk,
        COUNT(*) as total_analyses
    FROM dbx_aviation.ml_analysis_results mar
    JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
    WHERE mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY fs.org_id, DATE_TRUNC('month', mar.analysis_timestamp)
)
SELECT 
    ms.org_name,
    ms.org_type,
    ms.month,
    COALESCE(ms.flights, 0) as flights,
    COALESCE(ms.active_aircraft, 0) as active_aircraft,
    ROUND(COALESCE(ms.avg_hours, 0)::numeric, 2) as avg_flight_hours,
    ROUND(COALESCE(ms.total_km, 0)::numeric, 0) as total_distance_km,
    ROUND(COALESCE(rs.avg_risk, 0)::numeric, 4) as avg_risk_score,
    COALESCE(rs.anomalies, 0) as anomaly_count,
    COALESCE(rs.high_risk, 0) as high_risk_flights,
    ROUND(COALESCE(100.0 * rs.high_risk / NULLIF(ms.flights, 0), 0), 2) as high_risk_percentage,
    ROUND(COALESCE(100.0 * ms.completed_flights / NULLIF(ms.flights, 0), 0), 1) as completion_rate
FROM monthly_stats ms
LEFT JOIN risk_stats rs ON ms.org_id = rs.org_id AND ms.month = rs.month
WHERE ms.month IS NOT NULL
ORDER BY ms.org_name, ms.month DESC;

-- Real-time fleet status view
CREATE OR REPLACE VIEW dbx_analytics.fleet_status AS
WITH aircraft_stats AS (
    SELECT 
        ar.org_id,
        ar.aircraft_id,
        ar.registration_number,
        ar.aircraft_type,
        ar.operational_status,
        ar.total_flight_hours,
        ar.next_maintenance_date,
        -- Recent flight activity
        COUNT(fs.session_id) FILTER (WHERE fs.actual_departure >= CURRENT_DATE - INTERVAL '7 days') as flights_last_7_days,
        COUNT(fs.session_id) FILTER (WHERE fs.actual_departure >= CURRENT_DATE - INTERVAL '30 days') as flights_last_30_days,
        MAX(fs.actual_departure) as last_flight,
        -- Recent risk metrics
        AVG(mar.risk_score) FILTER (WHERE mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days') as recent_avg_risk,
        COUNT(*) FILTER (WHERE mar.anomaly_detected AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days') as recent_anomalies,
        COUNT(*) FILTER (WHERE mar.risk_level IN ('high', 'critical') AND mar.analysis_timestamp >= CURRENT_DATE - INTERVAL '7 days') as recent_high_risk
    FROM dbx_aviation.aircraft_registry ar
    LEFT JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
    LEFT JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
    WHERE ar.is_active = true
    GROUP BY ar.org_id, ar.aircraft_id, ar.registration_number, ar.aircraft_type, 
             ar.operational_status, ar.total_flight_hours, ar.next_maintenance_date
)
SELECT 
    o.org_name,
    ast.aircraft_id,
    ast.registration_number,
    ast.aircraft_type,
    ast.operational_status,
    ast.total_flight_hours,
    ast.next_maintenance_date,
    CASE 
        WHEN ast.next_maintenance_date <= CURRENT_DATE THEN 'OVERDUE'
        WHEN ast.next_maintenance_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'DUE_SOON'
        WHEN ast.next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'SCHEDULED'
        ELSE 'OK'
    END as maintenance_status,
    ast.flights_last_7_days,
    ast.flights_last_30_days,
    ast.last_flight,
    CASE 
        WHEN ast.last_flight IS NULL THEN 'NEVER_FLOWN'
        WHEN ast.last_flight < CURRENT_DATE - INTERVAL '30 days' THEN 'INACTIVE'
        WHEN ast.last_flight < CURRENT_DATE - INTERVAL '7 days' THEN 'LOW_ACTIVITY'
        ELSE 'ACTIVE'
    END as activity_status,
    ROUND(COALESCE(ast.recent_avg_risk, 0)::numeric, 3) as recent_avg_risk_score,
    COALESCE(ast.recent_anomalies, 0) as recent_anomalies,
    COALESCE(ast.recent_high_risk, 0) as recent_high_risk_flights,
    CASE 
        WHEN ast.recent_high_risk > 2 THEN 'HIGH_RISK'
        WHEN ast.recent_high_risk > 0 OR ast.recent_avg_risk > 0.6 THEN 'MEDIUM_RISK'
        WHEN ast.recent_anomalies > 3 THEN 'WATCH'
        ELSE 'NORMAL'
    END as risk_status
FROM aircraft_stats ast
JOIN dbx_aviation.organizations o ON ast.org_id = o.org_id
ORDER BY o.org_name, ast.aircraft_type, ast.registration_number;

-- System health monitoring view
CREATE OR REPLACE VIEW dbx_analytics.system_health AS
SELECT 
    'database_size' as metric,
    pg_size_pretty(pg_database_size(current_database())) as value,
    'Database storage usage' as description
UNION ALL
SELECT 
    'active_connections',
    count(*)::text,
    'Current database connections'
FROM pg_stat_activity
WHERE datname = current_database()
UNION ALL
SELECT 
    'slow_queries_count',
    count(*)::text,
    'Queries averaging over 100ms'
FROM pg_stat_statements
WHERE mean_exec_time > 100
UNION ALL
SELECT 
    'cache_hit_ratio',
    round(100.0 * sum(heap_blks_hit) / 
          GREATEST(sum(heap_blks_hit) + sum(heap_blks_read), 1))::text || '%',
    'Database cache efficiency'
FROM pg_statio_user_tables
UNION ALL
SELECT 
    'total_flights_today',
    count(*)::text,
    'Flights completed today'
FROM dbx_aviation.flight_sessions
WHERE actual_departure::date = CURRENT_DATE
UNION ALL
SELECT 
    'active_aircraft',
    count(*)::text,
    'Aircraft with flights in last 7 days'
FROM dbx_aviation.aircraft_registry ar
WHERE EXISTS (
    SELECT 1 FROM dbx_aviation.flight_sessions fs 
    WHERE fs.aircraft_id = ar.aircraft_id 
    AND fs.actual_departure >= CURRENT_DATE - INTERVAL '7 days'
)
UNION ALL
SELECT 
    'high_risk_flights_today',
    count(*)::text,
    'High/critical risk flights today'
FROM dbx_aviation.ml_analysis_results mar
JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
WHERE fs.actual_departure::date = CURRENT_DATE
AND mar.risk_level IN ('high', 'critical');

-- ============================================
-- AUTOMATED ANALYTICS JOBS
-- ============================================

-- Function to generate daily analytics summary
CREATE OR REPLACE FUNCTION dbx_analytics.generate_daily_summary()
RETURNS void AS $$
DECLARE
    summary_record RECORD;
BEGIN
    -- Create daily summary table if not exists
    CREATE TABLE IF NOT EXISTS dbx_analytics.daily_summaries (
        summary_date DATE PRIMARY KEY,
        total_flights INTEGER,
        total_organizations INTEGER,
        active_aircraft INTEGER,
        avg_risk_score NUMERIC,
        high_risk_flights INTEGER,
        anomalies_detected INTEGER,
        system_health_score NUMERIC,
        maintenance_due INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Calculate daily metrics
    WITH daily_metrics AS (
        SELECT 
            CURRENT_DATE as summary_date,
            COUNT(DISTINCT fs.session_id) as total_flights,
            COUNT(DISTINCT fs.org_id) as total_orgs,
            COUNT(DISTINCT fs.aircraft_id) as active_aircraft,
            AVG(mar.risk_score) as avg_risk,
            COUNT(*) FILTER (WHERE mar.risk_level IN ('high', 'critical')) as high_risk,
            COUNT(*) FILTER (WHERE mar.anomaly_detected) as anomalies,
            -- Simple health score based on error rates and performance
            GREATEST(0, 100 - (COUNT(*) FILTER (WHERE ar.error_occurred) * 100.0 / GREATEST(COUNT(*), 1))) as health_score,
            COUNT(DISTINCT aircraft.aircraft_id) FILTER (WHERE aircraft.next_maintenance_date <= CURRENT_DATE + INTERVAL '30 days') as maint_due
        FROM dbx_aviation.flight_sessions fs
        LEFT JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
        LEFT JOIN dbx_aviation.api_requests ar ON fs.session_id::text = ar.session_id::text
        LEFT JOIN dbx_aviation.aircraft_registry aircraft ON fs.aircraft_id = aircraft.aircraft_id
        WHERE fs.actual_departure >= CURRENT_DATE - INTERVAL '1 day'
    )
    INSERT INTO dbx_analytics.daily_summaries (
        summary_date, total_flights, total_organizations, active_aircraft,
        avg_risk_score, high_risk_flights, anomalies_detected, 
        system_health_score, maintenance_due
    )
    SELECT 
        summary_date, 
        COALESCE(total_flights, 0), 
        COALESCE(total_orgs, 0),
        COALESCE(active_aircraft, 0),
        ROUND(COALESCE(avg_risk, 0), 4), 
        COALESCE(high_risk, 0),
        COALESCE(anomalies, 0),
        ROUND(COALESCE(health_score, 100), 2),
        COALESCE(maint_due, 0)
    FROM daily_metrics
    ON CONFLICT (summary_date) DO UPDATE SET
        total_flights = EXCLUDED.total_flights,
        total_organizations = EXCLUDED.total_organizations,
        active_aircraft = EXCLUDED.active_aircraft,
        avg_risk_score = EXCLUDED.avg_risk_score,
        high_risk_flights = EXCLUDED.high_risk_flights,
        anomalies_detected = EXCLUDED.anomalies_detected,
        system_health_score = EXCLUDED.system_health_score,
        maintenance_due = EXCLUDED.maintenance_due;
    
    RAISE NOTICE 'Daily analytics summary generated for %', CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old data
CREATE OR REPLACE FUNCTION dbx_analytics.cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Archive old telemetry data (older than 90 days)
    WITH archived AS (
        DELETE FROM dbx_aviation.flight_telemetry 
        WHERE timestamp < CURRENT_DATE - INTERVAL '90 days'
        RETURNING *
    )
    INSERT INTO dbx_archive.flight_telemetry_archive 
    SELECT * FROM archived;
    
    -- Clean up old API request logs (older than 1 year)
    DELETE FROM dbx_aviation.api_requests 
    WHERE request_timestamp < CURRENT_DATE - INTERVAL '1 year';
    
    -- Clean up old audit logs (older than 2 years, except compliance-relevant)
    DELETE FROM dbx_audit.audit_log 
    WHERE timestamp < CURRENT_DATE - INTERVAL '2 years'
    AND compliance_relevant = false;
    
    RAISE NOTICE 'Old data cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Schedule daily analytics (requires pg_cron extension)
-- SELECT cron.schedule('daily-analytics', '0 6 * * *', 'SELECT dbx_analytics.generate_daily_summary()');
-- SELECT cron.schedule('weekly-cleanup', '0 2 * * 0', 'SELECT dbx_analytics.cleanup_old_data()');

-- ============================================
-- PERFORMANCE OPTIMIZATION
-- ============================================

-- Create materialized view for expensive fleet analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS dbx_analytics.fleet_performance_summary AS
SELECT 
    o.org_id,
    o.org_name,
    ar.aircraft_type,
    COUNT(DISTINCT ar.aircraft_id) as aircraft_count,
    COUNT(DISTINCT fs.session_id) as total_flights,
    AVG(fs.flight_duration_seconds) as avg_flight_duration,
    AVG(mar.risk_score) as avg_risk_score,
    COUNT(*) FILTER (WHERE mar.anomaly_detected) as total_anomalies,
    SUM(ar.total_flight_hours) as total_fleet_hours,
    MAX(fs.actual_departure) as last_flight_date
FROM dbx_aviation.organizations o
JOIN dbx_aviation.aircraft_registry ar ON o.org_id = ar.org_id
LEFT JOIN dbx_aviation.flight_sessions fs ON ar.aircraft_id = fs.aircraft_id
LEFT JOIN dbx_aviation.ml_analysis_results mar ON fs.session_id = mar.session_id
WHERE o.is_active = true AND ar.is_active = true
GROUP BY o.org_id, o.org_name, ar.aircraft_type;

-- Create index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_fleet_perf_summary_unique 
ON dbx_analytics.fleet_performance_summary (org_id, aircraft_type);

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION dbx_analytics.refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY dbx_analytics.fleet_performance_summary;
    RAISE NOTICE 'Materialized views refreshed';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Advanced Analytics Functions Installed Successfully!';
    RAISE NOTICE '✅ Fleet risk profiling functions';
    RAISE NOTICE '✅ Anomaly pattern analysis';
    RAISE NOTICE '✅ Predictive maintenance scoring';
    RAISE NOTICE '✅ Executive reporting views';
    RAISE NOTICE '✅ Real-time fleet status monitoring';
    RAISE NOTICE '✅ System health dashboards';
    RAISE NOTICE '✅ Automated daily analytics';
    RAISE NOTICE '✅ Performance optimization with materialized views';
    RAISE NOTICE '';
    RAISE NOTICE 'Available Functions:';
    RAISE NOTICE '  • dbx_analytics.calculate_fleet_risk_profile(org_id, start_date, end_date)';
    RAISE NOTICE '  • dbx_analytics.analyze_anomaly_patterns(aircraft_id, org_id, days_back)';
    RAISE NOTICE '  • dbx_analytics.calculate_maintenance_score(aircraft_id, org_id)';
    RAISE NOTICE '  • dbx_analytics.generate_daily_summary()';
    RAISE NOTICE '';
    RAISE NOTICE 'Available Views:';
    RAISE NOTICE '  • dbx_analytics.executive_summary';
    RAISE NOTICE '  • dbx_analytics.fleet_status';
    RAISE NOTICE '  • dbx_analytics.system_health';
    RAISE NOTICE '  • dbx_analytics.fleet_performance_summary (materialized)';
END $$;