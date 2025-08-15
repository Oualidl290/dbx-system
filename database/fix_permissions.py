#!/usr/bin/env python3
"""
Fix Database Permissions
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_permissions():
    """Fix database permissions for the application user"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),  # Use superuser to fix permissions
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    app_user = "dbx_app_user"
    
    print("🔧 Fixing Database Permissions...")
    
    try:
        conn = psycopg2.connect(**config)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cursor:
            # Grant permissions on all schemas
            schemas = ['dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring']
            for schema in schemas:
                cursor.execute(f"GRANT USAGE ON SCHEMA {schema} TO {app_user}")
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema} TO {app_user}")
                cursor.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA {schema} TO {app_user}")
                print(f"✅ Permissions granted on schema: {schema}")
            
            # Grant execute permissions on functions
            cursor.execute(f"GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dbx_aviation TO {app_user}")
            cursor.execute(f"GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dbx_monitoring TO {app_user}")
            print("✅ Function execution permissions granted")
            
            # Grant specific permissions for monitoring
            cursor.execute(f"GRANT INSERT ON dbx_monitoring.system_health TO {app_user}")
            print("✅ Monitoring permissions granted")
            
            # Check if admin user exists and fix password if needed
            cursor.execute("SELECT COUNT(*) FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
            if cursor.fetchone()[0] == 0:
                print("⚠️  Admin user not found, creating...")
                
                # Get default org ID
                cursor.execute("SELECT org_id FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
                org_result = cursor.fetchone()
                if org_result:
                    org_id = org_result[0]
                    
                    # Create admin user with correct password
                    cursor.execute("SELECT dbx_aviation.hash_password('admin123')")
                    password_data = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        INSERT INTO dbx_aviation.users (
                            org_id, email, password_hash, salt, first_name, last_name,
                            role, email_verified, is_active
                        ) VALUES (
                            %s, 'admin@dbx-ai.com', %s, %s, 'System', 'Administrator',
                            'admin', true, true
                        )
                    """, (org_id, password_data['hash'], password_data['salt']))
                    print("✅ Admin user created")
            else:
                print("✅ Admin user already exists")
        
        conn.close()
        print("\n🎉 Permissions fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Permission fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_permissions()
    exit(0 if success else 1)