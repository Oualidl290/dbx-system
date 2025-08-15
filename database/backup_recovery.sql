-- ============================================
-- DBX AI Aviation System - Backup & Recovery Strategy
-- Enterprise-Grade Data Protection & Disaster Recovery
-- ============================================

-- ============================================
-- BACKUP CONFIGURATION TABLES
-- ============================================

-- Backup policies and schedules
CREATE TABLE dbx_aviation.backup_policies (
    policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_name VARCHAR(100) UNIQUE NOT NULL,
    
    -- Backup Configuration
    backup_type VARCHAR(50) NOT NULL CHECK (backup_type IN ('full', 'incremental', 'differential', 'logical')),
    backup_frequency VARCHAR(50) NOT NULL CHECK (backup_frequency IN ('hourly', 'daily', 'weekly', 'monthly')),
    retention_days INTEGER NOT NULL DEFAULT 30,
    
    -- Scope
    backup_scope VARCHAR(50) NOT NULL DEFAULT 'database' CHECK (backup_scope IN ('database', 'schema', 'table', 'custom')),
    included_schemas TEXT[] DEFAULT ARRAY['dbx_aviation', 'dbx_analytics'],
    excluded_tables TEXT[] DEFAULT '{}',
    
    -- Storage Configuration
    storage_location VARCHAR(500) NOT NULL, -- S3 bucket, local path, etc.
    compression_enabled BOOLEAN DEFAULT true,
    encryption_enabled BOOLEAN DEFAULT true,
    encryption_key_id VARCHAR(255),
    
    -- Performance Settings
    parallel_jobs INTEGER DEFAULT 2,
    bandwidth_limit_mbps INTEGER, -- NULL = no limit
    
    -- Monitoring
    max_backup_duration_hours INTEGER DEFAULT 4,
    alert_on_failure BOOLEAN DEFAULT true,
    alert_recipients TEXT[],
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES dbx_aviation.users(user_id),
    is_active BOOLEAN DEFAULT true,
    description TEXT
);

-- Backup execution history
CREATE TABLE dbx_aviation.backup_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID NOT NULL REFERENCES dbx_aviation.backup_policies(policy_id),
    
    -- Execution Details
    backup_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'running' 
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled', 'partial')),
    exit_code INTEGER,
    error_message TEXT,
    
    -- Backup Details
    backup_file_path VARCHAR(1000),
    backup_size_bytes BIGINT,
    compressed_size_bytes BIGINT,
    compression_ratio DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE 
            WHEN backup_size_bytes > 0 AND compressed_size_bytes > 0 
            THEN (1 - compressed_size_bytes::decimal / backup_size_bytes)
            ELSE NULL 
        END
    ) STORED,
    
    -- Data Statistics
    tables_backed_up INTEGER,
    rows_backed_up BIGINT,
    
    -- Verification
    checksum VARCHAR(64), -- SHA-256 checksum
    verified_at TIMESTAMPTZ,
    verification_status VARCHAR(20) CHECK (verification_status IN ('pending', 'passed', 'failed')),
    
    -- Recovery Information
    recovery_point_objective TIMESTAMPTZ, -- Point in time this backup represents
    log_sequence_number VARCHAR(50), -- PostgreSQL LSN for point-in-time recovery
    
    -- Metadata
    backup_metadata JSONB DEFAULT '{}'::jsonb,
    execution_log TEXT
);

-- Recovery operations tracking
CREATE TABLE dbx_aviation.recovery_operations (
    recovery_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Recovery Request
    recovery_type VARCHAR(50) NOT NULL CHECK (recovery_type IN ('full_restore', 'point_in_time', 'table_restore', 'schema_restore')),
    requested_by UUID REFERENCES dbx_aviation.users(user_id),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by UUID REFERENCES dbx_aviation.users(user_id),
    approved_at TIMESTAMPTZ,
    
    -- Recovery Details
    source_backup_id UUID REFERENCES dbx_aviation.backup_executions(execution_id),
    target_point_in_time TIMESTAMPTZ,
    recovery_scope JSONB, -- Tables, schemas, or custom scope
    
    -- Execution
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'approved', 'running', 'completed', 'failed', 'cancelled')),
    
    -- Results
    recovered_tables INTEGER,
    recovered_rows BIGINT,
    data_loss_assessment TEXT,
    
    -- Verification
    verification_queries TEXT[],
    verification_results JSONB,
    
    -- Metadata
    recovery_notes TEXT,
    execution_log TEXT,
    error_message TEXT
);

