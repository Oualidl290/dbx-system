-- ============================================
-- DATA LIFECYCLE MANAGEMENT: Archival, Retention & Backup
-- ============================================

-- Create archive schema and tables
CREATE SCHEMA IF NOT EXISTS dbx_archive;

-- ============================================
-- ARCHIVE TABLES
-- ============================================

-- Archive table for old telemetry data
CREATE TABLE IF NOT EXISTS dbx_archive.flight_telemetry_archive (
    LIKE dbx_aviation.flight_telemetry INCLUDING ALL
);

-- Archive table for old flight sessions
CREATE TABLE IF NOT EXISTS dbx_archive.flight_sessions_archive (
    LIKE dbx_aviation.flight_sessions INCLUDING ALL
);

-- Archive table for old analysis results
CREATE TABLE IF NOT EXISTS dbx_archive.ml_analysis_results_archive (
    LIKE dbx_aviation.ml_analysis_results INCLUDING ALL
);

-- Archive table for old API requests
CREATE TABLE IF NOT EXISTS dbx_archive.api_requests_archive (
    LIKE dbx_aviation.api_requests INCLUDING ALL
);

-- Add archival metadata
ALTER TABLE dbx_archive.flight_telemetry_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE dbx_archive.flight_sessions_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE dbx_archive.ml_analysis_results_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ DEFAULT NOW();

ALTER TABLE dbx_archive.api_requests_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ DEFAULT NOW();

-- ============================================
-- ARCHIVAL FUNCTIONS
-- ============================================

-- Function to archive old telemetry data
CREATE OR REPLACE FUNCTION dbx_aviation.archive_old_telemetry(
    p_days_old INTEGER DEFAULT 90
)
RETURNS TABLE (
    archived_records BIGINT,
    oldest_archived TIMESTAMPTZ,
    newest_archived TIMESTAMPTZ
) AS $$
DECLARE
    archive_date TIMESTAMPTZ;
    archived_count BIGINT;
    oldest_record TIMESTAMPTZ;
    newest_record TIMESTAMPTZ;
BEGIN
    archive_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_old;
    
    -- Get statistics before archiving
    SELECT MIN(timestamp), MAX(timestamp), COUNT(*)
    INTO oldest_record, newest_record, archived_count
    FROM dbx_aviation.flight_telemetry
    WHERE timestamp < archive_date;
    
    -- Move to archive schema with compression
    INSERT INTO dbx_archive.flight_telemetry_archive
    SELECT *, NOW() as archived_at
    FROM dbx_aviation.flight_telemetry
    WHERE timestamp < archive_date;
    
    -- Delete from main table
    DELETE FROM dbx_aviation.flight_telemetry
    WHERE timestamp < archive_date;
    
    -- Compress archive table (PostgreSQL 14+)
    -- ALTER TABLE dbx_archive.flight_telemetry_archive SET (compression = lz4);
    
    RETURN QUERY SELECT archived_count, oldest_record, newest_record;
    
    RAISE NOTICE 'Archived % telemetry records older than %', archived_count, archive_date;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old flight sessions
CREATE OR REPLACE FUNCTION dbx_aviation.archive_old_flight_sessions(
    p_days_old INTEGER DEFAULT 365
)
RETURNS TABLE (
    archived_records BIGINT,
    oldest_archived TIMESTAMPTZ,
    newest_archived TIMESTAMPTZ
) AS $$
DECLARE
    archive_date TIMESTAMPTZ;
    archived_count BIGINT;
    oldest_record TIMESTAMPTZ;
    newest_record TIMESTAMPTZ;
BEGIN
    archive_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_old;
    
    -- Get statistics before archiving
    SELECT MIN(actual_departure), MAX(actual_departure), COUNT(*)
    INTO oldest_record, newest_record, archived_count
    FROM dbx_aviation.flight_sessions
    WHERE actual_departure < archive_date;
    
    -- Archive related analysis results first
    INSERT INTO dbx_archive.ml_analysis_results_archive
    SELECT mar.*, NOW() as archived_at
    FROM dbx_aviation.ml_analysis_results mar
    JOIN dbx_aviation.flight_sessions fs ON mar.session_id = fs.session_id
    WHERE fs.actual_departure < archive_date;
    
    DELETE FROM dbx_aviation.ml_analysis_results
    WHERE session_id IN (
        SELECT session_id FROM dbx_aviation.flight_sessions
        WHERE actual_departure < archive_date
    );
    
    -- Archive flight sessions
    INSERT INTO dbx_archive.flight_sessions_archive
    SELECT *, NOW() as archived_at
    FROM dbx_aviation.flight_sessions
    WHERE actual_departure < archive_date;
    
    DELETE FROM dbx_aviation.flight_sessions
    WHERE actual_departure < archive_date;
    
    RETURN QUERY SELECT archived_count, oldest_record, newest_record;
    
    RAISE NOTICE 'Archived % flight sessions older than %', archived_count, archive_date;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old API requests
