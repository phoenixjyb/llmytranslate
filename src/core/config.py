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
        default="http://127.0.0.1:11434",
        description="Ollama server host"
    )
    model_name: str = Field(
        default="gemma2:2b",
        description="Default LLM model name"
    )
    
    class Config:
        env_prefix = "OLLAMA__"
        
    def __init__(self, **kwargs):
        # Check for OLLAMA_HOST environment variable first
        import os
        if "OLLAMA_HOST" in os.environ:
            kwargs["ollama_host"] = os.environ["OLLAMA_HOST"]
        super().__init__(**kwargs)
        
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


class DeploymentSettings(BaseSettings):
    """Deployment mode configuration."""
    
    mode: str = Field(
        default="local",
        description="Deployment mode: 'local' or 'remote'"
    )
    service_name: str = Field(
        default="llm-translation",
        description="Service name for identification"
    )
    external_host: Optional[str] = Field(
        default=None,
        description="External host address for remote mode"
    )
    external_port: Optional[int] = Field(
        default=None,
        description="External port for remote mode"
    )
    network_interface: str = Field(
        default="auto",
        description="Network interface to bind to ('auto', 'eth0', 'wlan0', etc.)"
    )
    enable_discovery: bool = Field(
        default=False,
        description="Enable service discovery for remote mode"
    )
    discovery_port: int = Field(
        default=8889,
        description="Port for service discovery endpoint"
    )
    trusted_networks: List[str] = Field(
        default=["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        description="Trusted network ranges for remote access"
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
    deployment: DeploymentSettings = Field(default_factory=DeploymentSettings)
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
