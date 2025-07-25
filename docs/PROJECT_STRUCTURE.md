# Project Structure Reference

## Directory Layout

```
llmYTranslate/
├── .env                           # Environment variables (active)
├── .env.backup                    # Environment backup
├── .env.example                   # Environment variables template
├── .env.remote                    # Remote deployment environment
├── .gitignore                     # Git ignore patterns
├── Dockerfile                     # Application containerization
├── README.md                      # Project documentation
├── QUICK_NETWORK_ACCESS.md        # Quick network access guide
├── STARTUP_SCRIPTS.md            # Startup scripts documentation
├── deploy-online.ps1             # Online deployment script
├── discover_service.py           # Service discovery utility
├── docker-compose.yml            # Local multi-service deployment
├── docker-compose.remote.yml     # Remote deployment configuration
├── nginx.conf                    # Nginx configuration
├── pytest.ini                    # PyTest configuration
├── requirements.txt              # Python dependencies
├── requirements-minimal.txt      # Minimal Python dependencies
├── run.py                        # Development server launcher
├── run_tests.py                  # Test runner utility
├── softwareRequirements.txt      # Original requirements document
├── start-service.ps1             # Service start script
├── test_ollama.json              # Ollama test configuration
├── test_ollama_connectivity.py   # Ollama connectivity tests
├── translation_server.py         # Translation server entry point
├── validate.py                   # Service validation script
├── config/                       # Configuration files
│   └── nginx.conf                # Nginx configuration
├── docker/                       # Docker configurations
│   └── nginx.remote.conf         # Remote nginx configuration
├── docs/                         # Documentation
│   ├── CONTRIBUTING.md           # Development workflow and guidelines
│   ├── CURL_COMMANDS.md          # API testing commands
│   ├── GIT_CREDENTIAL_FIX.md     # Git credential troubleshooting
│   ├── NGROK_SETUP.md            # Ngrok setup guide
│   ├── PROJECT_ORGANIZATION.md   # Project organization guide
│   ├── PROJECT_STRUCTURE.md      # This file - project structure
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture documentation
│   ├── guides/                   # User guides
│   └── setup/                    # Setup documentation
├── logs/                         # Application logs
├── scripts/                      # Utility scripts
│   ├── add_ollama_to_path.bat    # Add Ollama to PATH (Windows)
│   ├── add_ollama_to_path.ps1    # Add Ollama to PATH (PowerShell)
│   ├── configure-remote-access.ps1 # Remote access configuration
│   ├── deploy-online.ps1         # Online deployment
│   ├── deploy.sh                 # Deployment script (Unix)
│   ├── git_helper.ps1            # Git helper utilities
│   ├── production-setup.ps1      # Production setup
│   ├── service-manager.ps1       # Service management
│   ├── setup.bat                 # Setup script (Windows)
│   ├── setup.ps1                 # Setup script (PowerShell)
│   ├── setup.sh                  # Setup script (Unix)
│   ├── setup_ngrok.ps1           # Ngrok setup
│   ├── setup_remote_access.ps1   # Remote access setup
│   ├── start-service.bat         # Start service (Windows)
│   ├── start-service.ps1         # Start service (PowerShell)
│   ├── start-service.sh          # Start service (Unix)
│   ├── test_endpoints.ps1        # Endpoint testing (PowerShell)
│   └── test_endpoints.sh         # Endpoint testing (Unix)
├── src/                          # Main application source
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── routes/               # API endpoints
│   │       ├── __init__.py
│   │       ├── admin.py          # Administrative routes
│   │       ├── discovery.py      # Service discovery routes
│   │       ├── health.py         # Health check endpoints
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
│       ├── ollama_client.py      # Local LLM integration
│       ├── stats_service.py      # Statistics and monitoring
│       └── translation_service.py # Core translation logic
└── tests/                        # Test suite
    ├── examples/                 # Example tests
    ├── integration/              # Integration tests
    └── unit/                     # Unit tests
```

## Key Files Description

### Application Core
- **`src/main.py`**: FastAPI application with middleware and route configuration
- **`src/core/config.py`**: Centralized configuration management
- **`src/core/network.py`**: Network configuration and utilities
- **`src/core/production_config.py`**: Production-specific configuration
- **`run.py`**: Development server with hot reload
- **`translation_server.py`**: Alternative server entry point

### Services Layer
- **`translation_service.py`**: Main translation orchestration
- **`ollama_client.py`**: Local LLM client with retry logic
- **`auth_service.py`**: Baidu API-compatible authentication
- **`cache_service.py`**: Redis-based caching and rate limiting
- **`stats_service.py`**: Metrics collection and reporting

### API Endpoints
- **`/translate`**: Main translation endpoint (Baidu API compatible)
- **`/api/v2/trans`**: Alternative translation endpoint
- **`/health`**: Service health checks
- **`/admin/stats`**: Statistics and monitoring
- **`/admin/cache/clear`**: Cache management
- **`/discovery`**: Service discovery endpoints

### Models
- **`src/models/schemas.py`**: Pydantic data models and validation schemas

### Deployment & Configuration
- **`Dockerfile`**: Application containerization
- **`docker-compose.yml`**: Local multi-service orchestration (App + Ollama + Redis + Nginx)
- **`docker-compose.remote.yml`**: Remote deployment configuration
- **`nginx.conf`**: Nginx proxy configuration
- **`.env.example`**: Environment configuration template
- **`deploy-online.ps1`**: Online deployment automation

### Scripts & Utilities
- **`scripts/setup.ps1`**: PowerShell setup script
- **`scripts/start-service.ps1`**: Service startup script
- **`scripts/production-setup.ps1`**: Production environment setup
- **`scripts/service-manager.ps1`**: Service management utilities
- **`scripts/test_endpoints.ps1`**: API endpoint testing
- **`discover_service.py`**: Service discovery utility
- **`validate.py`**: Installation and service validation

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

# Alternative server entry point
python translation_server.py

# Run with Docker (local)
docker-compose up -d

# Run with Docker (remote)
docker-compose -f docker-compose.remote.yml up -d

# Run tests
python run_tests.py
# or
python -m pytest tests/

# Validate installation
python validate.py

# Test Ollama connectivity
python test_ollama_connectivity.py

# Discover services
python discover_service.py
```

### PowerShell Scripts
```powershell
# Setup environment
.\scripts\setup.ps1

# Start service
.\scripts\start-service.ps1

# Production setup
.\scripts\production-setup.ps1

# Configure remote access
.\scripts\configure-remote-access.ps1

# Deploy online
.\scripts\deploy-online.ps1

# Test endpoints
.\scripts\test_endpoints.ps1
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
pip install -r requirements-minimal.txt

# Run setup script (PowerShell)
.\scripts\setup.ps1

# Run setup script (Unix)
chmod +x scripts/setup.sh && ./scripts/setup.sh
```

## Configuration Files
- **`.env`**: Active environment variables
- **`.env.example`**: Environment variables template  
- **`.env.remote`**: Remote deployment environment variables
- **`.env.backup`**: Environment backup
- **`requirements.txt`**: Full Python package dependencies
- **`requirements-minimal.txt`**: Minimal Python dependencies
- **`docker-compose.yml`**: Local service configuration and networking
- **`docker-compose.remote.yml`**: Remote deployment service configuration
- **`nginx.conf`**: Nginx proxy configuration
- **`config/nginx.conf`**: Additional nginx configuration
- **`pytest.ini`**: PyTest configuration
- **`.gitignore`**: Version control exclusions
