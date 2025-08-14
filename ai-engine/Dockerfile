
# DBX AI Multi-Aircraft System - Optimized Production Dockerfile
# Multi-stage build for smaller, more secure images

# ================================
# Stage 1: Builder (Dependencies)
# ================================
FROM python:3.11-slim AS builder

# Build arguments
ARG BUILD_DATE
ARG VERSION=2.0.0
ARG VCS_REF

# Labels for better image management
LABEL maintainer="DBX AI Team" \
      version="${VERSION}" \
      description="AI-powered multi-aircraft flight analysis system" \
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
COPY ai-engine/requirements.txt .
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
      description="AI-powered multi-aircraft flight analysis system" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MODEL_VERSION=${VERSION} \
    PATH="/opt/venv/bin:$PATH" \
    WORKERS=1 \
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
    chown -R dbx:dbx /app

# Copy application code
COPY --chown=dbx:dbx ai-engine/app/ ./app/

# Copy additional files for demo/evaluation
COPY --chown=dbx:dbx simple_evaluation.py ./
COPY --chown=dbx:dbx demo_presentation.py ./
COPY --chown=dbx:dbx VALIDATION_REPORT.md ./
COPY --chown=dbx:dbx README.md ./

# Switch to non-root user
USER dbx

# Health check with better configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use exec form for better signal handling
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port 8000 --workers ${WORKERS} --timeout-keep-alive ${TIMEOUT}"]