CREATE OR REPLACE FUNCTION dbx_aviation.archive_old_api_requests(
    p_days_old INTEGER DEFAULT 180
)
RETURNS BIGINT AS $$
DECLARE
    archive_date TIMESTAMPTZ;
    archived_count BIGINT;
BEGIN
    archive_date := CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_old;
    
    -- Move to archive
    INSERT INTO dbx_archive.api_requests_archive
    SELECT *, NOW() as archived_at
    FROM dbx_aviation.api_requests
    WHERE request_timestamp < archive_date;
    
    -- Delete from main table
    DELETE FROM dbx_aviation.api_requests
    WHERE request_timestamp < archive_date;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    RAISE NOTICE 'Archived % API requests older than %', archived_count, archive_date;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DATA RETENTION FUNCTIONS
-- ============================================

-- Function to enforce data retention policies per organization
CREATE OR REPLACE FUNCTION dbx_aviation.enforce_retention_policy()
RETURNS TABLE (
    org_code VARCHAR,
    table_name VARCHAR,
    records_deleted BIGINT,
    retention_days INTEGER
) AS $$
DECLARE
    org_record RECORD;
    deleted_count BIGINT;
BEGIN
    FOR org_record IN 
        SELECT org_id, org_code, data_retention_days 
        FROM dbx_aviation.organizations 
        WHERE is_active = true AND data_retention_days IS NOT NULL
    LOOP
        -- Delete old analysis results
        DELETE FROM dbx_aviation.ml_analysis_results
        WHERE org_id = org_record.org_id
            AND created_at < CURRENT_DATE - INTERVAL '1 day' * org_record.data_retention_days;
        
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        IF deleted_count > 0 THEN
            RETURN QUERY SELECT org_record.org_code, 'ml_analysis_results'::VARCHAR, 
                               deleted_count, org_record.data_retention_days;
        END IF;
        
        -- Delete old flight sessions (and cascade to telemetry)
        DELETE FROM dbx_aviation.flight_sessions
        WHERE org_id = org_record.org_id
            AND created_at < CURRENT_DATE - INTERVAL '1 day' * org_record.data_retention_days;
        
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        IF deleted_count > 0 THEN
            RETURN QUERY SELECT org_record.org_code, 'flight_sessions'::VARCHAR, 
                               deleted_count, org_record.data_retention_days;
        END IF;
        
        -- Delete old API requests
        DELETE FROM dbx_aviation.api_requests
        WHERE org_id = org_record.org_id
            AND request_timestamp < CURRENT_DATE - INTERVAL '1 day' * org_record.data_retention_days;
        
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        IF deleted_count > 0 THEN
            RETURN QUERY SELECT org_record.org_code, 'api_requests'::VARCHAR, 
                               deleted_count, org_record.data_retention_days;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to check retention compliance
