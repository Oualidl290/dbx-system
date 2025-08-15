"""
Configuration management for DBX AI Aviation System
Handles environment-specific settings and application configuration
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

import yaml
from pydantic import BaseSettings, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="postgresql://dbx_api_service:password@localhost:5432/dbx_aviation")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(default="redis://localhost:6379")


class APISettings(BaseSettings):
    """API configuration"""
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)
    workers: int = Field(default=1)


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO")
    format: str = Field(default="json")


class SecuritySettings(BaseSettings):
    """Security configuration"""
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)


class MonitoringSettings(BaseSettings):
    """Monitoring configuration"""
    prometheus_enabled: bool = Field(default=False)
    health_check_interval: int = Field(default=30)


class Settings(PydanticBaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


def load_config_from_yaml(environment: str) -> dict:
    """Load configuration from YAML file"""
    config_path = Path(__file__).parent.parent.parent / "config" / "environments" / f"{environment}.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    return {}


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Load base settings
    settings = Settings(environment=environment)
    
    # Override with YAML config if available
    yaml_config = load_config_from_yaml(environment)
    if yaml_config:
        # Update settings with YAML values
        for section, values in yaml_config.items():
            if hasattr(settings, section):
                section_settings = getattr(settings, section)
                for key, value in values.items():
                    if hasattr(section_settings, key):
                        setattr(section_settings, key, value)
    
    return settings


# Global settings instance
settings = get_settings()