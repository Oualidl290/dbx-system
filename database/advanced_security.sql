-- ============================================
-- ADVANCED SECURITY: Row Level Security & Encryption
-- ============================================

-- Enable Row Level Security on sensitive tables
ALTER TABLE dbx_aviation.flight_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dbx_aviation.ml_analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE dbx_aviation.aircraft_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE dbx_aviation.flight_telemetry ENABLE ROW LEVEL SECURITY;

-- Create security policies for multi-tenant isolation
CREATE POLICY org_isolation_policy ON dbx_aviation.flight_sessions
    USING (org_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY org_isolation_policy ON dbx_aviation.ml_analysis_results
    USING (org_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY org_isolation_policy ON dbx_aviation.aircraft_registry
    USING (org_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY org_isolation_policy ON dbx_aviation.flight_telemetry
    USING (session_id IN (
        SELECT session_id FROM dbx_aviation.flight_sessions 
        WHERE org_id = current_setting('app.current_org_id')::uuid
    ));

-- Function to set organization context
CREATE OR REPLACE FUNCTION dbx_aviation.set_org_context(p_org_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_org_id', p_org_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add encrypted columns for sensitive data
ALTER TABLE dbx_aviation.organizations 
ADD COLUMN IF NOT EXISTS api_key_encrypted BYTEA;

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
DROP TRIGGER IF EXISTS audit_organizations ON dbx_aviation.organizations;
CREATE TRIGGER audit_organizations
    AFTER INSERT OR UPDATE OR DELETE ON dbx_aviation.organizations
    FOR EACH ROW EXECUTE FUNCTION dbx_audit.log_sensitive_access();

DROP TRIGGER IF EXISTS audit_aircraft_registry ON dbx_aviation.aircraft_registry;
CREATE TRIGGER audit_aircraft_registry
    AFTER INSERT OR UPDATE OR DELETE ON dbx_aviation.aircraft_registry
    FOR EACH ROW EXECUTE FUNCTION dbx_audit.log_sensitive_access();

DROP TRIGGER IF EXISTS audit_flight_sessions ON dbx_aviation.flight_sessions;
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

-- Function to check data retention compliance
CREATE OR REPLACE FUNCTION dbx_aviation.check_retention_compliance()
RETURNS TABLE (
    org_code VARCHAR,
    table_name VARCHAR,
    records_to_delete BIGINT,
    oldest_record TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    WITH retention_check AS (
        SELECT 
            o.org_code,
            'flight_sessions' as table_name,
            COUNT(*) as records_to_delete,
            MIN(fs.created_at) as oldest_record
        FROM dbx_aviation.organizations o
        JOIN dbx_aviation.flight_sessions fs ON o.org_id = fs.org_id
        WHERE fs.created_at < CURRENT_DATE - INTERVAL '1 day' * o.data_retention_days
        GROUP BY o.org_code
        
        UNION ALL
        
        SELECT 
            o.org_code,
            'ml_analysis_results' as table_name,
            COUNT(*) as records_to_delete,
            MIN(mar.created_at) as oldest_record
        FROM dbx_aviation.organizations o
        JOIN dbx_aviation.ml_analysis_results mar ON o.org_id = mar.org_id
        WHERE mar.created_at < CURRENT_DATE - INTERVAL '1 day' * o.data_retention_days
        GROUP BY o.org_code
    )
    SELECT * FROM retention_check WHERE records_to_delete > 0;
END;
$$ LANGUAGE plpgsql;

RAISE NOTICE 'Advanced Security Features Installed Successfully!';