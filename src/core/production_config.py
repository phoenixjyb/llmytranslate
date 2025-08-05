# Enhanced production configuration for the LLM Translation Service
# This file contains production-ready settings for security, performance, and monitoring

from typing import List, Optional
from pydantic import BaseSettings, Field
import os

class ProductionConfig(BaseSettings):
    """Production configuration settings."""
    
    # Environment
    environment: str = Field(default="production", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Token expiration")
    
    # Public access controls
    public_access: bool = Field(default=True, description="Allow public access")
    require_api_key: bool = Field(default=True, description="Require API key for requests")
    
    # Rate limiting (more restrictive for public access)
    requests_per_minute: int = Field(default=30, description="Requests per minute per IP")
    requests_per_hour: int = Field(default=500, description="Requests per hour per IP")
    requests_per_day: int = Field(default=5000, description="Requests per day per IP")
    
    # Content restrictions
    max_request_size: int = Field(default=1024*1024, description="Max request size in bytes")
    max_text_length: int = Field(default=10000, description="Max translation text length")
    
    # IP filtering
    allowed_ips: List[str] = Field(default=[], description="Allowed IP addresses")
    blocked_ips: List[str] = Field(default=[], description="Blocked IP addresses")
    
    # Geographic restrictions (optional)
    allowed_countries: List[str] = Field(default=[], description="Allowed country codes")
    geo_blocking_enabled: bool = Field(default=False, description="Enable geographic blocking")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_methods: List[str] = Field(default=["GET", "POST"], description="Allowed CORS methods")
    cors_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    log_file: str = Field(default="logs/production.log", description="Log file path")
    enable_access_logs: bool = Field(default=True, description="Enable access logging")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=8001, description="Metrics endpoint port")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")
    
    # SSL/TLS (for HTTPS)
    ssl_enabled: bool = Field(default=False, description="Enable SSL/TLS")
    ssl_keyfile: Optional[str] = Field(None, description="SSL private key file")
    ssl_certfile: Optional[str] = Field(None, description="SSL certificate file")
    
    # Performance settings
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    keep_alive_timeout: int = Field(default=5, description="Keep-alive timeout")
    max_concurrent_requests: int = Field(default=100, description="Max concurrent requests")
    
    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Max cache entries")
    
    # Translation service settings
    default_model: str = Field(default="gemma2:2b", description="Default Ollama model")
    model_timeout: int = Field(default=120, description="Model request timeout")
    max_tokens: int = Field(default=4096, description="Max tokens per request")
    
    # Database settings (if using persistent storage)
    database_url: Optional[str] = Field(None, description="Database connection URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    
    # Backup settings
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_interval: int = Field(default=24, description="Backup interval in hours")
    backup_retention: int = Field(default=7, description="Backup retention in days")
    
    class Config:
        env_file = ".env.production"
        case_sensitive = False

# Security middleware configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}

# Rate limiting configurations by endpoint
RATE_LIMITS = {
    "/api/translate": "30/minute",
    "/api/health": "100/minute",
    "/docs": "10/minute",
    "/": "50/minute"
}

# Allowed file types for uploads (if any)
ALLOWED_FILE_TYPES = [
    "text/plain",
    "application/json",
    "text/csv"
]

# Maximum file sizes (in bytes)
MAX_FILE_SIZES = {
    "text/plain": 1024 * 1024,  # 1MB
    "application/json": 512 * 1024,  # 512KB
    "text/csv": 2 * 1024 * 1024  # 2MB
}

# Production-specific middleware order
MIDDLEWARE_ORDER = [
    "SecurityHeadersMiddleware",
    "IPFilteringMiddleware", 
    "RateLimitingMiddleware",
    "GeoBlockingMiddleware",
    "AuthenticationMiddleware",
    "LoggingMiddleware",
    "CompressionMiddleware",
    "CacheMiddleware"
]

# Monitoring and alerting thresholds
MONITORING_THRESHOLDS = {
    "cpu_usage": 80,  # Percentage
    "memory_usage": 85,  # Percentage
    "disk_usage": 90,  # Percentage
    "error_rate": 5,  # Percentage
    "response_time": 2000,  # Milliseconds
    "concurrent_users": 50  # Number of users
}

# Auto-scaling settings (if using cloud deployment)
AUTO_SCALING = {
    "enabled": False,
    "min_instances": 1,
    "max_instances": 5,
    "cpu_threshold": 70,
    "memory_threshold": 80,
    "scale_up_cooldown": 300,  # Seconds
    "scale_down_cooldown": 600  # Seconds
}

# Notification settings for alerts
NOTIFICATIONS = {
    "email_enabled": False,
    "webhook_enabled": False,
    "slack_enabled": False,
    "alert_email": "admin@example.com",
    "webhook_url": "",
    "slack_webhook": ""
}

# Default production environment variables
DEFAULT_PRODUCTION_ENV = """
# Production Environment Configuration for LLM Translation Service
ENVIRONMENT=production
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-super-secure-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Public Access
PUBLIC_ACCESS=true
REQUIRE_API_KEY=true

# Rate Limiting (restrictive for public access)
REQUESTS_PER_MINUTE=30
REQUESTS_PER_HOUR=500
REQUESTS_PER_DAY=5000

# Content Restrictions
MAX_REQUEST_SIZE=1048576
MAX_TEXT_LENGTH=10000

# CORS (adjust as needed for your domains)
CORS_ORIGINS=["*"]
CORS_METHODS=["GET", "POST", "OPTIONS"]
CORS_HEADERS=["*"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/production.log
ENABLE_ACCESS_LOGS=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8001
HEALTH_CHECK_INTERVAL=60

# Performance
REQUEST_TIMEOUT=30
KEEP_ALIVE_TIMEOUT=5
MAX_CONCURRENT_REQUESTS=100

# Cache
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# Translation Service
DEFAULT_MODEL=gemma2:2b
MODEL_TIMEOUT=120
MAX_TOKENS=4096

# SSL/TLS (configure for HTTPS)
SSL_ENABLED=false
SSL_KEYFILE=
SSL_CERTFILE=

# Backup
BACKUP_ENABLED=true
BACKUP_INTERVAL=24
BACKUP_RETENTION=7

# Geographic filtering (optional)
GEO_BLOCKING_ENABLED=false
ALLOWED_COUNTRIES=[]

# IP filtering (optional)
ALLOWED_IPS=[]
BLOCKED_IPS=[]
"""

def create_production_env_file(file_path: str = ".env.production"):
    """Create a production environment file with secure defaults."""
    import secrets
    
    # Generate a secure secret key
    secret_key = secrets.token_urlsafe(32)
    
    # Replace placeholder with actual secure key
    env_content = DEFAULT_PRODUCTION_ENV.replace(
        "your-super-secure-secret-key-here-change-this",
        secret_key
    )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print(f"Production environment file created: {file_path}")
    print("Please review and adjust settings as needed for your deployment.")

if __name__ == "__main__":
    create_production_env_file()
