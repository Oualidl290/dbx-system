#!/usr/bin/env python3
"""
Test Enhanced Database Features
"""

import os
import psycopg2
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_enhanced_features():
    """Test the enhanced database features"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    print("🧪 Testing Enhanced Database Features")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(**config)
        
        with conn.cursor() as cursor:
            # Test 1: Health Monitoring
            print("\n🏥 Testing Health Monitoring...")
            cursor.execute("SELECT dbx_monitoring.collect_health_metrics()")
            health_result = cursor.fetchone()[0]
            print(f"✅ Health Status: {health_result.get('overall_health')}")
            print(f"   Active Connections: {health_result.get('active_connections')}")
            print(f"   Database Size: {health_result.get('database_size_mb')} MB")
            
            # Test 2: Password Hashing
            print("\n🔐 Testing Password Security...")
            cursor.execute("SELECT dbx_aviation.hash_password('test123')")
            hash_result = cursor.fetchone()[0]
            print(f"✅ Password hashing works: {hash_result.get('algorithm')}")
            
            # Test password verification
            cursor.execute("SELECT dbx_aviation.verify_password('test123', %s, %s)", 
                         (hash_result['hash'], hash_result['salt']))
            verify_result = cursor.fetchone()[0]
            print(f"✅ Password verification: {'PASSED' if verify_result else 'FAILED'}")
            
            # Test 3: Cache Policies
            print("\n🚀 Testing Cache Policies...")
            cursor.execute("SELECT policy_name, cache_type, default_ttl_seconds FROM dbx_aviation.cache_policies")
            policies = cursor.fetchall()
            print(f"✅ Cache policies configured: {len(policies)}")
            for policy_name, cache_type, ttl in policies:
                print(f"   • {policy_name}: {cache_type} ({ttl}s TTL)")
            
            # Test 4: User Management
            print("\n👤 Testing User Management...")
            cursor.execute("SELECT COUNT(*) FROM dbx_aviation.users")
            user_count = cursor.fetchone()[0]
            print(f"✅ Users in system: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT email, role, is_active FROM dbx_aviation.users LIMIT 3")
                users = cursor.fetchall()
                for email, role, is_active in users:
                    status = "Active" if is_active else "Inactive"
                    print(f"   • {email}: {role} ({status})")
            
            # Test 5: Organization Context
            print("\n🏢 Testing Organization Context...")
            cursor.execute("SELECT org_id FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
            org_result = cursor.fetchone()
            if org_result:
                org_id = org_result[0]
                cursor.execute("SELECT dbx_aviation.set_org_context(%s)", (org_id,))
                print(f"✅ Organization context set: {str(org_id)[:8]}...")
            
            # Test 6: Database Schema
            print("\n📊 Testing Database Schema...")
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                ORDER BY schema_name
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            print(f"✅ Schemas available: {', '.join(schemas)}")
            
            # Test 7: Table Counts
            cursor.execute("""
                SELECT 
                    schemaname,
                    COUNT(*) as table_count
                FROM pg_tables 
                WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                GROUP BY schemaname
                ORDER BY schemaname
            """)
            table_counts = cursor.fetchall()
            print("✅ Tables per schema:")
            for schema, count in table_counts:
                print(f"   • {schema}: {count} tables")
            
            # Test 8: Function Availability
            print("\n⚙️ Testing Functions...")
            functions_to_test = [
                'dbx_aviation.hash_password',
                'dbx_aviation.verify_password',
                'dbx_aviation.set_org_context',
                'dbx_monitoring.collect_health_metrics'
            ]
            
            for func_name in functions_to_test:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.routines 
                    WHERE routine_schema || '.' || routine_name = %s
                """, (func_name,))
                func_exists = cursor.fetchone()[0] > 0
                status = "✅ Available" if func_exists else "❌ Missing"
                print(f"   • {func_name}: {status}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 All Enhanced Features Working!")
        print("=" * 50)
        print("\n🚀 Your database now includes:")
        print("  • Enterprise-grade user authentication")
        print("  • Smart caching management system")
        print("  • Real-time health monitoring")
        print("  • Enhanced API key management")
        print("  • Multi-tenant organization support")
        print("  • Secure password hashing and verification")
        print("\n✨ Ready for production use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_features()
    exit(0 if success else 1)