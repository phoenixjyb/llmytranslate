# Project Structure Reference

## Directory Layout

```
llmYTranslate/
├── .env                           # Environment variables (active)
├── .env.backup                    # Environment backup
├── .env.example                   # Environment variables template
├── .env.tailscale                 # Tailscale environment configuration
├── .gitignore                     # Git ignore patterns
├── .ngrok_pid                     # Ngrok process ID file
├── README.md                      # Project documentation (English)
├── README-zh.md                   # Project documentation (Chinese)
├── requirements.txt               # Python dependencies
├── run.py                         # Development server launcher
├── service-manager.ps1            # Service management script
├── setup-web-interface.ps1        # Web interface setup script
├── start-service.ps1              # Service start script
├── stop-service.ps1               # Service stop script
├── stop-service-zh.ps1            # Service stop script (Chinese)
├── cache/                         # Cache storage
│   └── translation_cache.json.gz # Compressed translation cache
├── config/                        # Configuration files
│   ├── .env.example              # Environment template
│   ├── .env.remote               # Remote deployment environment
│   ├── nginx.conf                # Nginx configuration
│   ├── README.md                 # Configuration documentation
│   ├── requirements-minimal.txt  # Minimal dependencies
│   └── softwareRequirements.txt  # Software requirements
├── docker/                        # Docker configurations
│   ├── docker-compose.yml        # Local development composition
│   ├── docker-compose.remote.yml # Remote deployment composition
│   ├── Dockerfile                # Application container
│   ├── nginx.remote.conf         # Remote nginx configuration
│   └── README.md                 # Docker documentation
├── docs/                          # Documentation
│   ├── CONTRIBUTING.md           # Development workflow and guidelines
│   ├── CURL_COMMANDS.md          # API testing commands
│   ├── GIT_CREDENTIAL_FIX.md     # Git credential troubleshooting
│   ├── LLMyTranslate_Service_Setup.md # Service setup guide
│   ├── NGROK_SETUP.md            # Ngrok setup guide
│   ├── PROJECT_ORGANIZATION.md   # Project organization guide
│   ├── PROJECT_STRUCTURE.md      # This file - project structure
│   ├── Remote_Access_Setup.md    # Remote access setup guide
│   ├── SHELL_SCRIPT_SYNC_SUMMARY.md # Shell script synchronization
│   ├── STARTUP_SCRIPTS.md        # Startup scripts documentation
│   ├── api/                      # API documentation
│   │   ├── BAIDU_API_COMPATIBILITY.md # Baidu API compatibility
│   │   └── CLIENT_EXAMPLES.md    # Client usage examples
│   ├── architecture/             # Architecture documentation
│   │   ├── DIRECTORY_STRUCTURE.md # Directory structure guide
│   │   ├── README.md             # Architecture overview
│   │   ├── SOFTWARE_STACK_FLOWCHART.md # Stack flowchart (English)
│   │   └── SOFTWARE_STACK_FLOWCHART-zh.md # Stack flowchart (Chinese)
│   ├── guides/                   # User guides
│   │   ├── QUICK_NETWORK_ACCESS.md # Quick network access
│   │   ├── REMOTE_ACCESS_GUIDE.md # Remote access guide
│   │   ├── ROUTER_SETUP_GUIDE.md # Router setup guide
│   │   ├── SERVICE_STOP_GUIDE.md # Service stop guide
│   │   ├── TESTING_PROCEDURE.md  # Testing procedures
│   │   ├── WEB_INTERFACE_DEPLOYMENT.md # Web interface deployment
│   │   └── WEB_INTERFACE_GUIDE.md # Web interface guide
│   └── setup/                    # Setup documentation
│       ├── MACOS_SETUP_NOTES.md  # macOS setup notes
│       ├── PRODUCTION_SETUP_GUIDE.md # Production setup
│       ├── QUICK_START_PRODUCTION.md # Quick production start
│       ├── STARTUP_SCRIPTS.md    # Startup scripts guide
│       ├── WINDOWS_COMPATIBILITY.md # Windows compatibility
│       └── WINDOWS_COMPATIBILITY_FINAL.md # Final Windows compatibility
├── logs/                          # Application logs
│   └── .gitkeep                  # Keep directory in git
├── performance/                   # Performance testing
│   ├── ollama_direct_results.json # Direct Ollama test results
│   ├── optimized_service_results.json # Optimized service results
│   ├── README.md                 # Performance testing documentation
│   ├── test-performance.ps1      # Performance test script (PowerShell)
│   ├── test_optimized_service.py # Optimized service test
│   ├── test_performance.py       # Performance test suite
│   └── test_performance_comparison.py # Performance comparison
├── scripts/                       # Utility scripts
│   ├── add-ollama-to-path.ps1    # Add Ollama to PATH (PowerShell)
│   ├── add_ollama_to_path.bat    # Add Ollama to PATH (Windows Batch)
│   ├── configure-remote-access.ps1 # Remote access configuration
│   ├── deploy-online.ps1         # Online deployment (PowerShell)
│   ├── deploy-online.sh          # Online deployment (Unix)
│   ├── deploy.sh                 # Deployment script (Unix)
│   ├── git-helper.ps1            # Git helper utilities (PowerShell)
│   ├── git-helper.sh             # Git helper utilities (Unix)
│   ├── organize-directory.ps1    # Directory organization
│   ├── production-setup.ps1      # Production setup (PowerShell)
│   ├── production-setup.sh       # Production setup (Unix)
│   ├── README.md                 # Scripts documentation
│   ├── service-manager.ps1       # Service management (PowerShell)
│   ├── service-manager.sh        # Service management (Unix)
│   ├── setup-ngrok-enhanced.sh   # Enhanced Ngrok setup
│   ├── setup-ngrok.ps1           # Ngrok setup (PowerShell)
│   ├── setup-ngrok.sh            # Ngrok setup (Unix)
│   ├── setup-remote-access-unified.ps1 # Unified remote access (PowerShell)
│   ├── setup-remote-access-unified.sh # Unified remote access (Unix)
│   ├── setup-remote-access.ps1   # Remote access setup (PowerShell)
│   ├── setup-remote-access.sh    # Remote access setup (Unix)
│   ├── setup-tailscale.ps1       # Tailscale setup (PowerShell)
│   ├── setup-tailscale.sh        # Tailscale setup (Unix)
│   ├── setup.bat                 # Setup script (Windows Batch)
│   ├── setup.ps1                 # Setup script (PowerShell)
│   ├── setup.sh                  # Setup script (Unix)
│   ├── start-service.bat         # Start service (Windows Batch)
│   ├── start-service.ps1         # Start service (PowerShell)
│   ├── start-service.sh          # Start service (Unix)
│   ├── start-tailscale.ps1       # Start Tailscale (PowerShell)
│   ├── start-tailscale.sh        # Start Tailscale (Unix)
│   ├── stop-ngrok.sh             # Stop Ngrok (Unix)
│   ├── stop-service.ps1          # Stop service (PowerShell)
│   ├── stop-service.sh           # Stop service (Unix)
│   ├── test-endpoints.ps1        # Endpoint testing (PowerShell)
│   └── test-endpoints.sh         # Endpoint testing (Unix)
├── src/                           # Main application source
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── routes/               # API endpoints
│   │       ├── __init__.py
│   │       ├── admin.py          # Administrative routes
│   │       ├── discovery.py      # Service discovery routes
│   │       ├── health.py         # Health check endpoints
│   │       ├── optimized.py      # Optimized API routes
│   │       └── translation.py   # Translation API routes
│   ├── core/                     # Core application configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Settings and configuration
│   │   ├── network.py            # Network configuration
│   │   ├── network_backup.py     # Network backup configuration
│   │   ├── network_old.py        # Legacy network configuration
│   │   └── production_config.py  # Production configuration
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic schemas
│   └── services/                 # Business logic layer
│       ├── __init__.py
│       ├── auth_service.py       # Authentication and authorization
│       ├── cache_service.py      # Redis caching operations
│       ├── enhanced_cache_service.py # Enhanced caching with compression
│       ├── ollama_client.py      # Local LLM integration
│       ├── optimized_ollama_client.py # Optimized LLM client
│       ├── optimized_translation_service.py # Optimized translation logic
│       ├── stats_service.py      # Statistics and monitoring
│       └── translation_service.py # Core translation logic
├── tests/                         # Test suite
│   ├── discover_service.py       # Service discovery test
│   ├── pytest.ini               # PyTest configuration
│   ├── run_tests.py              # Test runner utility
│   ├── test_ollama.json          # Ollama test configuration
│   ├── test_ollama_connectivity.py # Ollama connectivity tests
│   ├── test_ollama_direct.py     # Direct Ollama tests
│   ├── translation_server.py     # Translation server test
│   ├── validate.py               # Service validation script
│   ├── examples/                 # Example tests
│   │   ├── __init__.py
│   │   ├── quick_test.py         # Quick functionality test
│   │   ├── simple_test.py        # Simple test cases
│   │   └── validate.py           # Validation examples
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── test_baidu_compatibility.py # Baidu API compatibility tests
│   │   ├── test_compatibility.py # General compatibility tests
│   │   ├── test_no_proxy.py      # Non-proxy tests
│   │   ├── test_service.py       # Service integration tests
│   │   └── test_service_simple.py # Simple service tests
│   └── unit/                     # Unit tests
│       ├── __init__.py
│       ├── test_api.py           # API unit tests
│       ├── test_config.py        # Configuration unit tests
│       └── test_ollama.py        # Ollama unit tests
└── web/                           # Web interface
    ├── index.html                # Main web interface
    ├── index_original.html       # Original web interface backup
    └── optimized.html            # Optimized web interface
```

