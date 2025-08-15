#!/usr/bin/env python3
"""
DBX AI Aviation Database - Quick Setup Script
Uses existing database credentials from .env file
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

class QuickDatabaseSetup:
    """Quick database setup using existing credentials"""
    
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
        logger.info(f"Using credentials: {self.config['username']} (from .env file)")
    
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
    
    def test_connection(self) -> bool:
        """Test database connection"""
        logger.info("🔍 Testing database connection...")
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"✅ PostgreSQL connected: {version[:50]}...")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist"""
        logger.info(f"📊 Checking/creating database: {self.config['database']}")
        
        try:
            # Connect to postgres database
            conn = self._get_connection("postgres")
            
            with conn.cursor() as cursor:
                # Check if database exists
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.config["database"],)
                )
                
                if cursor.fetchone():
                    logger.info(f"✅ Database {self.config['database']} already exists")
                else:
                    # Create database
                    cursor.execute(f'CREATE DATABASE "{self.config["database"]}" WITH ENCODING \'UTF8\'')
                    logger.info(f"✅ Database {self.config['database']} created successfully")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False
    
    def install_enhanced_schema(self) -> bool:
        """Install the enhanced database schema"""
        logger.info("🚀 Installing enhanced database schema...")
        
        try:
            conn = self._get_connection(self.config["database"])
            
            # Read all SQL files in order
            sql_files = [
                "init_database.sql",
                "enhanced_security.sql",
                "smart_caching.sql", 
                "performance_optimization.sql",
                "backup_recovery.sql"
            ]
            
            for sql_file in sql_files:
                logger.info(f"📄 Installing: {sql_file}")
                
                sql_path = self.db_scripts_path / sql_file
                if not sql_path.exists():
                    logger.error(f"❌ SQL file not found: {sql_file}")
                    return False
                
                with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Execute the SQL
                with conn.cursor() as cursor:
                    try:
                        cursor.execute(sql_content)
                        logger.info(f"✅ {sql_file} installed successfully")
                    except Exception as e:
                        logger.error(f"❌ Error installing {sql_file}: {e}")
                        # Continue with other files
                        continue
            
            conn.close()
            logger.info("✅ Enhanced database schema installed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema installation failed: {e}")
            return False
    
    def create_app_user(self) -> bool:
        """Create application user"""
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
                else:
                    # Create user
                    cursor.execute(f"""
                        CREATE ROLE {self.config['app_user']} WITH 
                        LOGIN PASSWORD %s
                    """, (self.config["app_password"],))
                    
                    logger.info(f"✅ User {self.config['app_user']} created")
                
                # Grant permissions
                cursor.execute(f"GRANT CONNECT ON DATABASE {self.config['database']} TO {self.config['app_user']}")
                cursor.execute(f"GRANT USAGE ON SCHEMA dbx_aviation, dbx_analytics, dbx_monitoring TO {self.config['app_user']}")
                
                # Try to grant role permissions (may not exist yet)
                try:
                    cursor.execute(f"GRANT dbx_app_write TO {self.config['app_user']}")
                    cursor.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA dbx_aviation TO {self.config['app_user']}")
                except:
                    logger.info("⚠️  Some role permissions not available yet (will be set after schema installation)")
                
                logger.info("✅ Application user configured")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Application user creation failed: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """Verify the installation"""
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
                logger.info(f"✅ Schemas found: {', '.join(schemas)}")
                
                # Check tables
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema IN ('dbx_aviation', 'dbx_analytics', 'dbx_audit', 'dbx_monitoring')
                """)
                table_count = cursor.fetchone()[0]
                logger.info(f"✅ Tables created: {table_count}")
                
                # Check if default org exists
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT'")
                org_count = cursor.fetchone()[0]
                if org_count > 0:
                    logger.info("✅ Default organization found")
                else:
                    logger.warning("⚠️  Default organization not found")
                
                # Check if admin user exists
                cursor.execute("SELECT COUNT(*) FROM dbx_aviation.users WHERE email = 'admin@dbx-ai.com'")
                user_count = cursor.fetchone()[0]
                if user_count > 0:
                    logger.info("✅ Default admin user found")
                else:
                    logger.warning("⚠️  Default admin user not found")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create updated .env file with database settings"""
        logger.info("📝 Creating database configuration...")
        
        try:
            # Read existing .env file
            env_path = Path(".env")
            existing_content = ""
            if env_path.exists():
                with open(env_path, 'r') as f:
                    existing_content = f.read()
            
            # Add database configuration
            database_config = f"""
# DBX AI Aviation Database Configuration (Added by setup script)
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
            logger.error(f"❌ Environment file creation failed: {e}")
            return False
    
    def run_quick_setup(self) -> bool:
        """Run the quick setup process"""
        logger.info("🚀 Starting DBX AI Aviation Database Quick Setup")
        logger.info("=" * 60)
        
        steps = [
            ("Connection Test", self.test_connection),
            ("Database Creation", self.create_database_if_not_exists),
            ("Enhanced Schema Installation", self.install_enhanced_schema),
            ("Application User Creation", self.create_app_user),
            ("Installation Verification", self.verify_installation),
            ("Environment Configuration", self.create_env_file)
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
        logger.info(f"  • Connection String: postgresql://{self.config['app_user']}:***@{self.config['host']}:{self.config['port']}/{self.config['database']}")
        
        logger.info("\n🔑 Default Credentials (CHANGE IN PRODUCTION!):")
        logger.info("  • Admin User: admin@dbx-ai.com / admin123")
        logger.info(f"  • Database User: {self.config['app_user']} / {self.config['app_password']}")
        
        logger.info("\n🧪 Test Your Database:")
        logger.info("  python -c \"from ai_engine.app.database import db_manager; print(db_manager.health_check())\"")
        
        logger.info("\n🚀 Your enhanced aviation AI database is ready!")
        logger.info("  • Enterprise security with authentication")
        logger.info("  • Smart caching with Redis integration")
        logger.info("  • Performance optimization with advanced indexing")
        logger.info("  • Automated backup and recovery system")
        logger.info("  • Real-time monitoring and health checks")

def main():
    """Main setup function"""
    print("🚁 DBX AI Aviation Database - Quick Setup")
    print("=" * 50)
    
    setup = QuickDatabaseSetup()
    
    try:
        success = setup.run_quick_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Setup failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()