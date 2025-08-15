#!/usr/bin/env python3
"""
Simple Database Test
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def simple_test():
    """Simple database functionality test"""
    
    # Test with superuser first
    superuser_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    # Test with app user
    app_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": "dbx_app_user",
        "password": "dbx_secure_2025"
    }
    
    print("🧪 Simple Database Test")
    print("=" * 30)
    
    # Test 1: Superuser connection
    print("\n👑 Testing Superuser Connection...")
    try:
        conn = psycopg2.connect(**superuser_config, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            cursor.execute("SELECT email, role FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
            user = cursor.fetchone()
            if user:
                print(f"✅ Admin user found: {user['email']} ({user['role']})")
                
                # Test password verification
                cursor.execute("SELECT password_hash, salt FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
                pwd_data = cursor.fetchone()
                
                cursor.execute("SELECT dbx_aviation.verify_password('admin123', %s, %s)", 
                             (pwd_data['password_hash'], pwd_data['salt']))
                pwd_valid = cursor.fetchone()[0]
                print(f"✅ Password verification: {'PASSED' if pwd_valid else 'FAILED'}")
            else:
                print("❌ Admin user not found")
        conn.close()
    except Exception as e:
        print(f"❌ Superuser test failed: {e}")
    
    # Test 2: App user connection
    print("\n👤 Testing App User Connection...")
    try:
        conn = psycopg2.connect(**app_config, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM dbx_aviation.users")
            count = cursor.fetchone()['count']
            print(f"✅ App user can read users table: {count} users")
            
            # Test basic health check
            cursor.execute("SELECT NOW() as timestamp, pg_database_size(current_database()) as size")
            health = cursor.fetchone()
            print(f"✅ Basic queries work: DB size {health['size']} bytes")
            
        conn.close()
    except Exception as e:
        print(f"❌ App user test failed: {e}")
    
    # Test 3: Create a simple authentication function
    print("\n🔐 Creating Simple Authentication...")
    try:
        conn = psycopg2.connect(**superuser_config)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cursor:
            # Create a simple authentication function
            cursor.execute("""
                CREATE OR REPLACE FUNCTION dbx_aviation.simple_authenticate(p_email TEXT, p_password TEXT)
                RETURNS JSONB AS $$
                DECLARE
                    user_record RECORD;
                    password_valid BOOLEAN;
                BEGIN
                    SELECT user_id, org_id, role, password_hash, salt, is_active
                    INTO user_record
                    FROM dbx_aviation.users
                    WHERE email = p_email AND is_active = true;
                    
                    IF NOT FOUND THEN
                        RETURN jsonb_build_object('success', false, 'error', 'User not found');
                    END IF;
                    
                    SELECT dbx_aviation.verify_password(p_password, user_record.password_hash, user_record.salt)
                    INTO password_valid;
                    
                    IF password_valid THEN
                        RETURN jsonb_build_object(
                            'success', true,
                            'user_id', user_record.user_id,
                            'org_id', user_record.org_id,
                            'role', user_record.role
                        );
                    ELSE
                        RETURN jsonb_build_object('success', false, 'error', 'Invalid password');
                    END IF;
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
            """)
            
            # Grant execute permission
            cursor.execute("GRANT EXECUTE ON FUNCTION dbx_aviation.simple_authenticate(TEXT, TEXT) TO dbx_app_user")
            
            print("✅ Simple authentication function created")
            
        conn.close()
    except Exception as e:
        print(f"❌ Function creation failed: {e}")
    
    # Test 4: Test the simple authentication
    print("\n🧪 Testing Simple Authentication...")
    try:
        conn = psycopg2.connect(**app_config, cursor_factory=RealDictCursor)
        with conn.cursor() as cursor:
            cursor.execute("SELECT dbx_aviation.simple_authenticate('admin@dbx-ai.com', 'admin123')")
            auth_result = cursor.fetchone()[0]
            
            if auth_result['success']:
                print(f"✅ Authentication successful!")
                print(f"   User ID: {auth_result['user_id']}")
                print(f"   Role: {auth_result['role']}")
                print(f"   Org ID: {auth_result['org_id']}")
            else:
                print(f"❌ Authentication failed: {auth_result['error']}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    print("\n🎉 Simple test completed!")

if __name__ == "__main__":
    simple_test()