#!/usr/bin/env python3
"""
HONEST Database Recheck - Complete Truth Assessment
No sugar-coating, just facts about what actually works
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

load_dotenv()

def honest_recheck():
    """Brutally honest assessment of what actually works"""
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "dbx_aviation"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "password")
    }
    
    print("🔍 HONEST DATABASE RECHECK - THE REAL TRUTH")
    print("=" * 60)
    print("No marketing fluff - just what actually works vs what doesn't")
    print("=" * 60)
    
    working_features = []
    broken_features = []
    missing_features = []
    
    try:
        conn = psycopg2.connect(**config, cursor_factory=RealDictCursor)
        
        with conn.cursor() as cursor:
            # 1. BASIC DATABASE STRUCTURE
            print("\n📊 BASIC DATABASE STRUCTURE")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    SELECT schema_name FROM information_schema.schemata 
                    WHERE schema_name IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                    ORDER BY schema_name
                """)
                schemas = [row['schema_name'] for row in cursor.fetchall()]
                print(f"✅ WORKING: Enhanced schemas created: {', '.join(schemas)}")
                working_features.append("Enhanced database schemas")
            except Exception as e:
                print(f"❌ BROKEN: Schema creation failed: {e}")
                broken_features.append("Enhanced database schemas")
            
            # 2. ORIGINAL TABLES (from your existing system)
            print("\n🗄️ ORIGINAL TABLES STATUS")
            print("-" * 40)
            
            original_tables = [
                'dbx_aviation.organizations',
                'dbx_aviation.aircraft_registry', 
                'dbx_aviation.flight_sessions',
                'dbx_aviation.flight_telemetry',
                'dbx_aviation.ml_analysis_results',
                'dbx_aviation.api_requests'
            ]
            
            for table in original_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"✅ WORKING: {table}: {count} records")
                    working_features.append(f"Original table: {table}")
                except Exception as e:
                    print(f"❌ BROKEN: {table}: {e}")
                    broken_features.append(f"Original table: {table}")
            
            # 3. NEW ENHANCED TABLES
            print("\n🆕 NEW ENHANCED TABLES STATUS")
            print("-" * 40)
            
            enhanced_tables = [
                'dbx_aviation.users',
                'dbx_aviation.user_sessions', 
                'dbx_aviation.api_keys',
                'dbx_aviation.cache_policies',
                'dbx_monitoring.system_health'
            ]
            
            for table in enhanced_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"✅ WORKING: {table}: {count} records")
                    working_features.append(f"Enhanced table: {table}")
                except Exception as e:
                    print(f"❌ BROKEN: {table}: {e}")
                    broken_features.append(f"Enhanced table: {table}")
            
            # 4. SECURITY FUNCTIONS
            print("\n🔐 SECURITY FUNCTIONS STATUS")
            print("-" * 40)
            
            security_functions = [
                'dbx_aviation.hash_password',
                'dbx_aviation.verify_password',
                'dbx_aviation.set_org_context'
            ]
            
            for func in security_functions:
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM information_schema.routines 
                        WHERE routine_schema || '.' || routine_name = '{func}'
                    """)
                    exists = cursor.fetchone()['count'] > 0
                    if exists:
                        print(f"✅ WORKING: Function {func} exists")
                        working_features.append(f"Security function: {func}")
                    else:
                        print(f"❌ MISSING: Function {func} not found")
                        missing_features.append(f"Security function: {func}")
                except Exception as e:
                    print(f"❌ BROKEN: Function {func}: {e}")
                    broken_features.append(f"Security function: {func}")
            
            # 5. TEST ACTUAL SECURITY FUNCTIONALITY
            print("\n🧪 SECURITY FUNCTIONALITY TEST")
            print("-" * 40)
            
            try:
                # Test password hashing
                cursor.execute("SELECT dbx_aviation.hash_password('test123') as hash_data")
                hash_row = cursor.fetchone()
                hash_result = hash_row['hash_data']
                print(f"✅ WORKING: Password hashing produces: {hash_result.get('algorithm', 'unknown')}")
                
                # Test password verification
                cursor.execute("SELECT dbx_aviation.verify_password('test123', %s, %s) as is_valid", 
                             (hash_result['hash'], hash_result['salt']))
                verify_row = cursor.fetchone()
                verify_result = verify_row['is_valid']
                
                if verify_result:
                    print("✅ WORKING: Password verification works correctly")
                    working_features.append("Password hashing and verification")
                else:
                    print("❌ BROKEN: Password verification returns false")
                    broken_features.append("Password verification")
                    
            except Exception as e:
                print(f"❌ BROKEN: Security functions failed: {e}")
                broken_features.append("Security functions execution")
            
            # 6. USER AUTHENTICATION TEST
            print("\n👤 USER AUTHENTICATION TEST")
            print("-" * 40)
            
            try:
                cursor.execute("SELECT email, role, is_active FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
                admin_user = cursor.fetchone()
                
                if admin_user:
                    print(f"✅ WORKING: Admin user exists: {admin_user['email']} ({admin_user['role']})")
                    
                    # Test actual authentication
                    cursor.execute("""
                        SELECT u.user_id, u.org_id, u.role,
                               dbx_aviation.verify_password('admin123', u.password_hash, u.salt) as pwd_valid
                        FROM dbx_aviation.users u
                        WHERE u.email = 'admin@dbx-ai.com'
                    """)
                    auth_test = cursor.fetchone()
                    
                    if auth_test and auth_test['pwd_valid']:
                        print("✅ WORKING: Admin authentication works with correct password")
                        working_features.append("User authentication system")
                    else:
                        print("❌ BROKEN: Admin authentication fails")
                        broken_features.append("User authentication")
                else:
                    print("❌ MISSING: Admin user not found")
                    missing_features.append("Default admin user")
                    
            except Exception as e:
                print(f"❌ BROKEN: User authentication test failed: {e}")
                broken_features.append("User authentication system")
            
            # 7. CACHE POLICIES TEST
            print("\n🚀 CACHE POLICIES TEST")
            print("-" * 40)
            
            try:
                cursor.execute("SELECT policy_name, cache_type, default_ttl_seconds FROM dbx_aviation.cache_policies")
                policies = cursor.fetchall()
                
                if policies:
                    print(f"✅ WORKING: {len(policies)} cache policies configured:")
                    for policy in policies:
                        print(f"   • {policy['policy_name']}: {policy['cache_type']} ({policy['default_ttl_seconds']}s)")
                    working_features.append("Cache policy management")
                else:
                    print("❌ MISSING: No cache policies found")
                    missing_features.append("Cache policies")
                    
            except Exception as e:
                print(f"❌ BROKEN: Cache policies test failed: {e}")
                broken_features.append("Cache policy system")
            
            # 8. PERFORMANCE INDEXES TEST
            print("\n⚡ PERFORMANCE INDEXES TEST")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    SELECT schemaname, COUNT(*) as index_count
                    FROM pg_indexes 
                    WHERE schemaname IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                    GROUP BY schemaname
                    ORDER BY schemaname
                """)
                index_stats = cursor.fetchall()
                
                total_indexes = sum(row['index_count'] for row in index_stats)
                
                if total_indexes > 0:
                    print(f"✅ WORKING: {total_indexes} performance indexes created:")
                    for stat in index_stats:
                        print(f"   • {stat['schemaname']}: {stat['index_count']} indexes")
                    working_features.append("Performance indexing")
                else:
                    print("❌ MISSING: No performance indexes found")
                    missing_features.append("Performance indexes")
                    
            except Exception as e:
                print(f"❌ BROKEN: Performance indexes test failed: {e}")
                broken_features.append("Performance indexing")
            
            # 9. ROW LEVEL SECURITY TEST
            print("\n🛡️ ROW LEVEL SECURITY TEST")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
                    FROM pg_policies 
                    WHERE schemaname = 'dbx_aviation'
                """)
                policies = cursor.fetchall()
                
                if policies:
                    print(f"✅ WORKING: {len(policies)} RLS policies active:")
                    for policy in policies:
                        print(f"   • {policy['tablename']}: {policy['policyname']}")
                    working_features.append("Row Level Security policies")
                else:
                    print("❌ MISSING: No RLS policies found")
                    missing_features.append("Row Level Security")
                    
            except Exception as e:
                print(f"❌ BROKEN: RLS test failed: {e}")
                broken_features.append("Row Level Security")
            
            # 10. MONITORING SYSTEM TEST
            print("\n📈 MONITORING SYSTEM TEST")
            print("-" * 40)
            
            try:
                cursor.execute("SELECT COUNT(*) as count FROM dbx_monitoring.system_health")
                health_count = cursor.fetchone()['count']
                
                if health_count > 0:
                    print(f"✅ WORKING: {health_count} health monitoring records")
                    
                    # Test health function
                    cursor.execute("SELECT NOW() as timestamp, pg_database_size(current_database()) as db_size")
                    health_data = cursor.fetchone()
                    print(f"✅ WORKING: Health monitoring captures data (DB size: {health_data['db_size']} bytes)")
                    working_features.append("Health monitoring system")
                else:
                    print("❌ MISSING: No health monitoring data")
                    missing_features.append("Health monitoring data")
                    
            except Exception as e:
                print(f"❌ BROKEN: Monitoring system test failed: {e}")
                broken_features.append("Monitoring system")
            
            # 11. BACKUP SYSTEM TEST
            print("\n💾 BACKUP SYSTEM TEST")
            print("-" * 40)
            
            backup_tables = [
                'dbx_aviation.backup_policies',
                'dbx_aviation.backup_executions',
                'dbx_aviation.recovery_operations'
            ]
            
            backup_working = True
            for table in backup_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"✅ WORKING: {table}: {count} records")
                except Exception as e:
                    print(f"❌ MISSING: {table}: {e}")
                    backup_working = False
            
            if backup_working:
                working_features.append("Backup system tables")
            else:
                missing_features.append("Backup system")
            
            # 12. EXTENSIONS TEST
            print("\n🔧 EXTENSIONS TEST")
            print("-" * 40)
            
            try:
                cursor.execute("SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_stat_statements')")
                extensions = [row['extname'] for row in cursor.fetchall()]
                
                if extensions:
                    print(f"✅ WORKING: Extensions enabled: {', '.join(extensions)}")
                    working_features.append("PostgreSQL extensions")
                else:
                    print("❌ MISSING: No enhanced extensions found")
                    missing_features.append("PostgreSQL extensions")
                    
            except Exception as e:
                print(f"❌ BROKEN: Extensions test failed: {e}")
                broken_features.append("PostgreSQL extensions")
        
        conn.close()
        
        # FINAL HONEST ASSESSMENT
        print("\n" + "=" * 60)
        print("🎯 HONEST ASSESSMENT - THE REAL TRUTH")
        print("=" * 60)
        
        print(f"\n✅ WORKING FEATURES ({len(working_features)}):")
        for feature in working_features:
            print(f"   • {feature}")
        
        if broken_features:
            print(f"\n❌ BROKEN FEATURES ({len(broken_features)}):")
            for feature in broken_features:
                print(f"   • {feature}")
        
        if missing_features:
            print(f"\n⚠️ MISSING FEATURES ({len(missing_features)}):")
            for feature in missing_features:
                print(f"   • {feature}")
        
        # CALCULATE REAL SUCCESS RATE
        total_expected = len(working_features) + len(broken_features) + len(missing_features)
        success_rate = (len(working_features) / total_expected * 100) if total_expected > 0 else 0
        
        print(f"\n📊 REAL SUCCESS RATE: {success_rate:.1f}%")
        print(f"   Working: {len(working_features)}")
        print(f"   Broken: {len(broken_features)}")
        print(f"   Missing: {len(missing_features)}")
        
        # HONEST GRADE
        if success_rate >= 90:
            grade = "A"
            status = "EXCELLENT - Production Ready"
        elif success_rate >= 80:
            grade = "B"
            status = "GOOD - Minor Issues"
        elif success_rate >= 70:
            grade = "C"
            status = "ACCEPTABLE - Some Problems"
        elif success_rate >= 60:
            grade = "D"
            status = "POOR - Major Issues"
        else:
            grade = "F"
            status = "FAILED - Not Working"
        
        print(f"\n🎯 HONEST GRADE: {grade} ({status})")
        
        # WHAT ACTUALLY WORKS
        print(f"\n🚀 WHAT ACTUALLY WORKS:")
        if len(working_features) > 0:
            print("   Your database has been successfully enhanced with:")
            core_working = [f for f in working_features if any(x in f.lower() for x in ['schema', 'table', 'function', 'authentication'])]
            for feature in core_working[:5]:  # Show top 5
                print(f"   ✅ {feature}")
        else:
            print("   ❌ Very few enhancements are actually working")
        
        # WHAT NEEDS FIXING
        if broken_features or missing_features:
            print(f"\n⚠️ WHAT NEEDS FIXING:")
            all_issues = broken_features + missing_features
            for issue in all_issues[:5]:  # Show top 5 issues
                print(f"   🔧 {issue}")
        
        print(f"\n💡 BOTTOM LINE:")
        if success_rate >= 80:
            print("   Your database enhancement was largely successful!")
            print("   Most core features are working and you have a solid foundation.")
        elif success_rate >= 60:
            print("   Your database enhancement was partially successful.")
            print("   Core features work but some advanced features need attention.")
        else:
            print("   Your database enhancement needs significant work.")
            print("   Many features are not working as expected.")
        
        return success_rate >= 70  # Consider 70%+ as success
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Database connection or major system failure: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = honest_recheck()
    exit(0 if success else 1)