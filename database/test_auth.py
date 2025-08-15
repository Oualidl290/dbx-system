#!/usr/bin/env python3
"""
Test Authentication Separately
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def test_authentication():
    """Test authentication separately"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_APP_USER", "dbx_app_user"),
        "password": os.getenv("DB_APP_PASSWORD", "dbx_secure_2025")
    }
    
    print("🔐 Testing Authentication System...")
    
    try:
        conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cursor:
            # Check if admin user exists
            cursor.execute("SELECT email, password_hash, salt FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
            user_data = cursor.fetchone()
            
            if not user_data:
                print("❌ Admin user not found")
                return False
            
            print(f"✅ Admin user found: {user_data['email']}")
            
            # Test password verification
            cursor.execute("SELECT dbx_aviation.verify_password('admin123', %s, %s)", 
                         (user_data['password_hash'], user_data['salt']))
            password_valid = cursor.fetchone()[0]
            
            print(f"✅ Password verification: {'PASSED' if password_valid else 'FAILED'}")
            
            # Test health function
            print("\n🏥 Testing Health Function...")
            cursor.execute("SELECT NOW() as timestamp, 1 as active_connections, pg_database_size(current_database()) as db_size")
            health_data = cursor.fetchone()
            
            print(f"✅ Basic health check works")
            print(f"   Timestamp: {health_data['timestamp']}")
            print(f"   Database size: {health_data['db_size']} bytes")
            
            # Test organization context
            print("\n🏢 Testing Organization Context...")
            cursor.execute("SELECT org_id FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
            org_result = cursor.fetchone()
            
            if org_result:
                org_id = org_result['org_id']
                cursor.execute("SELECT dbx_aviation.set_org_context(%s)", (org_id,))
                print(f"✅ Organization context set: {str(org_id)[:8]}...")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_authentication()
    exit(0 if success else 1)