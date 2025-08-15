#!/usr/bin/env python3
"""
Simple database connection test
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection with current credentials"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    print("🔍 Testing database connection...")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    
    try:
        # Test connection
        conn = psycopg2.connect(**config)
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {version[:50]}...")
            
            # Check if our database exists
            cursor.execute("SELECT datname FROM pg_database WHERE datname = %s", (config['database'],))
            if cursor.fetchone():
                print(f"✅ Database '{config['database']}' exists")
            else:
                print(f"⚠️  Database '{config['database']}' does not exist")
                
                # Try to create it
                conn.close()
                
                # Connect to postgres database to create new database
                config['database'] = 'postgres'
                conn = psycopg2.connect(**config)
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                
                with conn.cursor() as cursor:
                    cursor.execute(f'CREATE DATABASE "dbx_aviation" WITH ENCODING \'UTF8\'')
                    print("✅ Database 'dbx_aviation' created successfully")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)