CREATE OR REPLACE FUNCTION dbx_aviation.check_retention_compliance()
RETURNS TABLE (
    org_code VARCHAR,
    table_name VARCHAR,
    records_to_delete BIGINT,
    oldest_record TIMESTAMPTZ,
    retention_days INTEGER,
    compliance_status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH retention_check AS (
        -- Check flight sessions
        SELECT 
            o.org_code,
            'flight_sessions' as table_name,
            COUNT(*) as records_to_delete,
            MIN(fs.created_at) as oldest_record,
            o.data_retention_days,
            CASE 
                WHEN COUNT(*) = 0 THEN 'COMPLIANT'
                WHEN MIN(fs.created_at) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 30) THEN 'CRITICAL'
                WHEN MIN(fs.created_at) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 7) THEN 'WARNING'
                ELSE 'ATTENTION_NEEDED'
            END as status
        FROM dbx_aviation.organizations o
        LEFT JOIN dbx_aviation.flight_sessions fs ON o.org_id = fs.org_id
            AND fs.created_at < CURRENT_DATE - INTERVAL '1 day' * o.data_retention_days
        WHERE o.is_active = true AND o.data_retention_days IS NOT NULL
        GROUP BY o.org_code, o.data_retention_days
        
        UNION ALL
        
        -- Check ML analysis results
        SELECT 
            o.org_code,
            'ml_analysis_results' as table_name,
            COUNT(*) as records_to_delete,
            MIN(mar.created_at) as oldest_record,
            o.data_retention_days,
            CASE 
                WHEN COUNT(*) = 0 THEN 'COMPLIANT'
                WHEN MIN(mar.created_at) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 30) THEN 'CRITICAL'
                WHEN MIN(mar.created_at) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 7) THEN 'WARNING'
                ELSE 'ATTENTION_NEEDED'
            END as status
        FROM dbx_aviation.organizations o
        LEFT JOIN dbx_aviation.ml_analysis_results mar ON o.org_id = mar.org_id
            AND mar.created_at < CURRENT_DATE - INTERVAL '1 day' * o.data_retention_days
        WHERE o.is_active = true AND o.data_retention_days IS NOT NULL
        GROUP BY o.org_code, o.data_retention_days
        
        UNION ALL
        
        -- Check API requests
        SELECT 
            o.org_code,
            'api_requests' as table_name,
            COUNT(*) as records_to_delete,
            MIN(ar.request_timestamp) as oldest_record,
            o.data_retention_days,
            CASE 
                WHEN COUNT(*) = 0 THEN 'COMPLIANT'
                WHEN MIN(ar.request_timestamp) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 30) THEN 'CRITICAL'
                WHEN MIN(ar.request_timestamp) < CURRENT_DATE - INTERVAL '1 day' * (o.data_retention_days + 7) THEN 'WARNING'
                ELSE 'ATTENTION_NEEDED'
            END as status
        FROM dbx_aviation.organizations o
        LEFT JOIN dbx_aviation.api_requests ar ON o.org_id = ar.org_id
            AND ar.request_timestamp < CURRENT_DATE - INTERVAL '1 day' * o.data_retention_days
        WHERE o.is_active = true AND o.data_retention_days IS NOT NULL
        GROUP BY o.org_code, o.data_retention_days
    )
    SELECT * FROM retention_check 
    WHERE records_to_delete > 0 OR compliance_status != 'COMPLIANT'
    ORDER BY 
        CASE compliance_status 
            WHEN 'CRITICAL' THEN 1 
            WHEN 'WARNING' THEN 2 
            WHEN 'ATTENTION_NEEDED' THEN 3 
            ELSE 4 
        END,
        org_code, table_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- BACKUP FUNCTIONS
-- ============================================

