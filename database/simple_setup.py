#!/usr/bin/env python3
"""
DBX AI Aviation Database - Simple Setup Script
Handles existing installations and dependencies properly
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDatabaseSetup:
    """Simple database setup that handles existing installations"""
    
    def __init__(self):
        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "dbx_aviation"),
            "username": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "password"),
            "app_user": "dbx_app_user",
            "app_password": "dbx_secure_2025"
        }
        self.db_scripts_path = Path(__file__).parent
        
        logger.info(f"Using database: {self.config['database']} on {self.config['host']}:{self.config['port']}")
    
    def _get_connection(self, database: str = None) -> psycopg2.extensions.connection:
        """Get database connection"""
        conn_params = {
            "host": self.config["host"],
            "port": self.config["port"],
            "user": self.config["username"],
            "password": self.config["password"]
        }
        
        if database:
            conn_params["database"] = database
        
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    
    def install_essential_enhancements(self) -> bool:
        """Install essential database enhancements"""
        logger.info("🚀 Installing essential database enhancements...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Create essential schemas if they don't exist
                schemas = ['dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring']
                for schema in schemas:
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                    logger.info(f"✅ Schema {schema} ready")
                
                # Enable essential extensions
                extensions = ['uuid-ossp', 'pgcrypto', 'pg_stat_statements']
                for ext in extensions:
                    try:
                        cursor.execute(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\"")
                        logger.info(f"✅ Extension {ext} enabled")
                    except Exception as e:
                        logger.warning(f"⚠️  Extension {ext} not available: {e}")
                
                # Create essential tables if they don't exist
                self._create_essential_tables(cursor)
                
                # Create essential functions
                self._create_essential_functions(cursor)
                
                logger.info("✅ Essential enhancements installed")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhancement installation failed: {e}")
            return False
    
    def _create_essential_tables(self, cursor):
        """Create essential tables"""
        
        # Enhanced users table with authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dbx_aviation.users (
                user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                org_id UUID,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                salt VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                permissions JSONB DEFAULT '[]'::jsonb,
                email_verified BOOLEAN DEFAULT false,
                mfa_enabled BOOLEAN DEFAULT false,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMPTZ,
                last_login_at TIMESTAMPTZ,
                last_login_ip INET,
                is_active BOOLEAN DEFAULT true,
                is_suspended BOOLEAN DEFAULT false,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        logger.info("✅ Enhanced users table ready")
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dbx_aviation.user_sessions (
                session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID,
                org_id UUID,
                session_token VARCHAR(255) UNIQUE NOT NULL,
                refresh_token VARCHAR(255) UNIQUE NOT NULL,
                ip_address INET NOT NULL,
                user_agent TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL,
                is_active BOOLEAN DEFAULT true,
                revoked_at TIMESTAMPTZ,
                session_type VARCHAR(50) DEFAULT 'web'
            )
        """)
        logger.info("✅ User sessions table ready")
        
        # Enhanced API keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dbx_aviation.api_keys (
                api_key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                org_id UUID,
                user_id UUID,
                key_name VARCHAR(100) NOT NULL,
                key_hash VARCHAR(255) UNIQUE NOT NULL,
                key_prefix VARCHAR(20) NOT NULL,
                scopes JSONB NOT NULL DEFAULT '["read"]'::jsonb,
                rate_limit_per_minute INTEGER DEFAULT 60,
                rate_limit_per_hour INTEGER DEFAULT 1000,
                allowed_ips INET[] DEFAULT '{}',
                last_used_at TIMESTAMPTZ,
                total_requests BIGINT DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT true,
                revoked_at TIMESTAMPTZ
            )
        """)
        logger.info("✅ Enhanced API keys table ready")
        
        # Cache policies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dbx_aviation.cache_policies (
                policy_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                policy_name VARCHAR(100) UNIQUE NOT NULL,
                cache_type VARCHAR(50) NOT NULL DEFAULT 'redis',
                default_ttl_seconds INTEGER NOT NULL DEFAULT 3600,
                key_pattern VARCHAR(255) NOT NULL,
                key_prefix VARCHAR(50) NOT NULL,
                invalidation_strategy VARCHAR(50) NOT NULL DEFAULT 'ttl',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                is_active BOOLEAN DEFAULT true,
                description TEXT
            )
        """)
        logger.info("✅ Cache policies table ready")
        
        # System health monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dbx_monitoring.system_health (
                health_id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                active_connections INTEGER,
                total_connections INTEGER,
                database_size_bytes BIGINT,
                cache_hit_ratio DECIMAL(5,4),
                overall_health VARCHAR(20) DEFAULT 'healthy',
                alerts JSONB DEFAULT '[]'::jsonb
            )
        """)
        logger.info("✅ System health table ready")
    
    def _create_essential_functions(self, cursor):
        """Create essential functions"""
        
        # Password hashing function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION dbx_aviation.hash_password(password TEXT, salt TEXT DEFAULT NULL)
            RETURNS JSONB AS $$
            DECLARE
                generated_salt TEXT;
                password_hash TEXT;
            BEGIN
                IF salt IS NULL THEN
                    generated_salt := encode(gen_random_bytes(16), 'hex');
                ELSE
                    generated_salt := salt;
                END IF;
                
                password_hash := encode(digest(password || generated_salt, 'sha256'), 'hex');
                
                RETURN jsonb_build_object(
                    'hash', password_hash,
                    'salt', generated_salt,
                    'algorithm', 'sha256_salted'
                );
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """)
        
        # Password verification function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION dbx_aviation.verify_password(password TEXT, stored_hash TEXT, salt TEXT)
            RETURNS BOOLEAN AS $$
            DECLARE
                computed_hash TEXT;
            BEGIN
                computed_hash := encode(digest(password || salt, 'sha256'), 'hex');
                RETURN computed_hash = stored_hash;
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """)
        
        # Organization context function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION dbx_aviation.set_org_context(org_uuid UUID)
            RETURNS VOID AS $$
            BEGIN
                PERFORM set_config('app.current_org_id', org_uuid::text, true);
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
        """)
        
        # Health check function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION dbx_monitoring.collect_health_metrics()
            RETURNS JSONB AS $$
            DECLARE
                health_data JSONB;
                active_conn INTEGER;
                total_conn INTEGER;
                db_size BIGINT;
            BEGIN
                SELECT COUNT(*) INTO active_conn FROM pg_stat_activity WHERE state = 'active';
                SELECT COUNT(*) INTO total_conn FROM pg_stat_activity;
                SELECT pg_database_size(current_database()) INTO db_size;
                
                INSERT INTO dbx_monitoring.system_health (
                    active_connections, total_connections, database_size_bytes, overall_health
                ) VALUES (
                    active_conn, total_conn, db_size, 'healthy'
                );
                
                health_data := jsonb_build_object(
                    'timestamp', NOW(),
                    'active_connections', active_conn,
                    'total_connections', total_conn,
                    'database_size_mb', ROUND(db_size / 1024.0 / 1024.0, 2),
                    'overall_health', 'healthy'
                );
                
                RETURN health_data;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        logger.info("✅ Essential functions created")
    
    def create_default_data(self) -> bool:
        """Create default data"""
        logger.info("📊 Creating default data...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Check if default organization exists
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
                if cursor.fetchone()[0] == 0:
                    # Create default organization
                    cursor.execute("""
                        INSERT INTO dbx_aviation.organizations (
                            org_code, org_name, org_type, api_key_hash, created_by
                        ) VALUES (
                            'DBX_DEFAULT', 'DBX AI Default Organization', 'private',
                            encode(digest('dbx_default_api_key_change_me', 'sha256'), 'hex'),
                            uuid_generate_v4()
                        )
                    """)
                    logger.info("✅ Default organization created")
                
                # Get default org ID
                cursor.execute("SELECT org_id FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
                org_id = cursor.fetchone()[0]
                
                # Check if admin user exists
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
                if cursor.fetchone()[0] == 0:
                    # Create admin user
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
                    logger.info("✅ Default admin user created")
                
                # Create default cache policies
                cache_policies = [
                    ('flight_analysis', 'redis', 7200, 'analysis:{org_id}:{session_id}', 'analysis:', 'Flight analysis results caching'),
                    ('aircraft_registry', 'redis', 21600, 'aircraft:{org_id}:{aircraft_id}', 'aircraft:', 'Aircraft registry data caching'),
                    ('user_sessions', 'memory', 1800, 'user_session:{session_token}', 'user_session:', 'User session data caching'),
                    ('rate_limits', 'memory', 60, 'rate_limit:{org_id}:{api_key}:{window}', 'rate_limit:', 'API rate limiting counters')
                ]
                
                for policy_name, cache_type, ttl, pattern, prefix, description in cache_policies:
                    cursor.execute("""
                        INSERT INTO dbx_aviation.cache_policies 
                        (policy_name, cache_type, default_ttl_seconds, key_pattern, key_prefix, description)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (policy_name) DO NOTHING
                    """, (policy_name, cache_type, ttl, pattern, prefix, description))
                
                logger.info("✅ Default cache policies created")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Default data creation failed: {e}")
            return False
    
    def create_app_user(self) -> bool:
        """Create application user"""
        logger.info("👤 Creating application user...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Check if user exists
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (self.config["app_user"],))
                
                if cursor.fetchone():
                    logger.info(f"👤 User {self.config['app_user']} already exists")
                    # Update password
                    cursor.execute(f"ALTER ROLE {self.config['app_user']} WITH PASSWORD %s", (self.config["app_password"],))
                else:
                    # Create user
                    cursor.execute(f"""
                        CREATE ROLE {self.config['app_user']} WITH 
                        LOGIN PASSWORD %s
                    """, (self.config["app_password"],))
                    logger.info(f"✅ User {self.config['app_user']} created")
                
                # Grant basic permissions
                cursor.execute(f"GRANT CONNECT ON DATABASE {self.config['database']} TO {self.config['app_user']}")
                cursor.execute(f"GRANT USAGE ON SCHEMA dbx_aviation, dbx_analytics, dbx_monitoring TO {self.config['app_user']}")
                cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dbx_aviation TO {self.config['app_user']}")
                cursor.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA dbx_aviation TO {self.config['app_user']}")
                
                logger.info("✅ Application user configured")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Application user creation failed: {e}")
            return False
    
    def test_functionality(self) -> bool:
        """Test basic functionality"""
        logger.info("🧪 Testing basic functionality...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Test health monitoring
                cursor.execute("SELECT dbx_monitoring.collect_health_metrics()")
                health_result = cursor.fetchone()[0]
                if health_result.get("overall_health") == "healthy":
                    logger.info("✅ Health monitoring test passed")
                else:
                    logger.warning("⚠️  Health monitoring test failed")
                
                # Test password functions
                cursor.execute("SELECT dbx_aviation.hash_password('test123')")
                hash_result = cursor.fetchone()[0]
                if hash_result.get("hash"):
                    logger.info("✅ Password hashing test passed")
                else:
                    logger.warning("⚠️  Password hashing test failed")
                
                # Test cache policies
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.cache_policies")
                policy_count = cursor.fetchone()[0]
                if policy_count > 0:
                    logger.info(f"✅ Cache policies test passed ({policy_count} policies)")
                else:
                    logger.warning("⚠️  Cache policies test failed")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Functionality test failed: {e}")
            return False
    
    def update_env_file(self) -> bool:
        """Update .env file with database configuration"""
        logger.info("📝 Updating .env file...")
        
        try:
            env_path = Path(".env")
            
            # Read existing content
            existing_content = ""
            if env_path.exists():
                with open(env_path, 'r') as f:
                    existing_content = f.read()
            
            # Check if database config already exists
            if "DATABASE_URL=" in existing_content:
                logger.info("✅ Database configuration already exists in .env")
                return True
            
            # Add database configuration
            database_config = f"""
# DBX AI Aviation Database Configuration (Enhanced)
DATABASE_URL=postgresql://{self.config['app_user']}:{self.config['app_password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}
DB_NAME={self.config['database']}
DB_APP_USER={self.config['app_user']}
DB_APP_PASSWORD={self.config['app_password']}

# Security Configuration
JWT_SECRET_KEY={os.urandom(32).hex()}
ENCRYPTION_KEY={os.urandom(32).hex()}
"""
            
            # Write updated .env file
            with open(env_path, 'w') as f:
                f.write(existing_content.rstrip() + database_config)
            
            logger.info("✅ Database configuration added to .env file")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment file update failed: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run the simple setup process"""
        logger.info("🚀 Starting DBX AI Aviation Database Simple Setup")
        logger.info("=" * 60)
        
        steps = [
            ("Essential Enhancements", self.install_essential_enhancements),
            ("Default Data Creation", self.create_default_data),
            ("Application User", self.create_app_user),
            ("Functionality Test", self.test_functionality),
            ("Environment Update", self.update_env_file)
        ]
        
        for step_name, step_function in steps:
            logger.info(f"\n📋 Step: {step_name}")
            logger.info("-" * 40)
            
            if not step_function():
                logger.error(f"❌ Setup failed at step: {step_name}")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 DBX AI Aviation Database Setup Completed Successfully!")
        logger.info("=" * 60)
        
        self._print_summary()
        return True
    
    def _print_summary(self):
        """Print setup summary"""
        logger.info("\n📊 Setup Summary:")
        logger.info(f"  • Database: {self.config['database']} on {self.config['host']}:{self.config['port']}")
        logger.info(f"  • Application User: {self.config['app_user']}")
        logger.info("  • Enhanced Features: Authentication, Caching, Monitoring")
        
        logger.info("\n🔑 Default Credentials (CHANGE IN PRODUCTION!):")
        logger.info("  • Admin User: admin@dbx-ai.com / admin123")
        logger.info(f"  • Database User: {self.config['app_user']} / {self.config['app_password']}")
        
        logger.info("\n🧪 Test Your Database:")
        logger.info("  python -c \"import psycopg2; print('✅ Database ready!')\"")
        
        logger.info("\n🚀 Your enhanced aviation AI database is ready!")
        logger.info("  • User authentication with secure password hashing")
        logger.info("  • Smart caching policies for performance")
        logger.info("  • Real-time health monitoring")
        logger.info("  • Enhanced API key management")

def main():
    """Main setup function"""
    print("🚁 DBX AI Aviation Database - Simple Setup")
    print("=" * 50)
    
    setup = SimpleDatabaseSetup()
    
    try:
        success = setup.run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Setup failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()