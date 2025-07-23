"""
Application configuration management using Pydantic settings.
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    db_url: str = Field(
        default="sqlite:///./translation_service.db",
        description="Database URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )


class RedisSettings(BaseSettings):
    """Redis configuration for caching and rate limiting."""
    
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )


class OllamaSettings(BaseSettings):
    """Ollama service configuration."""
    
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server host"
    )
    model_name: str = Field(
        default="llama3.1:8b",
        description="Default LLM model name"
    )
    request_timeout: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )


class AuthSettings(BaseSettings):
    """Authentication configuration."""
    
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    disable_signature_validation: bool = Field(
        default=False,
        description="Disable Baidu-compatible signature validation for development"
    )


class APISettings(BaseSettings):
    """API configuration."""
    
    title: str = Field(
        default="LLM Translation Service",
        description="API title"
    )
    description: str = Field(
        default="Local LLM-powered translation service with Baidu API compatibility",
        description="API description"
    )
    version: str = Field(
        default="1.0.0",
        description="API version"
    )
    host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    port: int = Field(
        default=8000,
        description="API port"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""
    
    requests_per_minute: int = Field(
        default=60,
        description="Requests per minute per API key"
    )
    requests_per_hour: int = Field(
        default=1000,
        description="Requests per hour per API key"
    )
    requests_per_day: int = Field(
        default=10000,
        description="Requests per day per API key"
    )


class TranslationSettings(BaseSettings):
    """Translation service configuration."""
    
    supported_languages: List[str] = Field(
        default=["en", "zh", "auto"],
        description="Supported language codes"
    )
    max_text_length: int = Field(
        default=5000,
        description="Maximum text length for translation"
    )
    concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent translation requests"
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format: json or text"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path"
    )


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration."""
    
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )
    metrics_port: int = Field(
        default=8001,
        description="Metrics endpoint port"
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # Sub-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    api: APISettings = Field(default_factory=APISettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    translation: TranslationSettings = Field(default_factory=TranslationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