-- Function to create logical backup metadata
CREATE OR REPLACE FUNCTION dbx_aviation.create_backup_metadata(
    p_backup_type VARCHAR DEFAULT 'full',
    p_backup_location VARCHAR DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    backup_id UUID;
    table_stats RECORD;
BEGIN
    -- Create backup metadata table if not exists
    CREATE TABLE IF NOT EXISTS dbx_aviation.backup_metadata (
        backup_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        backup_type VARCHAR NOT NULL,
        backup_location VARCHAR,
        backup_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        database_size BIGINT,
        table_counts JSONB,
        backup_status VARCHAR DEFAULT 'initiated',
        completed_at TIMESTAMPTZ,
        notes TEXT
    );
    
    backup_id := uuid_generate_v4();
    
    -- Collect table statistics
    WITH table_stats AS (
        SELECT 
            schemaname || '.' || tablename as table_name,
            n_tup_ins + n_tup_upd + n_tup_del as total_operations,
            n_live_tup as live_tuples,
            pg_total_relation_size(schemaname||'.'||tablename) as table_size
        FROM pg_stat_user_tables
        WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit')
    )
    INSERT INTO dbx_aviation.backup_metadata (
        backup_id, backup_type, backup_location, database_size, table_counts
    )
    SELECT 
        backup_id,
        p_backup_type,
        p_backup_location,
        pg_database_size(current_database()),
        jsonb_object_agg(table_name, jsonb_build_object(
            'live_tuples', live_tuples,
            'total_operations', total_operations,
            'table_size', table_size
        ))
    FROM table_stats;
    
    RAISE NOTICE 'Backup metadata created with ID: %', backup_id;
    RETURN backup_id;
END;
$$ LANGUAGE plpgsql;

-- Function to mark backup as completed
CREATE OR REPLACE FUNCTION dbx_aviation.complete_backup(
    p_backup_id UUID,
    p_success BOOLEAN DEFAULT TRUE,
    p_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE dbx_aviation.backup_metadata
    SET 
        backup_status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
        completed_at = NOW(),
        notes = p_notes
    WHERE backup_id = p_backup_id;
    
    IF FOUND THEN
        RAISE NOTICE 'Backup % marked as %', p_backup_id, 
                     CASE WHEN p_success THEN 'completed' ELSE 'failed' END;
        RETURN TRUE;
    ELSE
        RAISE WARNING 'Backup ID % not found', p_backup_id;
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- MAINTENANCE FUNCTIONS
-- ============================================

-- Function to analyze table bloat and recommend maintenance
CREATE OR REPLACE FUNCTION dbx_aviation.analyze_table_maintenance()
RETURNS TABLE (
    schema_name VARCHAR,
    table_name VARCHAR,
    table_size TEXT,
    bloat_ratio NUMERIC,
    maintenance_action VARCHAR,
    priority VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH table_stats AS (
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
            n_dead_tup::numeric / GREATEST(n_live_tup, 1) as dead_ratio,
            last_vacuum,
            last_analyze
        FROM pg_stat_user_tables
        WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_archive')
    )
    SELECT 
        schemaname::VARCHAR,
        tablename::VARCHAR,
        size_pretty::TEXT,
        ROUND(dead_ratio * 100, 2) as bloat_ratio,
        CASE 
            WHEN dead_ratio > 0.2 THEN 'VACUUM FULL recommended'
            WHEN dead_ratio > 0.1 THEN 'VACUUM recommended'
            WHEN last_analyze < NOW() - INTERVAL '7 days' THEN 'ANALYZE recommended'
            WHEN last_vacuum < NOW() - INTERVAL '7 days' THEN 'VACUUM recommended'
            ELSE 'No action needed'
        END::VARCHAR as maintenance_action,
        CASE 
            WHEN dead_ratio > 0.3 OR size_bytes > 1073741824 THEN 'HIGH'  -- 1GB
            WHEN dead_ratio > 0.1 OR size_bytes > 104857600 THEN 'MEDIUM'  -- 100MB
            ELSE 'LOW'
        END::VARCHAR as priority
    FROM table_stats
    ORDER BY 
        CASE 
            WHEN dead_ratio > 0.3 OR size_bytes > 1073741824 THEN 1
            WHEN dead_ratio > 0.1 OR size_bytes > 104857600 THEN 2
            ELSE 3
        END,
        size_bytes DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to perform automated maintenance
CREATE OR REPLACE FUNCTION dbx_aviation.perform_maintenance(
    p_vacuum_threshold NUMERIC DEFAULT 0.1,
    p_analyze_days INTEGER DEFAULT 7
)
RETURNS TABLE (
    table_name VARCHAR,
    action_taken VARCHAR,
    duration_ms BIGINT
) AS $$
DECLARE
    table_record RECORD;
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    duration_ms BIGINT;
BEGIN
    FOR table_record IN 
        SELECT schemaname, tablename, n_dead_tup::numeric / GREATEST(n_live_tup, 1) as dead_ratio,
               last_analyze
        FROM pg_stat_user_tables
        WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit')
    LOOP
        start_time := clock_timestamp();
        
        -- Vacuum if needed
        IF table_record.dead_ratio > p_vacuum_threshold THEN
            EXECUTE format('VACUUM ANALYZE %I.%I', table_record.schemaname, table_record.tablename);
            end_time := clock_timestamp();
            duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
            
            RETURN QUERY SELECT 
                (table_record.schemaname || '.' || table_record.tablename)::VARCHAR,
                'VACUUM ANALYZE'::VARCHAR,
                duration_ms::BIGINT;
                
        -- Analyze if needed
        ELSIF table_record.last_analyze < NOW() - INTERVAL '1 day' * p_analyze_days THEN
            EXECUTE format('ANALYZE %I.%I', table_record.schemaname, table_record.tablename);
            end_time := clock_timestamp();
            duration_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
            
            RETURN QUERY SELECT 
                (table_record.schemaname || '.' || table_record.tablename)::VARCHAR,
                'ANALYZE'::VARCHAR,
                duration_ms::BIGINT;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SCHEDULED JOBS SETUP
-- ============================================

-- Note: These require pg_cron extension to be installed and configured
-- Uncomment and modify as needed for your environment

/*
-- Schedule daily archival of old telemetry data (90+ days old)
SELECT cron.schedule('archive-telemetry', '0 2 * * *', 
    'SELECT dbx_aviation.archive_old_telemetry(90)');

-- Schedule weekly archival of old flight sessions (1+ year old)
SELECT cron.schedule('archive-flights', '0 3 * * 0', 
    'SELECT dbx_aviation.archive_old_flight_sessions(365)');

-- Schedule monthly archival of old API requests (6+ months old)
SELECT cron.schedule('archive-api-requests', '0 4 1 * *', 
    'SELECT dbx_aviation.archive_old_api_requests(180)');

-- Schedule daily retention policy enforcement
SELECT cron.schedule('enforce-retention', '0 5 * * *', 
    'SELECT dbx_aviation.enforce_retention_policy()');

-- Schedule weekly maintenance
SELECT cron.schedule('weekly-maintenance', '0 1 * * 0', 
    'SELECT dbx_aviation.perform_maintenance()');

-- Schedule monthly backup metadata cleanup (keep 1 year)
SELECT cron.schedule('cleanup-backup-metadata', '0 6 1 * *', 
    'DELETE FROM dbx_aviation.backup_metadata WHERE backup_timestamp < NOW() - INTERVAL ''1 year''');
*/

-- ============================================
-- MONITORING VIEWS
-- ============================================

-- View for data lifecycle monitoring
CREATE OR REPLACE VIEW dbx_aviation.data_lifecycle_status AS
WITH table_ages AS (
    SELECT 
        'flight_sessions' as table_name,
        COUNT(*) as total_records,
        MIN(created_at) as oldest_record,
        MAX(created_at) as newest_record,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '90 days') as old_records_90d,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '365 days') as old_records_1y
    FROM dbx_aviation.flight_sessions
    
    UNION ALL
    
    SELECT 
        'flight_telemetry' as table_name,
        COUNT(*) as total_records,
        MIN(timestamp) as oldest_record,
        MAX(timestamp) as newest_record,
        COUNT(*) FILTER (WHERE timestamp < CURRENT_DATE - INTERVAL '90 days') as old_records_90d,
        COUNT(*) FILTER (WHERE timestamp < CURRENT_DATE - INTERVAL '365 days') as old_records_1y
    FROM dbx_aviation.flight_telemetry
    
    UNION ALL
    
    SELECT 
        'ml_analysis_results' as table_name,
        COUNT(*) as total_records,
        MIN(created_at) as oldest_record,
        MAX(created_at) as newest_record,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '90 days') as old_records_90d,
        COUNT(*) FILTER (WHERE created_at < CURRENT_DATE - INTERVAL '365 days') as old_records_1y
    FROM dbx_aviation.ml_analysis_results
    
    UNION ALL
    
    SELECT 
        'api_requests' as table_name,
        COUNT(*) as total_records,
        MIN(request_timestamp) as oldest_record,
        MAX(request_timestamp) as newest_record,
        COUNT(*) FILTER (WHERE request_timestamp < CURRENT_DATE - INTERVAL '90 days') as old_records_90d,
        COUNT(*) FILTER (WHERE request_timestamp < CURRENT_DATE - INTERVAL '365 days') as old_records_1y
    FROM dbx_aviation.api_requests
)
SELECT 
    table_name,
    total_records,
    oldest_record,
    newest_record,
    old_records_90d,
    old_records_1y,
    CASE 
        WHEN old_records_1y > total_records * 0.5 THEN 'ARCHIVAL_NEEDED'
        WHEN old_records_90d > total_records * 0.3 THEN 'ARCHIVAL_RECOMMENDED'
        ELSE 'OK'
    END as archival_status,
    pg_size_pretty(pg_total_relation_size('dbx_aviation.' || table_name)) as table_size