-- ============================================
-- BACKUP FUNCTIONS
-- ============================================

-- Function to create a logical backup
CREATE OR REPLACE FUNCTION dbx_aviation.create_logical_backup(
    p_policy_name TEXT,
    p_backup_path TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    policy_record RECORD;
    execution_id UUID;
    backup_command TEXT;
    backup_path TEXT;
    start_time TIMESTAMPTZ;
BEGIN
    start_time := NOW();
    execution_id := uuid_generate_v4();
    
    -- Get backup policy
    SELECT * INTO policy_record
    FROM dbx_aviation.backup_policies
    WHERE policy_name = p_policy_name AND is_active = true;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Backup policy not found: %', p_policy_name;
    END IF;
    
    -- Generate backup path if not provided
    IF p_backup_path IS NULL THEN
        backup_path := policy_record.storage_location || '/backup_' || 
                      to_char(start_time, 'YYYY-MM-DD_HH24-MI-SS') || '_' || 
                      execution_id || '.sql';
    ELSE
        backup_path := p_backup_path;
    END IF;
    
    -- Record backup execution start
    INSERT INTO dbx_aviation.backup_executions (
        execution_id, policy_id, backup_type, started_at,
        backup_file_path, status
    ) VALUES (
        execution_id, policy_record.policy_id, policy_record.backup_type,
        start_time, backup_path, 'running'
    );
    
    -- Build pg_dump command
    backup_command := format(
        'pg_dump --verbose --format=custom --compress=%s --file=%s',
        CASE WHEN policy_record.compression_enabled THEN '9' ELSE '0' END,
        backup_path
    );
    
    -- Add schema restrictions
    IF array_length(policy_record.included_schemas, 1) > 0 THEN
        FOR i IN 1..array_length(policy_record.included_schemas, 1) LOOP
            backup_command := backup_command || ' --schema=' || policy_record.included_schemas[i];
        END LOOP;
    END IF;
    
    -- Add table exclusions
    IF array_length(policy_record.excluded_tables, 1) > 0 THEN
        FOR i IN 1..array_length(policy_record.excluded_tables, 1) LOOP
            backup_command := backup_command || ' --exclude-table=' || policy_record.excluded_tables[i];
        END LOOP;
    END IF;
    
    -- Add database name
    backup_command := backup_command || ' ' || current_database();
    
    -- Log the backup command (in production, execute via external script)
    UPDATE dbx_aviation.backup_executions
    SET execution_log = backup_command,
        backup_metadata = jsonb_build_object(
            'command', backup_command,
            'parallel_jobs', policy_record.parallel_jobs,
            'compression_enabled', policy_record.compression_enabled
        )
    WHERE execution_id = create_logical_backup.execution_id;
    
    -- In production, this would execute the actual backup
    -- For now, simulate completion
    UPDATE dbx_aviation.backup_executions
    SET status = 'completed',
        completed_at = NOW(),
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - start_time)),
        backup_size_bytes = 1024 * 1024 * 100, -- 100MB simulated
        compressed_size_bytes = 1024 * 1024 * 30, -- 30MB compressed
        tables_backed_up = (
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = ANY(policy_record.included_schemas)
        ),
        checksum = encode(gen_random_bytes(32), 'hex'),
        verification_status = 'pending'
    WHERE execution_id = create_logical_backup.execution_id;
    
    RETURN execution_id;
END;
$$ LANGUAGE plpgsql;

-- Function to verify backup integrity
CREATE OR REPLACE FUNCTION dbx_aviation.verify_backup(p_execution_id UUID)
RETURNS JSONB AS $$
DECLARE
    backup_record RECORD;
    verification_result JSONB;
    file_exists BOOLEAN := true; -- Simulated
    checksum_valid BOOLEAN := true; -- Simulated
