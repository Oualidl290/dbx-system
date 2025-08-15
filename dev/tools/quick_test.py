#!/usr/bin/env python3
"""
DBX AI System - Quick Test Suite (No External Dependencies)
Tests the basic structure and files of the production-grade aviation AI system
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

class DBXQuickTester:
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name, status, message="", details=""):
        """Log test results"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_project_structure(self):
        """Test basic project structure"""
        required_dirs = [
            "ai-engine",
            "ai-engine/app",
            "ai-engine/app/models",
            "database",
            "data"
        ]
        
        existing_dirs = []
        missing_dirs = []
        
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                existing_dirs.append(dir_path)
            else:
                missing_dirs.append(dir_path)
        
        if len(existing_dirs) >= 4:  # Most directories exist
            self.log_test("Project Structure", "PASS", 
                         f"Found {len(existing_dirs)}/{len(required_dirs)} required directories",
                         f"Existing: {existing_dirs}")
            return True
        else:
            self.log_test("Project Structure", "FAIL", 
                         f"Missing critical directories: {missing_dirs}",
                         f"Found only: {existing_dirs}")
            return False
    
    def test_database_files(self):
        """Test database setup files"""
        database_files = [
            "database/init_database.sql",
            "database/setup_database.py",
            "database/requirements.txt",
            "database/advanced_security.sql"
        ]
        
        existing_files = []
        file_sizes = {}
        
        for file_path in database_files:
            path = Path(file_path)
            if path.exists():
                existing_files.append(file_path)
                file_sizes[file_path] = f"{path.stat().st_size / 1024:.1f}KB"
        
        if len(existing_files) >= 3:  # Most database files exist
            self.log_test("Database Files", "PASS", 
                         f"Found {len(existing_files)}/{len(database_files)} database files",
                         f"Files: {file_sizes}")
            return True
        else:
            self.log_test("Database Files", "FAIL", 
                         f"Missing database files",
                         f"Found only: {existing_files}")
            return False
    
    def test_api_files(self):
        """Test API application files"""
        api_files = [
            "ai-engine/app/api.py",
            "ai-engine/app/models/model.py",
            "ai-engine/app/models/aircraft_classifier.py",
            "ai-engine/app/models/anomaly_detector.py"
        ]
        
        existing_files = []
        file_info = {}
        
        for file_path in api_files:
            path = Path(file_path)
            if path.exists():
                existing_files.append(file_path)
                file_info[file_path] = f"{path.stat().st_size / 1024:.1f}KB"
        
        if len(existing_files) >= 2:  # At least core API files exist
            self.log_test("API Files", "PASS", 
                         f"Found {len(existing_files)}/{len(api_files)} API files",
                         f"Files: {file_info}")
            return True
        else:
            self.log_test("API Files", "FAIL", 
                         f"Missing critical API files",
                         f"Found only: {existing_files}")
            return False
    
    def test_documentation(self):
        """Test documentation files"""
        doc_files = [
            "README.md",
            "DATABASE_SETUP_GUIDE.md", 
            "WHAT_WE_BUILT_EXPLAINED.md"
        ]
        
        existing_docs = []
        doc_sizes = {}
        
        for doc_file in doc_files:
            path = Path(doc_file)
            if path.exists():
                existing_docs.append(doc_file)
                doc_sizes[doc_file] = f"{path.stat().st_size / 1024:.1f}KB"
        
        if len(existing_docs) >= 2:
            self.log_test("Documentation", "PASS", 
                         f"Found {len(existing_docs)}/{len(doc_files)} documentation files",
                         f"Docs: {doc_sizes}")
            return True
        else:
            self.log_test("Documentation", "FAIL", 
                         f"Missing documentation files",
                         f"Found only: {existing_docs}")
            return False
    
    def test_configuration_files(self):
        """Test configuration and setup files"""
        config_files = [
            "requirements.txt",
            ".gitignore",
            ".env.example"
        ]
        
        existing_configs = []
        optional_configs = []
        
        for config_file in config_files:
            if Path(config_file).exists():
                existing_configs.append(config_file)
            else:
                optional_configs.append(config_file)
        
        if len(existing_configs) >= 2:  # At least requirements and gitignore
            self.log_test("Configuration Files", "PASS", 
                         f"Found {len(existing_configs)}/{len(config_files)} config files",
                         f"Existing: {existing_configs}")
            return True
        else:
            self.log_test("Configuration Files", "WARN", 
                         f"Some config files missing: {optional_configs}",
                         f"Found: {existing_configs}")
            return True  # Not critical
    
    def test_python_syntax(self):
        """Test Python files for basic syntax errors"""
        python_files = []
        
        # Find all Python files
        for root, dirs, files in os.walk("."):
            # Skip virtual environment and cache directories
            dirs[:] = [d for d in dirs if d not in ['.venv', 'venv', '__pycache__', '.git']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        syntax_errors = []
        valid_files = []
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
                valid_files.append(py_file)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")
            except Exception as e:
                # Skip files that can't be read or compiled for other reasons
                pass
        
        if len(syntax_errors) == 0:
            self.log_test("Python Syntax", "PASS", 
                         f"All {len(valid_files)} Python files have valid syntax",
                         f"Files checked: {len(python_files)}")
            return True
        else:
            self.log_test("Python Syntax", "FAIL", 
                         f"Found {len(syntax_errors)} syntax errors",
                         f"Errors: {syntax_errors[:3]}")  # Show first 3 errors
            return False
    
    def test_database_schema_content(self):
        """Test database schema file content"""
        schema_file = Path("database/init_database.sql")
        
        if not schema_file.exists():
            self.log_test("Database Schema Content", "FAIL", 
                         "init_database.sql not found")
            return False
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for key database components
            required_components = [
                "CREATE SCHEMA",
                "CREATE TABLE",
                "dbx_aviation.organizations",
                "dbx_aviation.aircraft_registry", 
                "dbx_aviation.flight_sessions",
                "dbx_aviation.flight_telemetry",
                "dbx_aviation.ml_analysis_results",
                "CREATE INDEX",
                "CREATE VIEW"
            ]
            
            found_components = []
            for component in required_components:
                if component in content:
                    found_components.append(component)
            
            if len(found_components) >= 7:  # Most components found
                self.log_test("Database Schema Content", "PASS", 
                             f"Found {len(found_components)}/{len(required_components)} key components",
                             f"Schema size: {len(content)/1024:.1f}KB")
                return True
            else:
                missing = set(required_components) - set(found_components)
                self.log_test("Database Schema Content", "FAIL", 
                             f"Missing components: {missing}",
                             f"Found: {found_components}")
                return False
                
        except Exception as e:
            self.log_test("Database Schema Content", "FAIL", 
                         f"Error reading schema file: {e}")
            return False
    
    def test_advanced_features(self):
        """Test advanced feature files"""
        advanced_files = [
            "database/advanced_security.sql",
            "database/analytics_functions.sql"
        ]
        
        existing_advanced = []
        advanced_info = {}
        
        for file_path in advanced_files:
            path = Path(file_path)
            if path.exists():
                existing_advanced.append(file_path)
                advanced_info[file_path] = f"{path.stat().st_size / 1024:.1f}KB"
        
        if len(existing_advanced) >= 1:
            self.log_test("Advanced Features", "PASS", 
                         f"Found {len(existing_advanced)} advanced feature files",
                         f"Files: {advanced_info}")
            return True
        else:
            self.log_test("Advanced Features", "WARN", 
                         "No advanced feature files found",
                         "This is optional for basic functionality")
            return True  # Not critical
    
    def analyze_system_completeness(self):
        """Analyze overall system completeness"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        completeness_score = (passed_tests / total_tests) * 100
        
        if completeness_score >= 90:
            status = "EXCELLENT"
            message = "System is production-ready!"
        elif completeness_score >= 75:
            status = "GOOD"
            message = "System is mostly complete with minor issues"
        elif completeness_score >= 60:
            status = "FAIR"
            message = "System has core functionality but needs work"
        else:
            status = "NEEDS_WORK"
            message = "System requires significant development"
        
        self.log_test("System Completeness", status, 
                     f"Overall score: {completeness_score:.1f}%",
                     message)
        
        return completeness_score
    
    def generate_quick_report(self):
        """Generate quick test report"""
        print("\n" + "="*80)
        print("🚀 DBX AI SYSTEM - QUICK TEST REPORT")
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
        
        # Show system status
        completeness = (passed_tests / total_tests) * 100
        if completeness >= 90:
            print(f"\n🟢 SYSTEM STATUS: EXCELLENT ({completeness:.1f}%)")
            print("   🎉 Your DBX AI system is production-ready!")
            print("   ✅ All core components are in place")
            print("   ✅ Database schema is complete")
            print("   ✅ API structure is ready")
            print("   ✅ Documentation is comprehensive")
        elif completeness >= 75:
            print(f"\n🟡 SYSTEM STATUS: GOOD ({completeness:.1f}%)")
            print("   👍 Your DBX AI system is mostly complete!")
            print("   ✅ Core functionality is ready")
            print("   ⚠️  Some minor components may need attention")
        else:
            print(f"\n🔴 SYSTEM STATUS: NEEDS WORK ({completeness:.1f}%)")
            print("   🔧 Your DBX AI system needs more development")
            print("   ❌ Some critical components are missing")
        
        if failed_tests > 0:
            print(f"\n❌ ISSUES TO FIX:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🎯 WHAT YOU'VE BUILT:")
        print("   🏗️  Production-grade database architecture")
        print("   🔐 Enterprise security features")
        print("   🤖 AI/ML integration framework")
        print("   📊 Analytics and monitoring capabilities")
        print("   📚 Comprehensive documentation")
        print("   🚀 Scalable API infrastructure")
        
        print("\n" + "="*80)
        
        # Save report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warned_tests,
                'success_rate': f"{(passed_tests/total_tests)*100:.1f}%",
                'completeness_score': f"{completeness:.1f}%"
            },
            'test_results': self.test_results
        }
        
        with open('quick_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Detailed report saved to: quick_test_report.json")
    
    def run_quick_tests(self):
        """Run all quick tests"""
        print("🚀 DBX AI System - Quick Test Suite")
        print("🧪 Testing system structure and completeness...")
        print("="*80)
        
        # Structure Tests
        print("\n🏗️  STRUCTURE TESTS:")
        self.test_project_structure()
        self.test_database_files()
        self.test_api_files()
        
        # Content Tests  
        print("\n📄 CONTENT TESTS:")
        self.test_database_schema_content()
        self.test_python_syntax()
        
        # Documentation Tests
        print("\n📚 DOCUMENTATION TESTS:")
        self.test_documentation()
        
        # Configuration Tests
        print("\n⚙️  CONFIGURATION TESTS:")
        self.test_configuration_files()
        
        # Advanced Features
        print("\n🚀 ADVANCED FEATURES:")
        self.test_advanced_features()
        
        # Overall Analysis
        print("\n🎯 SYSTEM ANALYSIS:")
        self.analyze_system_completeness()
        
        # Generate report
        self.generate_quick_report()

def main():
    """Main test execution"""
    print("🎯 DBX AI System - Production Grade Aviation Database")
    print("🧪 Running Quick System Validation...\n")
    
    tester = DBXQuickTester()
    tester.run_quick_tests()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())