## Key Files Description

### Application Core
- **`src/main.py`**: FastAPI application with middleware and route configuration
- **`src/core/config.py`**: Centralized configuration management
- **`src/core/network.py`**: Network configuration and utilities
- **`src/core/production_config.py`**: Production-specific configuration
- **`run.py`**: Development server with hot reload

### Services Layer
- **`translation_service.py`**: Main translation orchestration
- **`optimized_translation_service.py`**: Performance-optimized translation logic
- **`ollama_client.py`**: Local LLM client with retry logic
- **`optimized_ollama_client.py`**: Optimized LLM client for better performance
- **`auth_service.py`**: Baidu API-compatible authentication
- **`cache_service.py`**: Redis-based caching and rate limiting
- **`enhanced_cache_service.py`**: Enhanced caching with compression support
- **`stats_service.py`**: Metrics collection and reporting

### API Endpoints
- **`/translate`**: Main translation endpoint (Baidu API compatible)
- **`/api/v2/trans`**: Alternative translation endpoint
- **`/health`**: Service health checks
- **`/admin/stats`**: Statistics and monitoring
- **`/admin/cache/clear`**: Cache management
- **`/discovery`**: Service discovery endpoints
- **`/optimized/*`**: Optimized API endpoints for better performance

### Models
- **`src/models/schemas.py`**: Pydantic data models and validation schemas

