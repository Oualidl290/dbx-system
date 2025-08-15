# 🚀 PostgreSQL Setup Guide - DBX AI Aviation System

## ⚡ **Quick Setup (5 Minutes)**

### **Step 1: Install PostgreSQL**

**Windows (Recommended):**
```cmd
# Option 1: Download installer from postgresql.org
# https://www.postgresql.org/download/windows/

# Option 2: Use winget (Windows 10/11)
winget install PostgreSQL.PostgreSQL

# Option 3: Use chocolatey
choco install postgresql
```

**After installation:**
- Default user: `postgres`
- Default port: `5432`
- Remember the password you set during installation!

### **Step 2: Install Python Dependencies**
```cmd
pip install psycopg2-binary sqlalchemy python-dotenv
```

### **Step 3: Set Environment Variables**
```cmd
# Create .env file in your project root
echo DB_HOST=localhost >> .env
echo DB_PORT=5432 >> .env
echo DB_USER=postgres >> .env
echo DB_PASSWORD=your_postgres_password >> .env
```

### **Step 4: Run Automated Setup**
```cmd
python database/setup_database.py
```

**Expected Output:**
```
🚀 Starting DBX AI Database Setup
==================================================
Step: Creating database
✅ Creating database completed
Step: Running schema setup
✅ Running schema setup completed
Step: Creating application users
✅ Creating application users completed
Step: Creating sample data
✅ Creating sample data completed
Step: Verifying setup
✅ Verifying setup completed
==================================================
🎉 Database setup completed successfully!
```

### **Step 5: Update Your .env File**
```cmd
# Add these lines to your .env file (use credentials from database/credentials.txt)
echo DATABASE_URL=postgresql://dbx_api_service:your_generated_password@localhost:5432/dbx_aviation >> .env
echo DBX_DEFAULT_API_KEY=your_generated_api_key >> .env
```

---

## 🧪 **Test Your Setup**

### **Test 1: Database Connection**
```cmd
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user='dbx_api_service',
    password='your_password_from_credentials_file',
    database='dbx_aviation'
)
print('✅ Database connection successful!')
conn.close()
"
```

### **Test 2: Verify Tables**
```cmd
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user='dbx_api_service',
    password='your_password_from_credentials_file',
    database='dbx_aviation'
)
cursor = conn.cursor()
cursor.execute(\"\"\"
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema LIKE 'dbx_%'
    ORDER BY table_schema, table_name
\"\"\")
tables = cursor.fetchall()
print('📊 Database tables:')
for schema, table in tables:
    print(f'   - {schema}.{table}')
conn.close()
"
```

### **Test 3: API Integration**
```cmd
# Update your FastAPI app to use PostgreSQL
python deploy.py

# Test the API
curl http://localhost:8000/api/v2/system/status
```

---

## 🔧 **Manual Setup (If Automated Fails)**

### **1. Create Database Manually**
```cmd
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE dbx_aviation WITH ENCODING 'UTF8';
\c dbx_aviation;
\i database/init_database.sql
\q
```

### **2. Create Users Manually**
```cmd
psql -U postgres -d dbx_aviation

# Create application users
CREATE USER dbx_api_service WITH PASSWORD 'your_secure_password';
CREATE USER dbx_analytics_service WITH PASSWORD 'your_secure_password';

# Grant permissions
GRANT dbx_app_write TO dbx_api_service;
GRANT dbx_app_read TO dbx_analytics_service;
\q
```

---

## 🎯 **What You Get**

### **Database Structure:**
```
📊 dbx_aviation (Database)
├── 🏢 dbx_aviation schema (Main tables)
│   ├── organizations (Multi-tenant support)
│   ├── aircraft_registry (Aircraft management)
│   ├── flight_sessions (Flight tracking)
│   ├── flight_telemetry (Sensor data)
│   ├── ml_analysis_results (AI predictions)
│   └── api_requests (Usage tracking)
├── 📈 dbx_analytics schema (Analytics functions)
├── 🔍 dbx_audit schema (Audit trails)
└── 📦 dbx_archive schema (Data archival)
```

### **Security Features:**
- ✅ **Multi-tenant isolation** (Row Level Security)
- ✅ **Encrypted API keys** (pgcrypto)
- ✅ **Complete audit trails** (Every action logged)
- ✅ **Role-based access** (Separate read/write users)

### **Sample Data:**
- Default organization: `DBX_DEFAULT`
- Sample aircraft: `N123DBX` (multirotor), `N456DBX` (fixed wing)
- API key for testing (saved in `database/api_key.txt`)

---

## 🚨 **Troubleshooting**

### **Issue: Connection Refused**
```cmd
# Check if PostgreSQL is running
# Windows:
services.msc
# Look for "postgresql" service and start it

# Or restart PostgreSQL
net stop postgresql-x64-15
net start postgresql-x64-15
```

### **Issue: Authentication Failed**
```cmd
# Reset postgres password
psql -U postgres
ALTER USER postgres PASSWORD 'newpassword';
```

### **Issue: Database Doesn't Exist**
```cmd
# Create database manually
createdb -U postgres dbx_aviation
```

### **Issue: Permission Denied**
```cmd
# Check user permissions
psql -U postgres -d dbx_aviation
\du  # List users and roles
```

---

## 🔄 **Update FastAPI Integration**

### **Update ai-engine/app/database.py:**
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use PostgreSQL instead of in-memory
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://dbx_api_service:password@localhost:5432/dbx_aviation'
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### **Update ai-engine/app/api.py:**
```python
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db

@app.post("/api/v2/analyze")
async def analyze_flight(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Now you can save results to PostgreSQL
    # Save flight session
    # Save analysis results
    # Return response
    pass
```

---

## 🎉 **Success Checklist**

- [ ] PostgreSQL installed and running
- [ ] Database `dbx_aviation` created
- [ ] All tables and schemas created
- [ ] Application users created with proper permissions
- [ ] Sample data inserted
- [ ] Credentials files generated and secured
- [ ] Environment variables configured
- [ ] Database connection test passes
- [ ] API integration updated
- [ ] System ready for production use

---

## 🚀 **Next Steps**

1. **Secure Your Credentials**
   - Move `database/credentials.txt` to secure location
   - Add to `.gitignore`
   - Use environment variables in production

2. **Enable Monitoring**
   - Set up database monitoring
   - Configure alerts for performance issues
   - Monitor connection pool usage

3. **Backup Strategy**
   - Set up automated backups
   - Test restore procedures
   - Configure point-in-time recovery

4. **Production Deployment**
   - Use connection pooling (PgBouncer)
   - Enable SSL connections
   - Configure firewall rules
   - Set up read replicas for analytics

**Your production-grade PostgreSQL database is now ready! 🎯**

---

*This setup creates a enterprise-grade, multi-tenant, secure database system ready for your aviation AI workloads.*"