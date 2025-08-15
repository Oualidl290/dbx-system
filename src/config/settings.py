"""
Configuration management for DBX AI Aviation System
Production-ready settings with environment support
"""

import os
from pathlib import Path
from typing import Optional, List
from functools import lru_cache

from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(
        default="postgresql://dbx_app_user:dbx_secure_2025@localhost:5432/dbx_aviation",
        env="DATABASE_URL"
    )
    echo: bool = Field(default=False, env="DB_ECHO")
    pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=40, env="DB_MAX_OVERFLOW")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")


class RedisSettings(BaseSettings):
    """Redis configuration for caching"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")


class APISettings(BaseSettings):
    """API configuration"""
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    reload: bool = Field(default=False, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="TOKEN_EXPIRE_MINUTES")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")


class AISettings(BaseSettings):
    """AI/ML model configuration"""
    models_path: str = Field(default="data/models", env="MODELS_PATH")
    training_data_path: str = Field(default="data/training_data", env="TRAINING_DATA_PATH")
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    supported_formats: List[str] = Field(default=[".csv", ".log", ".txt"], env="SUPPORTED_FORMATS")


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")


class Settings(BaseSettings):
    """Main application settings"""
    
    # Application info
    app_name: str = "DBX AI Aviation System"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    api: APISettings = APISettings()
    security: SecuritySettings = SecuritySettings()
    ai: AISettings = AISettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    logs_dir: Path = base_dir / "logs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    environment: str = "development"
    
    class Config:
        env_file = ".env.development"


class ProductionSettings(Settings):
    """Production environment settings"""
    environment: str = "production"
    
    class Config:
        env_file = ".env.production"


class TestingSettings(Settings):
    """Testing environment settings"""
    environment: str = "testing"
    
    class Config:
        env_file = ".env.testing"


def get_environment_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()