### Deployment & Configuration
- **`docker/Dockerfile`**: Application containerization
- **`docker/docker-compose.yml`**: Local multi-service orchestration (App + Ollama + Redis + Nginx)
- **`docker/docker-compose.remote.yml`**: Remote deployment configuration
- **`config/nginx.conf`**: Nginx proxy configuration
- **`docker/nginx.remote.conf`**: Remote nginx configuration
- **`.env.example`**: Environment configuration template
- **`.env.tailscale`**: Tailscale-specific environment variables

### Scripts & Utilities
- **`scripts/setup.ps1`**: PowerShell setup script
- **`scripts/start-service.ps1`**: Service startup script
- **`scripts/stop-service.ps1`**: Service stop script
- **`scripts/production-setup.ps1`**: Production environment setup
- **`scripts/service-manager.ps1`**: Service management utilities
- **`scripts/test-endpoints.ps1`**: API endpoint testing
- **`scripts/configure-remote-access.ps1`**: Remote access configuration
- **`scripts/setup-tailscale.ps1`**: Tailscale VPN setup
- **`scripts/setup-ngrok.ps1`**: Ngrok tunnel setup
- **`service-manager.ps1`**: Main service management script
- **`setup-web-interface.ps1`**: Web interface setup

### Performance & Testing
- **`performance/`**: Performance testing suite and results
- **`performance/test_performance_comparison.py`**: Performance comparison tests
- **`performance/test_optimized_service.py`**: Optimized service performance tests
- **`tests/examples/`**: Example test cases
- **`tests/integration/`**: Integration test suite
- **`tests/unit/`**: Unit test suite

### Web Interface
- **`web/index.html`**: Main web interface for translation
- **`web/optimized.html`**: Performance-optimized web interface
- **`web/index_original.html`**: Original web interface backup

### Cache & Logs
- **`cache/translation_cache.json.gz`**: Compressed translation cache storage
- **`logs/`**: Application log storage directory