FROM table_ages;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Data Lifecycle Management Functions Installed Successfully!';
    RAISE NOTICE '✅ Automated archival functions';
    RAISE NOTICE '✅ Data retention policy enforcement';
    RAISE NOTICE '✅ Backup metadata tracking';
    RAISE NOTICE '✅ Table maintenance analysis';
    RAISE NOTICE '✅ Lifecycle monitoring views';
    RAISE NOTICE '';
    RAISE NOTICE 'Available Functions:';
    RAISE NOTICE '  • dbx_aviation.archive_old_telemetry(days_old)';
    RAISE NOTICE '  • dbx_aviation.archive_old_flight_sessions(days_old)';
    RAISE NOTICE '  • dbx_aviation.enforce_retention_policy()';
    RAISE NOTICE '  • dbx_aviation.check_retention_compliance()';
    RAISE NOTICE '  • dbx_aviation.create_backup_metadata(type, location)';
    RAISE NOTICE '  • dbx_aviation.analyze_table_maintenance()';
    RAISE NOTICE '  • dbx_aviation.perform_maintenance()';
    RAISE NOTICE '';
    RAISE NOTICE 'Available Views:';
    RAISE NOTICE '  • dbx_aviation.data_lifecycle_status';
    RAISE NOTICE '';
    RAISE NOTICE 'Note: Uncomment pg_cron jobs in the file to enable automated scheduling';
END $$;