# DBX AI Aviation System - Local Development Setup

This guide will help you set up the DBX AI Aviation System for local development with a complete Docker environment including PostgreSQL database, Redis cache, and the application.

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** (usually included with Docker Desktop)
- **Git** (to clone the repository)
- At least **4GB RAM** available for Docker
- **8GB free disk space**

### Automated Setup

#### Windows
```bash
# Run the automated setup script
scripts\setup-local.bat
```

#### Linux/Mac
```bash
# Make the script executable
chmod +x scripts/setup-local.sh

# Run the automated setup script
./scripts/setup-local.sh
```

The automated script will:
1. ✅ Check Docker installation
2. ✅ Create necessary directories
3. ✅ Set up environment configuration
4. ✅ Build and start all services
5. ✅ Wait for services to be healthy
6. ✅ Display connection information

## 🔧 Manual Setup

If you prefer to set up manually or need to troubleshoot:

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd dbx-ai-aviation-system
```

### 2. Create Environment File
```bash
# Copy the local environment template
cp .env.local .env

# Edit the .env file to configure your settings
# Especially add your Gemini API key if you have one
```

### 3. Create Required Directories
```bash
mkdir -p data/{models,training_data,uploads,results,cache}
mkdir -p logs
mkdir -p docker/{postgres/init-scripts,pgadmin}
```

### 4. Start Services
```bash
# Start the complete development environment
docker-compose -f docker-compose.local.yml up -d

# Or start services individually
docker-compose -f docker-compose.local.yml up -d dbx-postgres dbx-redis
docker-compose -f docker-compose.local.yml up -d dbx-app
```

### 5. Verify Services
```bash
# Check service status
docker-compose -f docker-compose.local.yml ps

# Check application health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.local.yml logs -f
```

## 📊 Service URLs

Once everything is running, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | - |
| **Application API** | http://localhost:8000 | - |
| **Health Check** | http://localhost:8000/health | - |
| **pgAdmin** (optional) | http://localhost:5050 | admin@dbx-ai.com / admin123 |
| **Redis Commander** (optional) | http://localhost:8081 | - |

## 🗄️ Database Information

| Component | Details |
|-----------|---------|
| **Host** | localhost |
| **Port** | 5432 |
| **Database** | dbx_aviation |
| **Admin User** | postgres / password |
| **App User** | dbx_app_user / dbx_secure_2025 |
| **Default Org** | DBX_DEFAULT |
| **Admin Account** | admin@dbx-ai.com / admin123 |

## 🛩️ Sample Data

The system comes with pre-configured sample data:

### Sample Aircraft
- **TEST-001**: DJI Phantom 4 Pro (Multirotor)
- **TEST-002**: Cessna C172 (Fixed Wing)
- **TEST-003**: Bell V-280 Valor (VTOL)

### Sample Organization
- **Organization**: DBX_DEFAULT
- **Admin User**: admin@dbx-ai.com / admin123
- **API Key**: Generated automatically (check logs)

## 🔧 Management Tools

### Start Optional Management Tools
```bash
# Start pgAdmin for database management
docker-compose -f docker-compose.local.yml --profile tools up -d dbx-pgadmin

# Start Redis Commander for cache management
docker-compose -f docker-compose.local.yml --profile tools up -d dbx-redis-commander
```

### Database Shell Access
```bash
# Connect to PostgreSQL
docker exec -it dbx-postgres psql -U postgres -d dbx_aviation

# Example queries
SELECT * FROM dbx_aviation.organizations;
SELECT * FROM dbx_aviation.aircraft_registry;
SELECT * FROM dbx_aviation.users;
```

### Redis Shell Access
```bash
# Connect to Redis
docker exec -it dbx-redis redis-cli

# Example commands
PING
KEYS *
INFO
```

## 🛠️ Development Commands

### Service Management
```bash
# View all service logs
docker-compose -f docker-compose.local.yml logs -f

# View specific service logs
docker-compose -f docker-compose.local.yml logs -f dbx-app

# Restart a service
docker-compose -f docker-compose.local.yml restart dbx-app

# Stop all services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (⚠️ deletes data)
docker-compose -f docker-compose.local.yml down -v
```

### Application Development
```bash
# Rebuild application after code changes
docker-compose -f docker-compose.local.yml build dbx-app
docker-compose -f docker-compose.local.yml up -d dbx-app

# Execute commands in the app container
docker exec -it dbx-app bash

# Run tests (when implemented)
docker exec -it dbx-app python -m pytest

# Check Python dependencies
docker exec -it dbx-app pip list
```

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation.

### Sample API Calls
```bash
# Get system status
curl http://localhost:8000/api/v2/system/status

# Upload a flight log (you'll need a CSV file)
curl -X POST "http://localhost:8000/api/v2/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_flight_log.csv"

# Get recent analyses
curl http://localhost:8000/api/v2/analyses
```

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
netstat -tulpn | grep :8000  # Linux
netstat -ano | findstr :8000  # Windows

# Stop conflicting services or change ports in docker-compose.local.yml
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker exec dbx-postgres pg_isready -U postgres -d dbx_aviation

# Check database logs
docker-compose -f docker-compose.local.yml logs dbx-postgres

# Reset database (⚠️ deletes data)
docker-compose -f docker-compose.local.yml down
docker volume rm dbx-ai-aviation-system_postgres_data
docker-compose -f docker-compose.local.yml up -d
```

#### Application Won't Start
```bash
# Check application logs
docker-compose -f docker-compose.local.yml logs dbx-app

# Rebuild the application
docker-compose -f docker-compose.local.yml build --no-cache dbx-app
docker-compose -f docker-compose.local.yml up -d dbx-app
```

#### Out of Disk Space
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

### Getting Help

1. **Check the logs** first: `docker-compose -f docker-compose.local.yml logs -f`
2. **Verify all services are running**: `docker-compose -f docker-compose.local.yml ps`
3. **Check Docker resources**: Ensure Docker has enough memory (4GB+)
4. **Restart services**: `docker-compose -f docker-compose.local.yml restart`

## 🔒 Security Notes

⚠️ **Important**: This is a development setup with default credentials:

- **PostgreSQL**: postgres / password
- **Admin User**: admin@dbx-ai.com / admin123
- **pgAdmin**: admin@dbx-ai.com / admin123

**Never use these credentials in production!**

## 🚀 Next Steps

Once your local environment is running:

1. **Configure Gemini API Key** in `.env` for AI-powered reports
2. **Explore the API** at http://localhost:8000/docs
3. **Upload sample flight logs** to test the analysis
4. **Check the database** using pgAdmin
5. **Start developing** new features!

## 📝 Environment Variables

Key environment variables you can customize in `.env`:

```bash
# Database
DATABASE_URL=postgresql://dbx_app_user:dbx_secure_2025@localhost:5432/dbx_aviation

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# External Services
GEMINI_API_KEY=your_gemini_api_key_here

# Logging
LOG_LEVEL=DEBUG
```

## 🎯 Ready to Develop!

Your DBX AI Aviation System is now ready for local development. You can:

- ✅ Analyze flight logs
- ✅ Detect aircraft types
- ✅ Identify anomalies
- ✅ Generate AI reports
- ✅ Manage aircraft registry
- ✅ Access comprehensive APIs

Happy coding! 🚁✈️🛩️