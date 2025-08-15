#!/usr/bin/env python3
"""
Reset Admin User Password
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def reset_admin():
    """Reset admin user password"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    print("🔐 Resetting Admin User Password...")
    
    try:
        conn = psycopg2.connect(**config)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cursor:
            # Generate new password hash
            cursor.execute("SELECT dbx_aviation.hash_password('admin123')")
            password_data = cursor.fetchone()[0]
            
            print(f"✅ Generated new password hash")
            
            # Update admin user
            cursor.execute("""
                UPDATE dbx_aviation.users 
                SET password_hash = %s, salt = %s, updated_at = NOW()
                WHERE email = 'admin@dbx-ai.com'
            """, (password_data['hash'], password_data['salt']))
            
            print("✅ Admin user password updated")
            
            # Test the password
            cursor.execute("""
                SELECT dbx_aviation.verify_password('admin123', password_hash, salt)
                FROM dbx_aviation.users 
                WHERE email = 'admin@dbx-ai.com'
            """)
            
            verify_result = cursor.fetchone()[0]
            print(f"✅ Password verification test: {'PASSED' if verify_result else 'FAILED'}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Admin reset failed: {e}")
        return False

if __name__ == "__main__":
    success = reset_admin()
    exit(0 if success else 1)