### Documentation Structure
- **`docs/api/`**: API documentation and examples
- **`docs/architecture/`**: System architecture documentation
- **`docs/guides/`**: User and setup guides
- **`docs/setup/`**: Detailed setup instructions
- **`README.md`**: Quick start and usage guide
- **`CONTRIBUTING.md`**: Development workflow and standards

## Quick Commands

### Development
```powershell
# Start development server
python run.py

# Run with Docker (local)
docker-compose -f docker/docker-compose.yml up -d

# Run with Docker (remote)
docker-compose -f docker/docker-compose.remote.yml up -d

# Run tests
.\tests\run_tests.py
# or
python -m pytest tests/

# Validate installation
.\tests\validate.py

# Test Ollama connectivity
.\tests\test_ollama_connectivity.py

# Discover services
.\tests\discover_service.py

# Performance testing
.\performance\test-performance.ps1
```

### PowerShell Scripts
```powershell
# Setup environment
.\scripts\setup.ps1

# Start service (normal mode)
.\scripts\start-service.ps1
# or
.\start-service.ps1

# Start service with Tailscale VPN access
.\scripts\start-service.ps1 -WithTailscale
# or
.\start-service.ps1 -WithTailscale

# Start service with Ngrok tunnel
.\scripts\start-service.ps1 -WithNgrok

# Start service in production mode
.\scripts\start-service.ps1 -Production

# Start service with debug output
.\scripts\start-service.ps1 -Debug

# Stop service
.\scripts\stop-service.ps1
# or
.\stop-service.ps1

# Service management
.\scripts\service-manager.ps1
# or
.\service-manager.ps1

# Production setup
.\scripts\production-setup.ps1

# Configure remote access
.\scripts\configure-remote-access.ps1

# Setup web interface
.\setup-web-interface.ps1

# Deploy online
.\scripts\deploy-online.ps1

# Test endpoints
.\scripts\test-endpoints.ps1

# Setup Tailscale VPN
.\scripts\setup-tailscale.ps1

# Setup Ngrok tunnel
.\scripts\setup-ngrok.ps1
```

### Unix/Linux Scripts
```bash
# Start service with Tailscale
./scripts/start-service.sh --with-tailscale

# Start service with Ngrok
./scripts/start-service.sh --with-ngrok

# Start in production mode
./scripts/start-service.sh --production

# Start with debug output
./scripts/start-service.sh --debug
```

### Tailscale VPN Access
```powershell
# Prerequisites: Install and setup Tailscale
# 1. Download Tailscale from https://tailscale.com/download
# 2. Install and authenticate: tailscale up

# Start service with Tailscale access
.\scripts\start-service.ps1 -WithTailscale

# Or use the Unix version
./scripts/start-service.sh --with-tailscale

# What happens:
# - Checks if Tailscale is installed and running
# - Gets your Tailscale IP address
# - Copies .env.tailscale to .env for configuration
# - Starts service accessible via Tailscale network
# - Shows Tailscale IP and service URLs
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Standard commit
git add .
git commit -m "feat: your feature description"

# Push changes
git push origin feature/your-feature
```

### Environment Setup
```powershell
# Copy environment template
Copy-Item .env.example .env

# Install dependencies
pip install -r requirements.txt

# Minimal dependencies
pip install -r config/requirements-minimal.txt

# Run setup script (PowerShell)
.\scripts\setup.ps1

# Run setup script (Unix)
chmod +x scripts/setup.sh && ./scripts/setup.sh

# Setup web interface
.\setup-web-interface.ps1
```

## Configuration Files
- **`.env`**: Active environment variables
- **`.env.example`**: Environment variables template  
- **`.env.tailscale`**: Tailscale VPN environment variables
- **`.env.backup`**: Environment backup
- **`config/.env.example`**: Configuration environment template
- **`config/.env.remote`**: Remote deployment environment variables
- **`requirements.txt`**: Full Python package dependencies
- **`config/requirements-minimal.txt`**: Minimal Python dependencies
- **`docker/docker-compose.yml`**: Local service configuration and networking
- **`docker/docker-compose.remote.yml`**: Remote deployment service configuration
- **`config/nginx.conf`**: Nginx proxy configuration
- **`docker/nginx.remote.conf`**: Remote nginx configuration
- **`tests/pytest.ini`**: PyTest configuration
- **`.gitignore`**: Version control exclusions
- **`config/softwareRequirements.txt`**: Original software requirements
- **`tests/test_ollama.json`**: Ollama test configuration
