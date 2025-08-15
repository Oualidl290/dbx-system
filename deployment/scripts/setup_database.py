#!/usr/bin/env python3
"""
Database Setup Script for DBX AI Multi-Aircraft System
Handles PostgreSQL database initialization and configuration
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import hashlib
import secrets
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSetup:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': 'dbx_aviation'
        }
        
    def create_database(self):
        """Create the main database if it doesn't exist"""
        logger.info("Creating database if not exists...")
        
        try:
            # Connect to postgres database to create our database
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_config['database'],))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE {self.db_config['database']} WITH ENCODING 'UTF8'")
                logger.info(f"Database '{self.db_config['database']}' created successfully")
            else:
                logger.info(f"Database '{self.db_config['database']}' already exists")
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
            
        return True
    
    def run_sql_file(self, sql_file_path):
        """Execute SQL file"""
        logger.info(f"Executing SQL file: {sql_file_path}")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            with open(sql_file_path, 'r') as file:
                sql_content = file.read()
                cursor.execute(sql_content)
                
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"SQL file executed successfully: {sql_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing SQL file {sql_file_path}: {e}")
            return False
    
    def create_application_users(self):
        """Create application users with proper permissions"""
        logger.info("Creating application users...")
        
        # Generate secure passwords
        api_password = secrets.token_urlsafe(32)
        analytics_password = secrets.token_urlsafe(32)
        
        sql_commands = [
            # Create application users
            f"CREATE USER dbx_api_service WITH PASSWORD '{api_password}';",
            f"CREATE USER dbx_analytics_service WITH PASSWORD '{analytics_password}';",
            
            # Grant roles
            "GRANT dbx_app_write TO dbx_api_service;",
            "GRANT dbx_app_read TO dbx_analytics_service;",
            
            # Additional permissions
            "GRANT CONNECT ON DATABASE dbx_aviation TO dbx_api_service, dbx_analytics_service;",
        ]
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            for sql in sql_commands:
                try:
                    cursor.execute(sql)
                except psycopg2.errors.DuplicateObject:
                    logger.info("User already exists, skipping...")
                    conn.rollback()
                    continue
                    
            conn.commit()
            cursor.close()
            conn.close()
            
            # Save credentials to file
            credentials_file = Path("database/credentials.txt")
            with open(credentials_file, 'w') as f:
                f.write("# DBX AI Database Credentials\n")
                f.write("# KEEP THIS FILE SECURE!\n\n")
                f.write(f"DBX_API_USER=dbx_api_service\n")
                f.write(f"DBX_API_PASSWORD={api_password}\n")
                f.write(f"DBX_ANALYTICS_USER=dbx_analytics_service\n")
                f.write(f"DBX_ANALYTICS_PASSWORD={analytics_password}\n")
                f.write(f"DBX_DB_HOST={self.db_config['host']}\n")
                f.write(f"DBX_DB_PORT={self.db_config['port']}\n")
                f.write(f"DBX_DB_NAME={self.db_config['database']}\n")
            
            logger.info(f"Application users created. Credentials saved to {credentials_file}")
            logger.warning("IMPORTANT: Keep the credentials file secure!")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating application users: {e}")
            return False
    
    def create_sample_data(self):
        """Create sample data for testing"""
        logger.info("Creating sample data...")
        
        # Generate API key for default org
        api_key = f"dbx_{secrets.token_urlsafe(32)}"
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        sample_data_sql = f"""
        -- Update default organization with proper API key
        UPDATE dbx_aviation.organizations 
        SET api_key_hash = '{api_key_hash}'
        WHERE org_code = 'DBX_DEFAULT';
        
        -- Insert sample aircraft
        INSERT INTO dbx_aviation.aircraft_registry (
            org_id, 
            registration_number, 
            aircraft_type, 
            manufacturer, 
            model,
            specifications
        ) 
        SELECT 
            org_id,
            'N123DBX',
            'multirotor',
            'DJI',
            'Matrice 300',
            '{{"motors": {{"count": 4, "type": "brushless"}}, "sensors": ["gps", "imu", "camera"]}}'::jsonb
        FROM dbx_aviation.organizations 
        WHERE org_code = 'DBX_DEFAULT'
        ON CONFLICT (org_id, registration_number) DO NOTHING;
        
        -- Insert sample fixed wing aircraft
        INSERT INTO dbx_aviation.aircraft_registry (
            org_id, 
            registration_number, 
            aircraft_type, 
            manufacturer, 
            model,
            specifications
        ) 
        SELECT 
            org_id,
            'N456DBX',
            'fixed_wing',
            'SenseFly',
            'eBee X',
            '{{"motors": {{"count": 1, "type": "electric"}}, "control_surfaces": ["elevator", "aileron"], "sensors": ["gps", "imu", "pitot"]}}'::jsonb
        FROM dbx_aviation.organizations 
        WHERE org_code = 'DBX_DEFAULT'
        ON CONFLICT (org_id, registration_number) DO NOTHING;
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(sample_data_sql)
            conn.commit()
            cursor.close()
            conn.close()
            
            # Save API key
            api_key_file = Path("database/api_key.txt")
            with open(api_key_file, 'w') as f:
                f.write(f"# Default Organization API Key\n")
                f.write(f"# Use this for testing the API\n\n")
                f.write(f"DBX_DEFAULT_API_KEY={api_key}\n")
            
            logger.info(f"Sample data created. API key saved to {api_key_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            return False
    
    def verify_setup(self):
        """Verify database setup"""
        logger.info("Verifying database setup...")
        
        verification_sql = """
        SELECT 
            'organizations' as table_name, COUNT(*) as count 
        FROM dbx_aviation.organizations
        UNION ALL
        SELECT 
            'aircraft_registry' as table_name, COUNT(*) as count 
        FROM dbx_aviation.aircraft_registry
        UNION ALL
        SELECT 
            'flight_sessions' as table_name, COUNT(*) as count 
        FROM dbx_aviation.flight_sessions;
        """
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(verification_sql)
            results = cursor.fetchall()
            
            logger.info("Database verification results:")
            for table_name, count in results:
                logger.info(f"  {table_name}: {count} records")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying setup: {e}")
            return False
    
    def setup_complete(self):
        """Complete database setup process"""
        logger.info("🚀 Starting DBX AI Database Setup")
        logger.info("=" * 50)
        
        steps = [
            ("Creating database", self.create_database),
            ("Running schema setup", lambda: self.run_sql_file("database/init_database.sql")),
            ("Creating application users", self.create_application_users),
            ("Creating sample data", self.create_sample_data),
            ("Verifying setup", self.verify_setup)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Failed at step: {step_name}")
                return False
            logger.info(f"✅ {step_name} completed")
            
        logger.info("=" * 50)
        logger.info("🎉 Database setup completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Update your .env file with database credentials")
        logger.info("2. Test the database connection")
        logger.info("3. Update the FastAPI app to use PostgreSQL")
        logger.info("")
        logger.info("Files created:")
        logger.info("- database/credentials.txt (application user passwords)")
        logger.info("- database/api_key.txt (default API key for testing)")
        logger.info("")
        logger.warning("⚠️  IMPORTANT: Keep credential files secure!")
        
        return True

def main():
    """Main setup function"""
    # Check if PostgreSQL is available
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    
    # Create database directory if it doesn't exist
    os.makedirs("database", exist_ok=True)
    
    # Check if init_database.sql exists
    if not os.path.exists("database/init_database.sql"):
        logger.error("database/init_database.sql not found!")
        logger.error("Make sure you have the SQL schema file in the database/ directory")
        sys.exit(1)
    
    # Get database connection info
    if not os.getenv('DB_PASSWORD'):
        logger.warning("DB_PASSWORD not set in environment")
        password = input("Enter PostgreSQL password for user 'postgres': ")
        os.environ['DB_PASSWORD'] = password
    
    # Run setup
    setup = DatabaseSetup()
    success = setup.setup_complete()
    
    if success:
        logger.info("Database setup completed successfully! 🎉")
        sys.exit(0)
    else:
        logger.error("Database setup failed! ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()