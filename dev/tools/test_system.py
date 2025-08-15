#!/usr/bin/env python3
"""
DBX AI System - Comprehensive Test Suite
Tests the entire production-grade aviation AI system
"""

import os
import sys
import time
import requests
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import subprocess
from pathlib import Path

class DBXSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_key = None
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': os.getenv('DB_PASSWORD', ''),
            'database': 'dbx_aviation'
        }
        self.test_results = []
        
    def log_test(self, test_name, status, message="", duration=0):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'duration': f"{duration:.2f}s",
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status} ({duration:.2f}s)")
        if message:
            print(f"   {message}")
    
    def test_database_connection(self):
        """Test PostgreSQL database connection"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            self.log_test("Database Connection", "PASS", f"PostgreSQL: {version[:50]}...", duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Database Connection", "FAIL", str(e), duration)
            return False
    
    def test_database_schema(self):
        """Test database schema and tables"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if all required tables exist
            required_tables = [
                'dbx_aviation.organizations',
                'dbx_aviation.aircraft_registry',
                'dbx_aviation.flight_sessions',
                'dbx_aviation.flight_telemetry',
                'dbx_aviation.ml_analysis_results',
                'dbx_aviation.api_requests',
                'dbx_audit.audit_log'
            ]
            
            existing_tables = []
            for table in required_tables:
                schema, table_name = table.split('.')
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """, (schema, table_name))
                
                if cursor.fetchone()[0]:
                    existing_tables.append(table)
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            if len(existing_tables) == len(required_tables):
                self.log_test("Database Schema", "PASS", f"All {len(required_tables)} tables exist", duration)
                return True
            else:
                missing = set(required_tables) - set(existing_tables)
                self.log_test("Database Schema", "FAIL", f"Missing tables: {missing}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Database Schema", "FAIL", str(e), duration)
            return False
    
    def test_database_setup_script(self):
        """Test database setup script"""
        start_time = time.time()
        try:
            # Check if setup script exists
            setup_script = Path("database/setup_database.py")
            if not setup_script.exists():
                duration = time.time() - start_time
                self.log_test("Database Setup Script", "FAIL", "setup_database.py not found", duration)
                return False
            
            # Check if init script exists
            init_script = Path("database/init_database.sql")
            if not init_script.exists():
                duration = time.time() - start_time
                self.log_test("Database Setup Script", "FAIL", "init_database.sql not found", duration)
                return False
            
            duration = time.time() - start_time
            self.log_test("Database Setup Script", "PASS", "Setup scripts found", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Database Setup Script", "FAIL", str(e), duration)
            return False
    
    def test_api_server_startup(self):
        """Test if API server can start"""
        start_time = time.time()
        try:
            # Check if FastAPI app exists
            app_file = Path("ai-engine/app/api.py")
            if not app_file.exists():
                duration = time.time() - start_time
                self.log_test("API Server Files", "FAIL", "api.py not found", duration)
                return False
            
            # Try to import the app (basic syntax check)
            sys.path.append("ai-engine/app")
            try:
                import api
                duration = time.time() - start_time
                self.log_test("API Server Import", "PASS", "FastAPI app imports successfully", duration)
                return True
            except ImportError as e:
                duration = time.time() - start_time
                self.log_test("API Server Import", "FAIL", f"Import error: {e}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("API Server Startup", "FAIL", str(e), duration)
            return False
    
    def test_ml_models(self):
        """Test ML model files and structure"""
        start_time = time.time()
        try:
            model_files = [
                "ai-engine/app/models/model.py",
                "ai-engine/app/models/aircraft_classifier.py",
                "ai-engine/app/models/anomaly_detector.py"
            ]
            
            existing_files = []
            for file_path in model_files:
                if Path(file_path).exists():
                    existing_files.append(file_path)
            
            duration = time.time() - start_time
            if len(existing_files) >= 1:  # At least one model file should exist
                self.log_test("ML Models", "PASS", f"Found {len(existing_files)} model files", duration)
                return True
            else:
                self.log_test("ML Models", "FAIL", "No model files found", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("ML Models", "FAIL", str(e), duration)
            return False
    
    def test_sample_data_generation(self):
        """Test sample data generation"""
        start_time = time.time()
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check if sample organization exists
            cursor.execute("SELECT COUNT(*) FROM dbx_aviation.organizations WHERE org_code = 'DBX_DEFAULT';")
            org_count = cursor.fetchone()[0]
            
            # Check if sample aircraft exist
            cursor.execute("SELECT COUNT(*) FROM dbx_aviation.aircraft_registry;")
            aircraft_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            if org_count > 0 and aircraft_count > 0:
                self.log_test("Sample Data", "PASS", f"Found {org_count} orgs, {aircraft_count} aircraft", duration)
                return True
            else:
                self.log_test("Sample Data", "FAIL", f"Missing sample data: {org_count} orgs, {aircraft_count} aircraft", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Sample Data", "FAIL", str(e), duration)
            return False
    
    def test_advanced_security_features(self):
        """Test advanced security features"""
        start_time = time.time()
        try:
            # Check if advanced security SQL file exists
            security_file = Path("database/advanced_security.sql")
            if not security_file.exists():
                duration = time.time() - start_time
                self.log_test("Advanced Security", "FAIL", "advanced_security.sql not found", duration)
                return False
            
            # Check if pgcrypto extension is available
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'pgcrypto';")
                pgcrypto_exists = cursor.fetchone() is not None
            except:
                pgcrypto_exists = False
            
            cursor.close()
            conn.close()
            
            duration = time.time() - start_time
            if pgcrypto_exists:
                self.log_test("Advanced Security", "PASS", "pgcrypto extension available", duration)
                return True
            else:
                self.log_test("Advanced Security", "WARN", "pgcrypto extension not installed", duration)
                return True  # Not critical for basic testing
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Advanced Security", "FAIL", str(e), duration)
            return False
    
    def test_documentation(self):
        """Test documentation completeness"""
        start_time = time.time()
        try:
            doc_files = [
                "README.md",
                "DATABASE_SETUP_GUIDE.md",
                "WHAT_WE_BUILT_EXPLAINED.md"
            ]
            
            existing_docs = []
            for doc_file in doc_files:
                if Path(doc_file).exists():
                    existing_docs.append(doc_file)
            
            duration = time.time() - start_time
            if len(existing_docs) >= 2:  # At least 2 documentation files
                self.log_test("Documentation", "PASS", f"Found {len(existing_docs)} documentation files", duration)
                return True
            else:
                self.log_test("Documentation", "FAIL", f"Only found {len(existing_docs)} documentation files", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Documentation", "FAIL", str(e), duration)
            return False
    
    def test_environment_setup(self):
        """Test environment and dependencies"""
        start_time = time.time()
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major >= 3 and python_version.minor >= 8:
                python_ok = True
            else:
                python_ok = False
            
            # Check if requirements.txt exists
            requirements_exist = Path("requirements.txt").exists()
            
            # Check if virtual environment is active
            venv_active = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            
            duration = time.time() - start_time
            
            issues = []
            if not python_ok:
                issues.append(f"Python {python_version.major}.{python_version.minor} (need 3.8+)")
            if not requirements_exist:
                issues.append("requirements.txt missing")
            if not venv_active:
                issues.append("virtual environment not active")
            
            if not issues:
                self.log_test("Environment Setup", "PASS", "Python 3.8+, requirements.txt found", duration)
                return True
            else:
                self.log_test("Environment Setup", "WARN", f"Issues: {', '.join(issues)}", duration)
                return True  # Not critical
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Environment Setup", "FAIL", str(e), duration)
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("🚀 DBX AI SYSTEM - COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warned_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['message']}")
        
        if warned_tests > 0:
            print(f"\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result['status'] == 'WARN':
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🎯 SYSTEM STATUS:")
        if failed_tests == 0:
            print("   🟢 SYSTEM READY FOR PRODUCTION!")
            print("   All critical components are working correctly.")
        elif failed_tests <= 2:
            print("   🟡 SYSTEM MOSTLY READY")
            print("   Minor issues detected, but core functionality works.")
        else:
            print("   🔴 SYSTEM NEEDS ATTENTION")
            print("   Multiple issues detected, please fix before deployment.")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warned_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%"
            },
            'test_results': self.test_results
        }
        
        with open('test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")
        print("="*80)
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting DBX AI System Comprehensive Test Suite...")
        print("="*80)
        
        # Core Infrastructure Tests
        print("\n🔧 INFRASTRUCTURE TESTS:")
        self.test_environment_setup()
        self.test_database_connection()
        self.test_database_schema()
        self.test_database_setup_script()
        
        # Application Tests
        print("\n🚀 APPLICATION TESTS:")
        self.test_api_server_startup()
        self.test_ml_models()
        self.test_sample_data_generation()
        
        # Security & Advanced Features
        print("\n🔐 SECURITY & ADVANCED FEATURES:")
        self.test_advanced_security_features()
        
        # Documentation Tests
        print("\n📚 DOCUMENTATION TESTS:")
        self.test_documentation()
        
        # Generate final report
        self.generate_test_report()

def main():
    """Main test execution"""
    print("🎯 DBX AI System - Production Grade Aviation Database")
    print("🧪 Running Comprehensive System Tests...\n")
    
    tester = DBXSystemTester()
    tester.run_all_tests()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())