# Security & Production Deployment Guide

## 🔐 Environment Variables & Secrets

### Development Setup
```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual values
nano .env  # Add your GEMINI_API_KEY
```

### Production Secrets Management
```bash
# Option 1: Docker Secrets
echo "your_gemini_key" | docker secret create gemini_api_key -

# Option 2: Kubernetes Secrets
kubectl create secret generic dbx-secrets \
  --from-literal=gemini-api-key=your_key_here

# Option 3: HashiCorp Vault
vault kv put secret/dbx-ai gemini_api_key=your_key_here
```

## 🛡️ API Security

### Rate Limiting
```python
# Add to FastAPI app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v2/analyze")
@limiter.limit("10/minute")  # 10 requests per minute
async def analyze_flight_log():
    pass
```

### HTTPS/TLS Configuration
```yaml
# docker-compose.prod.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl
      - ./nginx.conf:/etc/nginx/nginx.conf
```

## 🚀 Production Checklist

- [ ] Remove .env from git (add to .gitignore)
- [ ] Use secrets management (not environment files)
- [ ] Enable HTTPS/TLS
- [ ] Add API rate limiting
- [ ] Configure CORS properly
- [ ] Set up monitoring & logging
- [ ] Use non-root user in containers
- [ ] Scan images for vulnerabilities

## 🔍 Security Scanning
```bash
# Scan Docker image for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image oualidl290/dbx-ai-system:latest
```