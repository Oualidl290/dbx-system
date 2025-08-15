#!/usr/bin/env python3
"""
DBX AI Aviation Database Setup Script
Automated installation and configuration of the complete database system
"""

import os
import sys
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Automated database setup and configuration"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.db_scripts_path = Path(__file__).parent
        
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration from environment variables"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "dbx_aviation"),
            "username": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "password"),
            "app_user": os.getenv("DB_APP_USER", "dbx_app_user"),
            "app_password": os.getenv("DB_APP_PASSWORD", "change_me_in_production"),
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "create_database": os.getenv("CREATE_DATABASE", "true").lower() == "true",
            "run_tests": os.getenv("RUN_TESTS", "true").lower() == "true"
        }
    
    def _get_connection(self, database: Optional[str] = None) -> psycopg2.extensions.connection:
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
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        try:
            # Check PostgreSQL connection
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"✅ PostgreSQL connected: {version[:50]}...")
            conn.close()
            
            # Check required extensions
            conn = self._get_connection(self.config["database"] if not self.config["create_database"] else "postgres")
            with conn.cursor() as cursor:
                # Check if we can create extensions (need superuser for some)
                try:
                    cursor.execute("SELECT current_setting('is_superuser')")
                    is_superuser = cursor.fetchone()[0] == 'on'
                    if not is_superuser:
                        logger.warning("⚠️  Not running as superuser - some extensions may not install")
                except:
                    pass
            conn.close()
            
            # Check if database scripts exist
            required_scripts = [
                "init_database.sql",
                "enhanced_security.sql", 
                "smart_caching.sql",
                "performance_optimization.sql",
                "backup_recovery.sql",
                "install_complete_database.sql"
            ]
            
            for script in required_scripts:
                script_path = self.db_scripts_path / script
                if not script_path.exists():
                    logger.error(f"❌ Required script not found: {script}")
                    return False
                logger.info(f"✅ Found script: {script}")
            
            logger.info("✅ All prerequisites met")
            return True
            
        except Exception as e:
            logger.error(f"❌ Prerequisites check failed: {e}")
            return False
    
    def create_database(self) -> bool:
        """Create the database if it doesn't exist"""
        if not self.config["create_database"]:
            logger.info("📊 Skipping database creation (using existing database)")
            return True
        
        logger.info(f"📊 Creating database: {self.config['database']}")
        
        try:
            # Connect to postgres database to create new database
            conn = self._get_connection("postgres")
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.config["database"],)
                )
                
                if cursor.fetchone():
                    logger.info(f"📊 Database {self.config['database']} already exists")
                else:
                    # Create database
                    cursor.execute(f'CREATE DATABASE "{self.config["database"]}" WITH ENCODING \'UTF8\'')
                    logger.info(f"✅ Database {self.config['database']} created successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False
    
    def install_database_schema(self) -> bool:
        """Install the complete database schema"""
        logger.info("🚀 Installing database schema...")
        
        try:
            # Connect to the target database
            conn = self._get_connection(self.config["database"])
            
            # Read and execute the complete installation script
            install_script_path = self.db_scripts_path / "install_complete_database.sql"
            
            with open(install_script_path, 'r', encoding='utf-8') as f:
                install_script = f.read()
            
            # Replace \i commands with actual file contents
            script_replacements = {
                "\\i init_database.sql": self._read_script("init_database.sql"),
                "\\i enhanced_security.sql": self._read_script("enhanced_security.sql"),
                "\\i smart_caching.sql": self._read_script("smart_caching.sql"),
                "\\i performance_optimization.sql": self._read_script("performance_optimization.sql"),
                "\\i backup_recovery.sql": self._read_script("backup_recovery.sql")
            }
            
            for placeholder, content in script_replacements.items():
                install_script = install_script.replace(placeholder, content)
            
            # Remove psql-specific commands
            install_script = install_script.replace("\\timing on", "")
            install_script = install_script.replace("\\timing off", "")
            install_script = install_script.replace("\\echo", "-- echo")
            
            # Execute the installation script
            with conn.cursor() as cursor:
                cursor.execute(install_script)
            
            conn.close()
            logger.info("✅ Database schema installed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database schema installation failed: {e}")
            return False
    
    def _read_script(self, script_name: str) -> str:
        """Read SQL script file"""
        script_path = self.db_scripts_path / script_name
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_application_user(self) -> bool:
        """Create application database user"""
        logger.info("👤 Creating application user...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Check if user exists
                cursor.execute(
                    "SELECT 1 FROM pg_roles WHERE rolname = %s",
                    (self.config["app_user"],)
                )
                
                if cursor.fetchone():
                    logger.info(f"👤 User {self.config['app_user']} already exists")
                    # Update password
                    cursor.execute(
                        f"ALTER ROLE {self.config['app_user']} WITH PASSWORD %s",
                        (self.config["app_password"],)
                    )
                else:
                    # Create user
                    cursor.execute(f"""
                        CREATE ROLE {self.config['app_user']} WITH 
                        LOGIN PASSWORD %s
                    """, (self.config["app_password"],))
                    
                    logger.info(f"✅ User {self.config['app_user']} created successfully")
                
                # Grant permissions
                cursor.execute(f"GRANT dbx_app_write TO {self.config['app_user']}")
                cursor.execute(f"GRANT CONNECT ON DATABASE {self.config['database']} TO {self.config['app_user']}")
                cursor.execute(f"GRANT USAGE ON SCHEMA dbx_aviation, dbx_analytics, dbx_monitoring TO {self.config['app_user']}")
                cursor.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA dbx_aviation TO {self.config['app_user']}")
                
                logger.info("✅ Application user permissions granted")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Application user creation failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the database installation"""
        logger.info("🔍 Verifying installation...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Check schemas
                cursor.execute("""
                    SELECT schema_name FROM information_schema.schemata 
                    WHERE schema_name IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                    ORDER BY schema_name
                """)
                schemas = [row[0] for row in cursor.fetchall()]
                logger.info(f"✅ Schemas created: {', '.join(schemas)}")
                
                # Check tables
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                """)
                table_count = cursor.fetchone()[0]
                logger.info(f"✅ Tables created: {table_count}")
                
                # Check functions
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.routines 
                    WHERE routine_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                """)
                function_count = cursor.fetchone()[0]
                logger.info(f"✅ Functions created: {function_count}")
                
                # Check default organization
                cursor.execute("SELECT org_code FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
                if cursor.fetchone():
                    logger.info("✅ Default organization created")
                else:
                    logger.warning("⚠️  Default organization not found")
                
                # Check default admin user
                cursor.execute("SELECT email FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
                if cursor.fetchone():
                    logger.info("✅ Default admin user created")
                else:
                    logger.warning("⚠️  Default admin user not found")
            
            conn.close()
            logger.info("✅ Installation verification completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Installation verification failed: {e}")
            return False
    
    def run_basic_tests(self) -> bool:
        """Run basic functionality tests"""
        if not self.config["run_tests"]:
            logger.info("🧪 Skipping tests (disabled in configuration)")
            return True
        
        logger.info("🧪 Running basic functionality tests...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            with conn.cursor() as cursor:
                # Test authentication function
                cursor.execute("""
                    SELECT dbx_aviation.authenticate_user(
                        'admin@dbx-ai.com', 'admin123', '127.0.0.1'::inet, 'test-agent'
                    )
                """)
                auth_result = cursor.fetchone()[0]
                if auth_result.get("success"):
                    logger.info("✅ Authentication test passed")
                else:
                    logger.error(f"❌ Authentication test failed: {auth_result.get('error')}")
                    return False
                
                # Test cache policy creation
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.cache_policies")
                cache_policies = cursor.fetchone()[0]
                if cache_policies > 0:
                    logger.info(f"✅ Cache policies test passed ({cache_policies} policies)")
                else:
                    logger.error("❌ Cache policies test failed")
                    return False
                
                # Test backup policies
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.backup_policies")
                backup_policies = cursor.fetchone()[0]
                if backup_policies > 0:
                    logger.info(f"✅ Backup policies test passed ({backup_policies} policies)")
                else:
                    logger.error("❌ Backup policies test failed")
                    return False
                
                # Test health monitoring
                cursor.execute("SELECT dbx_monitoring.collect_health_metrics()")
                health_result = cursor.fetchone()[0]
                if health_result.get("overall_health"):
                    logger.info("✅ Health monitoring test passed")
                else:
                    logger.error("❌ Health monitoring test failed")
                    return False
            
            conn.close()
            logger.info("✅ All basic tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Basic tests failed: {e}")
            return False
    
    def generate_configuration_files(self) -> bool:
        """Generate configuration files for the application"""
        logger.info("📝 Generating configuration files...")
        
        try:
            # Generate .env file
            env_content = f"""# DBX AI Aviation Database Configuration
# Generated by setup script

# Database Configuration
DATABASE_URL=postgresql://{self.config['app_user']}:{self.config['app_password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}
DB_HOST={self.config['host']}
DB_PORT={self.config['port']}
DB_NAME={self.config['database']}
DB_USER={self.config['app_user']}
DB_PASSWORD={self.config['app_password']}

# Redis Configuration
REDIS_URL={self.config['redis_url']}

# Security Configuration
JWT_SECRET_KEY={os.urandom(32).hex()}
ENCRYPTION_KEY={os.urandom(32).hex()}

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
API_VERSION=2.0.0

# Default Credentials (CHANGE IN PRODUCTION!)
DEFAULT_ADMIN_EMAIL=admin@dbx-ai.com
DEFAULT_ADMIN_PASSWORD=admin123

# Performance Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
CACHE_DEFAULT_TTL=3600
"""
            
            env_file_path = self.db_scripts_path.parent / ".env.database"
            with open(env_file_path, 'w') as f:
                f.write(env_content)
            
            logger.info(f"✅ Configuration file created: {env_file_path}")
            
            # Generate connection test script
            test_script_content = f"""#!/usr/bin/env python3
\"\"\"
Database Connection Test Script
\"\"\"

import asyncio
import sys
import os
sys.path.append('{self.db_scripts_path}')

from python_integration import DBXDatabaseClient, DatabaseConfig, CacheConfig, SecurityConfig

async def test_connection():
    db_config = DatabaseConfig(
        database_url="postgresql+asyncpg://{self.config['app_user']}:{self.config['app_password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
    )
    cache_config = CacheConfig()
    security_config = SecurityConfig()
    
    client = DBXDatabaseClient(db_config, cache_config, security_config)
    
    try:
        await client.initialize()
        health = await client.health_check()
        print(f"Database Status: {{health['overall_status']}}")
        print(f"Connection Test: {'✅ PASSED' if health['overall_status'] == 'healthy' else '❌ FAILED'}")
        return health['overall_status'] == 'healthy'
    except Exception as e:
        print(f"Connection Test: ❌ FAILED - {{e}}")
        return False
    finally:
        await client.close()

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
"""
            
            test_script_path = self.db_scripts_path / "test_connection.py"
            with open(test_script_path, 'w') as f:
                f.write(test_script_content)
            
            # Make test script executable
            os.chmod(test_script_path, 0o755)
            
            logger.info(f"✅ Test script created: {test_script_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration file generation failed: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run the complete database setup process"""
        logger.info("🚀 Starting DBX AI Aviation Database Setup")
        logger.info("=" * 60)
        
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Database Creation", self.create_database),
            ("Schema Installation", self.install_database_schema),
            ("Application User", self.create_application_user),
            ("Installation Verification", self.verify_installation),
            ("Basic Tests", self.run_basic_tests),
            ("Configuration Files", self.generate_configuration_files)
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
        
        # Print summary
        self._print_setup_summary()
        
        return True
    
    def _print_setup_summary(self):
        """Print setup summary and next steps"""
        logger.info("\n📊 Setup Summary:")
        logger.info(f"  • Database: {self.config['database']} on {self.config['host']}:{self.config['port']}")
        logger.info(f"  • Application User: {self.config['app_user']}")
        logger.info(f"  • Redis URL: {self.config['redis_url']}")
        
        logger.info("\n🔑 Default Credentials (CHANGE IN PRODUCTION!):")
        logger.info("  • Admin User: admin@dbx-ai.com / admin123")
        logger.info(f"  • Database User: {self.config['app_user']} / {self.config['app_password']}")
        
        logger.info("\n📝 Configuration Files Created:")
        logger.info(f"  • Environment: {self.db_scripts_path.parent}/.env.database")
        logger.info(f"  • Test Script: {self.db_scripts_path}/test_connection.py")
        
        logger.info("\n⚠️  Important Next Steps:")
        logger.info("  1. Change all default passwords")
        logger.info("  2. Configure SSL/TLS certificates")
        logger.info("  3. Set up backup storage locations")
        logger.info("  4. Configure monitoring alerts")
        logger.info("  5. Review security settings")
        
        logger.info("\n🧪 Test Your Installation:")
        logger.info(f"  python {self.db_scripts_path}/test_connection.py")
        
        logger.info("\n🚀 Your production-ready aviation AI database is ready!")

def main():
    """Main setup function"""
    print("🚁 DBX AI Aviation Database Setup")
    print("=" * 50)
    
    # Load configuration from command line or environment
    config = {}
    
    # Parse command line arguments (basic implementation)
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("""
Usage: python setup_database.py [options]

Environment Variables:
  DB_HOST          Database host (default: localhost)
  DB_PORT          Database port (default: 5432)
  DB_NAME          Database name (default: dbx_aviation)
  DB_USER          Database superuser (default: postgres)
  DB_PASSWORD      Database password (default: password)
  DB_APP_USER      Application user (default: dbx_app_user)
  DB_APP_PASSWORD  Application password (default: change_me_in_production)
  REDIS_URL        Redis URL (default: redis://localhost:6379)
  CREATE_DATABASE  Create database (default: true)
  RUN_TESTS        Run tests (default: true)

Examples:
  # Basic setup with defaults
  python setup_database.py
  
  # Setup with custom database
  DB_NAME=my_aviation_db python setup_database.py
  
  # Setup without creating database
  CREATE_DATABASE=false python setup_database.py
            """)
            return
    
    # Initialize and run setup
    setup = DatabaseSetup(config)
    
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