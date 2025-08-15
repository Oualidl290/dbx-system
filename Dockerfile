# DBX AI Aviation System v2.0 - Production Multi-Stage Dockerfile
# Optimized for production deployment with latest system architecture

# ================================
# Stage 1: Builder (Dependencies)
# ================================
FROM python:3.11-slim AS builder

# Build arguments for versioning
ARG BUILD_DATE
ARG VERSION=2.0.0
ARG VCS_REF

# Labels for better image management
LABEL maintainer="DBX AI Team" \
      version="${VERSION}" \
      description="Production-ready multi-aircraft aviation AI system" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ================================
# Stage 2: Runtime (Production)
# ================================
FROM python:3.11-slim AS runtime

# Build arguments
ARG BUILD_DATE
ARG VERSION=2.0.0
ARG VCS_REF

# Labels
LABEL maintainer="DBX AI Team" \
      version="${VERSION}" \
      description="Production multi-aircraft aviation AI system" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MODEL_VERSION=${VERSION} \
    PATH="/opt/venv/bin:$PATH" \
    WORKERS=2 \
    MAX_WORKERS=4 \
    TIMEOUT=30

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r dbx && useradd -r -g dbx -d /app -s /bin/bash dbx

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/data/{models,cache,logs,temp,uploads,results} && \
    mkdir -p /app/reports && \
    mkdir -p /app/config && \
    chown -R dbx:dbx /app

# Copy application code with proper structure
COPY --chown=dbx:dbx app/ ./app/
COPY --chown=dbx:dbx ai-engine/ ./ai-engine/
COPY --chown=dbx:dbx main.py ./
COPY --chown=dbx:dbx pyproject.toml ./

# Copy additional files for production
COPY --chown=dbx:dbx scripts/maintenance/simple_evaluation.py ./scripts/
COPY --chown=dbx:dbx README.md ./
COPY --chown=dbx:dbx docs/README.md ./docs/

# Switch to non-root user
USER dbx

# Health check with better configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use exec form for better signal handling
CMD ["python", "main.py"]
