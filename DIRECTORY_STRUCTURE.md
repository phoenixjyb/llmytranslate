# LLM Translation Service - Directory Structure

## 📁 Organized Project Structure

```
llmytranslate/
├── 📄 README.md                          # Main project documentation
├── 📄 requirements.txt                   # Python dependencies
├── 📄 requirements-minimal.txt           # Minimal dependencies for testing
├── 📄 docker-compose.yml                # Docker composition
├── 📄 Dockerfile                        # Docker configuration
├── 📄 run.py                            # Main application entry point
├── 📄 .env                              # Environment variables (local)
├── 📄 .gitignore                        # Git ignore rules
├── 📄 softwareRequirements.txt          # Software requirements
│
├── 📂 src/                               # Source code
│   ├── 📄 __init__.py
│   ├── 📄 main.py                       # FastAPI application
│   ├── 📂 api/                          # API routes
│   │   ├── 📄 __init__.py
│   │   └── 📂 routes/
│   │       ├── 📄 __init__.py
│   │       ├── 📄 admin.py              # Admin endpoints
│   │       ├── 📄 health.py             # Health check endpoints
│   │       └── 📄 translation.py        # Translation endpoints
│   ├── 📂 core/                         # Core functionality
│   │   ├── 📄 __init__.py
│   │   ├── 📄 config.py                 # Configuration management
│   │   └── 📄 production_config.py      # Production-specific settings
│   ├── 📂 models/                       # Pydantic models
│   │   └── 📄 __init__.py
│   └── 📂 services/                     # Business logic services
│       ├── 📄 __init__.py
│       ├── 📄 auth_service.py           # Authentication service
│       ├── 📄 cache_service.py          # Caching service
│       ├── 📄 ollama_client.py          # Ollama integration
│       ├── 📄 stats_service.py          # Statistics service
│       └── 📄 translation_service.py    # Translation logic
│
├── 📂 tests/                            # Test suite
│   ├── 📄 test_api.py                   # API tests
│   ├── 📄 test_baidu_compatibility.py   # Baidu API compatibility tests
│   ├── 📄 test_compatibility.py         # General compatibility tests
│   ├── 📄 test_ollama.py               # Ollama service tests
│   ├── 📄 test_service.py              # Service layer tests
│   ├── 📄 final_test.py                # Final integration tests
│   ├── 📄 simple_test.py               # Simple functionality tests
│   └── 📄 validate.py                  # Validation utilities
│
├── 📂 scripts/                          # Setup and utility scripts
│   ├── 📄 setup.ps1                    # Windows PowerShell setup
│   ├── 📄 setup.bat                    # Windows Batch setup
│   ├── 📄 setup.sh                     # Linux/macOS setup
│   ├── 📄 production-setup.ps1         # Production deployment script
│   ├── 📄 add_ollama_to_path.ps1       # PowerShell PATH helper
│   └── 📄 add_ollama_to_path.bat       # Batch PATH helper
│
├── 📂 config/                           # Configuration files
│   ├── 📄 nginx.conf                   # Nginx reverse proxy config
│   └── 📄 .env.example                 # Environment template
│
├── 📂 docs/                            # Documentation
│   ├── 📄 BAIDU_API_COMPATIBILITY.md   # Baidu API compatibility
│   ├── 📄 CLIENT_EXAMPLES.md           # Client code examples
│   ├── 📄 CONTRIBUTING.md              # Contribution guidelines
│   ├── 📄 DATA_FLOW_DIAGRAM.md         # Data flow documentation
│   ├── 📄 PRODUCTION_SETUP_GUIDE.md    # Production deployment guide
│   ├── 📄 PROJECT_STRUCTURE.md         # Project structure (original)
│   ├── 📄 QUICK_START_PRODUCTION.md    # Quick start for production
│   ├── 📄 ROUTER_SETUP_GUIDE.md        # Router configuration guide
│   ├── 📄 SOFTWARE_DESIGN_DOCUMENT.md  # Software design document
│   ├── 📄 SYSTEM_ARCHITECTURE.md       # System architecture
│   ├── 📄 WINDOWS_COMPATIBILITY.md     # Windows compatibility notes
│   └── 📄 WINDOWS_COMPATIBILITY_FINAL.md # Final Windows setup
│
├── 📂 logs/                            # Log files (created at runtime)
│   └── 📄 .gitkeep                     # Keep directory in git
│
├── 📂 .venv/                           # Python virtual environment
└── 📂 .git/                            # Git repository data
```

## 🎯 Directory Purposes

### `/src` - Source Code
- **`main.py`**: FastAPI application entry point
- **`api/`**: REST API endpoints and routing
- **`core/`**: Core functionality and configuration
- **`models/`**: Pydantic data models and schemas
- **`services/`**: Business logic and external integrations

### `/scripts` - Setup & Utilities
- **Platform-specific setup scripts** for Windows, Linux, macOS
- **Production deployment scripts** for server setup
- **Utility scripts** for PATH management and configuration

### `/config` - Configuration Files
- **`nginx.conf`**: Production reverse proxy configuration
- **`.env.example`**: Environment variables template
- **Production-ready configurations** for different deployment scenarios

### `/docs` - Documentation
- **Setup guides** for different platforms and deployment scenarios
- **API documentation** and client examples
- **Architecture documentation** and design decisions
- **Compatibility guides** for different systems

### `/tests` - Test Suite
- **Unit tests** for individual components
- **Integration tests** for API endpoints
- **Compatibility tests** for different platforms
- **Validation utilities** for testing

### `/logs` - Runtime Logs
- **Application logs** (created when application runs)
- **Access logs** for monitoring and debugging
- **Error logs** for troubleshooting

## 🚀 Quick Navigation

### For Users:
- **Getting Started**: `README.md`
- **Windows Setup**: `scripts/setup.ps1`
- **Production Deployment**: `docs/PRODUCTION_SETUP_GUIDE.md`
- **Client Examples**: `docs/CLIENT_EXAMPLES.md`

### For Developers:
- **Source Code**: `src/`
- **Tests**: `tests/`
- **Contributing**: `docs/CONTRIBUTING.md`
- **Architecture**: `docs/SYSTEM_ARCHITECTURE.md`

### For System Administrators:
- **Production Setup**: `scripts/production-setup.ps1`
- **Nginx Config**: `config/nginx.conf`
- **Router Setup**: `docs/ROUTER_SETUP_GUIDE.md`
- **Monitoring**: `logs/` (runtime)

## 📋 File Naming Conventions

- **Setup Scripts**: `setup.*` (platform-specific extensions)
- **Documentation**: `*.md` (Markdown format)
- **Configuration**: `*.conf`, `*.env*` 
- **Tests**: `test_*.py`
- **Services**: `*_service.py`
- **Utilities**: `*_client.py`, `*_utils.py`

## 🔧 Development Workflow

1. **Setup**: Run appropriate setup script from `/scripts`
2. **Development**: Work in `/src` directory
3. **Testing**: Run tests from `/tests` directory
4. **Documentation**: Update relevant files in `/docs`
5. **Deployment**: Use production scripts from `/scripts`

This organized structure makes the project more maintainable, easier to navigate, and follows standard Python project conventions.
