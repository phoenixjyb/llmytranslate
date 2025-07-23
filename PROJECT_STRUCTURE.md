# Project Structure Reference

## Directory Layout

```
llmYTranslate/
├── .env.example                    # Environment variables template
├── .gitignore                     # Git ignore patterns
├── CONTRIBUTING.md                # Development workflow and guidelines
├── DATA_FLOW_DIAGRAM.md          # System data flow visualization
├── Dockerfile                     # Application containerization
├── README.md                      # Project documentation
├── SOFTWARE_DESIGN_DOCUMENT.md   # Comprehensive technical design
├── SYSTEM_ARCHITECTURE.md        # Architecture overview
├── docker-compose.yml            # Multi-service deployment
├── requirements.txt               # Python dependencies
├── run.py                        # Development server launcher
├── setup.sh                     # Environment setup script
├── softwareRequirements.txt     # Original requirements document
├── validate.py                   # Service validation script
├── src/                          # Main application source
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── routes/               # API endpoints
│   │       ├── __init__.py
│   │       ├── admin.py          # Administrative routes
│   │       ├── health.py         # Health check endpoints
│   │       └── translation.py   # Translation API routes
│   ├── core/                     # Core application configuration
│   │   ├── __init__.py
│   │   └── config.py             # Settings and configuration
│   └── services/                 # Business logic layer
│       ├── __init__.py
│       ├── auth_service.py       # Authentication and authorization
│       ├── cache_service.py      # Redis caching operations
│       ├── ollama_client.py      # Local LLM integration
│       ├── stats_service.py      # Statistics and monitoring
│       └── translation_service.py # Core translation logic
└── tests/                        # Test suite
    └── test_api.py               # API integration tests
```

## Key Files Description

### Application Core
- **`src/main.py`**: FastAPI application with middleware and route configuration
- **`src/core/config.py`**: Centralized configuration management
- **`run.py`**: Development server with hot reload

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

### Deployment
- **`Dockerfile`**: Application containerization
- **`docker-compose.yml`**: Multi-service orchestration (App + Ollama + Redis + Nginx)
- **`.env.example`**: Environment configuration template

### Documentation
- **`README.md`**: Quick start and usage guide
- **`SOFTWARE_DESIGN_DOCUMENT.md`**: Complete technical specification
- **`SYSTEM_ARCHITECTURE.md`**: High-level architecture overview
- **`CONTRIBUTING.md`**: Development workflow and standards

## Quick Commands

### Development
```bash
# Start development server
python run.py

# Run with Docker
docker-compose up -d

# Run tests
python -m pytest tests/

# Validate installation
python validate.py
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
```bash
# Copy environment template
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run setup script (Mac/Linux)
chmod +x setup.sh && ./setup.sh
```

## Configuration Files
- **`.env`**: Environment variables (create from `.env.example`)
- **`requirements.txt`**: Python package dependencies
- **`docker-compose.yml`**: Service configuration and networking
- **`.gitignore`**: Version control exclusions