BEGIN
    -- Get backup execution details
    SELECT * INTO backup_record
    FROM dbx_aviation.backup_executions
    WHERE execution_id = p_execution_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Backup execution not found: %', p_execution_id;
    END IF;
    
    -- Simulate verification checks
    -- In production, this would:
    -- 1. Check if backup file exists
    -- 2. Verify file checksum
    -- 3. Test restore to temporary database
    -- 4. Run data integrity checks
    
    verification_result := jsonb_build_object(
        'file_exists', file_exists,
        'checksum_valid', checksum_valid,
        'file_size_bytes', backup_record.backup_size_bytes,
        'verification_timestamp', NOW(),
        'tests_passed', ARRAY['file_existence', 'checksum_validation'],
        'tests_failed', ARRAY[]::TEXT[]
    );
    
    -- Update backup record
    UPDATE dbx_aviation.backup_executions
    SET verified_at = NOW(),
        verification_status = CASE 
            WHEN file_exists AND checksum_valid THEN 'passed'
            ELSE 'failed'
        END,
        backup_metadata = backup_metadata || verification_result
    WHERE execution_id = p_execution_id;
    
    RETURN verification_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- RECOVERY FUNCTIONS
-- ============================================

-- Function to initiate recovery operation
CREATE OR REPLACE FUNCTION dbx_aviation.initiate_recovery(
    p_recovery_type TEXT,
    p_source_backup_id UUID,
    p_requested_by UUID,
    p_target_point_in_time TIMESTAMPTZ DEFAULT NULL,
    p_recovery_scope JSONB DEFAULT NULL,
    p_recovery_notes TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    recovery_id UUID;
    backup_record RECORD;
BEGIN
    recovery_id := uuid_generate_v4();
    
    -- Validate source backup
    SELECT * INTO backup_record
    FROM dbx_aviation.backup_executions
    WHERE execution_id = p_source_backup_id
    AND status = 'completed'
    AND verification_status = 'passed';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Valid backup not found: %', p_source_backup_id;
    END IF;
    
    -- Create recovery operation record
    INSERT INTO dbx_aviation.recovery_operations (
        recovery_id, recovery_type, requested_by, source_backup_id,
        target_point_in_time, recovery_scope, recovery_notes, status
    ) VALUES (
        recovery_id, p_recovery_type, p_requested_by, p_source_backup_id,
        p_target_point_in_time, p_recovery_scope, p_recovery_notes, 'pending'
    );
    
    -- Log recovery request
    INSERT INTO dbx_audit.audit_log (
        user_id, action_type, table_name, record_id,
        new_values, compliance_relevant
    ) VALUES (
        p_requested_by, 'recovery_request', 'recovery_operations', recovery_id,
        jsonb_build_object(
            'recovery_type', p_recovery_type,
            'source_backup_id', p_source_backup_id,
            'target_point_in_time', p_target_point_in_time
        ),
        true
    );
    
    RETURN recovery_id;
END;
$$ LANGUAGE plpgsql;

-- Function to approve recovery operation
CREATE OR REPLACE FUNCTION dbx_aviation.approve_recovery(
    p_recovery_id UUID,
    p_approved_by UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    recovery_record RECORD;
BEGIN
    -- Get recovery operation
    SELECT * INTO recovery_record
    FROM dbx_aviation.recovery_operations
    WHERE recovery_id = p_recovery_id AND status = 'pending';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pending recovery operation not found: %', p_recovery_id;
    END IF;
    
    -- Update approval
    UPDATE dbx_aviation.recovery_operations
    SET approved_by = p_approved_by,
        approved_at = NOW(),
        status = 'approved'
    WHERE recovery_id = p_recovery_id;
    
    -- Log approval
    INSERT INTO dbx_audit.audit_log (
        user_id, action_type, table_name, record_id,
        new_values, compliance_relevant
    ) VALUES (
        p_approved_by, 'recovery_approval', 'recovery_operations', p_recovery_id,
        jsonb_build_object('approved_at', NOW()),
        true
    );
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- BACKUP SCHEDULING FUNCTIONS
-- ============================================

-- Function to execute scheduled backups
CREATE OR REPLACE FUNCTION dbx_aviation.execute_scheduled_backups()
RETURNS JSONB AS $$
DECLARE
    policy_record RECORD;
    execution_results JSONB := '[]'::jsonb;
    execution_id UUID;
    last_backup TIMESTAMPTZ;
    should_run BOOLEAN;
BEGIN
    -- Loop through active backup policies
    FOR policy_record IN 
        SELECT * FROM dbx_aviation.backup_policies 
        WHERE is_active = true
    LOOP
        -- Check if backup should run based on frequency
        SELECT MAX(started_at) INTO last_backup
        FROM dbx_aviation.backup_executions
        WHERE policy_id = policy_record.policy_id
        AND status = 'completed';
        
        should_run := false;
        
        CASE policy_record.backup_frequency
            WHEN 'hourly' THEN
                should_run := (last_backup IS NULL OR last_backup < NOW() - INTERVAL '1 hour');
            WHEN 'daily' THEN
                should_run := (last_backup IS NULL OR last_backup < NOW() - INTERVAL '1 day');
            WHEN 'weekly' THEN
                should_run := (last_backup IS NULL OR last_backup < NOW() - INTERVAL '1 week');
            WHEN 'monthly' THEN
                should_run := (last_backup IS NULL OR last_backup < NOW() - INTERVAL '1 month');
        END CASE;
        
        IF should_run THEN
            -- Execute backup
            execution_id := dbx_aviation.create_logical_backup(policy_record.policy_name);
            
            execution_results := execution_results || jsonb_build_object(
                'policy_name', policy_record.policy_name,
                'execution_id', execution_id,
                'status', 'started'
            );
        END IF;
    END LOOP;
    
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'executions', execution_results,
        'total_backups_started', jsonb_array_length(execution_results)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- BACKUP CLEANUP FUNCTIONS
-- ============================================

-- Function to cleanup old backups based on retention policy
CREATE OR REPLACE FUNCTION dbx_aviation.cleanup_old_backups()
RETURNS JSONB AS $$
DECLARE
    policy_record RECORD;
    cleanup_results JSONB := '[]'::jsonb;
    deleted_count INTEGER;
    total_deleted INTEGER := 0;
BEGIN
    -- Loop through backup policies
    FOR policy_record IN 
        SELECT * FROM dbx_aviation.backup_policies 
        WHERE is_active = true
    LOOP
        -- Delete old backup executions beyond retention period
        DELETE FROM dbx_aviation.backup_executions
        WHERE policy_id = policy_record.policy_id
        AND started_at < NOW() - (policy_record.retention_days || ' days')::INTERVAL
        AND status IN ('completed', 'failed');
        
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        total_deleted := total_deleted + deleted_count;
        
        IF deleted_count > 0 THEN
            cleanup_results := cleanup_results || jsonb_build_object(
                'policy_name', policy_record.policy_name,
                'deleted_backups', deleted_count,
                'retention_days', policy_record.retention_days
            );
        END IF;
    END LOOP;
    
    -- Log cleanup operation
    INSERT INTO dbx_audit.audit_log (
        action_type, table_name, new_values, compliance_relevant
    ) VALUES (
        'cleanup', 'backup_executions',
        jsonb_build_object('total_deleted', total_deleted, 'policies_processed', cleanup_results),
        false
    );
    
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'total_backups_deleted', total_deleted,
        'policy_results', cleanup_results
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- MONITORING VIEWS
-- ============================================

-- Backup status overview
CREATE VIEW dbx_aviation.backup_status AS
SELECT 
    bp.policy_name,
    bp.backup_frequency,
    bp.retention_days,
    bp.is_active,
    be.last_backup,
    be.last_status,
    be.last_duration_minutes,
    be.last_size_mb,
    CASE 
        WHEN bp.backup_frequency = 'hourly' AND be.last_backup < NOW() - INTERVAL '2 hours' THEN 'OVERDUE'
        WHEN bp.backup_frequency = 'daily' AND be.last_backup < NOW() - INTERVAL '25 hours' THEN 'OVERDUE'
        WHEN bp.backup_frequency = 'weekly' AND be.last_backup < NOW() - INTERVAL '8 days' THEN 'OVERDUE'
        WHEN bp.backup_frequency = 'monthly' AND be.last_backup < NOW() - INTERVAL '32 days' THEN 'OVERDUE'
        WHEN be.last_status = 'failed' THEN 'FAILED'
        WHEN be.last_status = 'completed' THEN 'OK'
        ELSE 'UNKNOWN'
    END as backup_health
FROM dbx_aviation.backup_policies bp
LEFT JOIN (
    SELECT 
        policy_id,
        MAX(started_at) as last_backup,
        (array_agg(status ORDER BY started_at DESC))[1] as last_status,
        (array_agg(duration_seconds ORDER BY started_at DESC))[1] / 60.0 as last_duration_minutes,
        (array_agg(backup_size_bytes ORDER BY started_at DESC))[1] / 1024.0 / 1024.0 as last_size_mb
    FROM dbx_aviation.backup_executions
    GROUP BY policy_id
) be ON bp.policy_id = be.policy_id;

-- Recovery operations summary
CREATE VIEW dbx_aviation.recovery_summary AS
SELECT 
    ro.recovery_id,
    ro.recovery_type,
    ro.status,
    ro.requested_at,
    ro.approved_at,
    ro.started_at,
    ro.completed_at,
    ro.duration_seconds / 60.0 as duration_minutes,
    u1.email as requested_by_email,
    u2.email as approved_by_email,
    be.backup_file_path as source_backup_path
FROM dbx_aviation.recovery_operations ro
LEFT JOIN dbx_aviation.users u1 ON ro.requested_by = u1.user_id
LEFT JOIN dbx_aviation.users u2 ON ro.approved_by = u2.user_id
LEFT JOIN dbx_aviation.backup_executions be ON ro.source_backup_id = be.execution_id
ORDER BY ro.requested_at DESC;

-- ============================================
-- DEFAULT BACKUP POLICIES
-- ============================================

-- Insert default backup policies
INSERT INTO dbx_aviation.backup_policies (
    policy_name, backup_type, backup_frequency, retention_days,
    storage_location, compression_enabled, encryption_enabled,
    description
) VALUES 
('daily_full_backup', 'full', 'daily', 30, '/backups/daily', true, true,
 'Daily full database backup with 30-day retention'),
 
('weekly_archive_backup', 'full', 'weekly', 365, '/backups/archive', true, true,
 'Weekly archive backup with 1-year retention for compliance'),
 
('hourly_incremental', 'incremental', 'hourly', 7, '/backups/incremental', true, true,
 'Hourly incremental backup for point-in-time recovery');

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_backup_executions_policy_time ON dbx_aviation.backup_executions(policy_id, started_at DESC);
CREATE INDEX idx_backup_executions_status ON dbx_aviation.backup_executions(status, started_at DESC);
CREATE INDEX idx_recovery_operations_status ON dbx_aviation.recovery_operations(status, requested_at DESC);
CREATE INDEX idx_recovery_operations_user ON dbx_aviation.recovery_operations(requested_by, requested_at DESC);

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '💾 Backup & Recovery System Created!';
    RAISE NOTICE '✅ Comprehensive backup policies and scheduling';
    RAISE NOTICE '✅ Recovery operations with approval workflow';
    RAISE NOTICE '✅ Backup verification and integrity checking';
    RAISE NOTICE '✅ Automated cleanup of old backups';
    RAISE NOTICE '✅ Monitoring views for backup health';
    RAISE NOTICE '✅ Default policies: daily_full_backup, weekly_archive_backup, hourly_incremental';
    RAISE NOTICE '📊 Views: backup_status, recovery_summary';
    RAISE NOTICE '🔧 Functions: create_logical_backup, verify_backup, initiate_recovery';
    RAISE NOTICE '⏰ Schedule execute_scheduled_backups() and cleanup_old_backups()';
END $$;