# LLMyTranslate Project Organization

## Directory Structure

```
llmytranslate/
├── 📁 android/                    # Android app source code
├── 📁 src/                        # Main Python application
├── 📁 web/                        # Web interface files
├── 📁 scripts/                    # Build and deployment scripts
├── 📁 docs/                       # Documentation
├── 📁 config/                     # Configuration files
├── 📁 tests/                      # All testing files (organized structure)
│   ├── 📁 unit/                  # Unit tests for individual components
│   ├── 📁 integration/           # Integration tests for complete workflows
│   ├── 📁 examples/              # Test examples and advanced scenarios
│   ├── 📄 run_tests.py           # Test runner
│   ├── � pytest.ini            # Pytest configuration
│   ├── 📄 check_tts_languages.py # TTS language validation
│   ├── 📄 debug_conversations.py # Conversation debugging tool
│   └── 📄 verify_phase4.py       # Phase 4 verification utility
├── 📁 dev/                        # Development and temporary files
│   ├── 📁 experiments/           # Experimental features and demos
│   ├── 📁 android-setup/         # Android development setup scripts
│   └── 📁 temp/                  # Temporary files and utilities
├── 📁 data/                       # Application data and databases
├── 📁 cache/                      # Cache files
├── 📁 audio_cache/               # Audio file cache
├── 📁 logs/                       # Application logs
├── 📁 performance/               # Performance testing and benchmarks
├── 📁 docker/                     # Docker configuration
├── 📁 __pycache__/               # Python cache (auto-generated)
├── 📁 .venv/                      # Python virtual environment
├── 📁 .venv-tts/                  # TTS-specific virtual environment
├── 📄 run.py                      # Main application entry point
├── 📄 requirements.txt            # Python dependencies
├── 📄 requirements-tts.txt        # TTS-specific dependencies
├── 📄 requirements-phone-call.txt # Phone call dependencies
├── 📄 README.md                   # Project documentation
├── 📄 .env.example               # Environment variables template
└── 📄 service-manager.ps1         # Service management script
```

## File Organization Rules

### ✅ Root Directory - Keep Only
- **Main entry points**: `run.py`
- **Core configuration**: `requirements*.txt`, `.env*`, `.gitignore`
- **Documentation**: `README.md`, `README-zh.md`
- **Key service scripts**: `service-manager.ps1`, `start-service.*`, `stop-service.*`

### 📁 `/tests/` - All Testing (Proper Structure)
- **unit/**: Unit tests for individual components
- **integration/**: End-to-end and integration tests  
- **examples/**: Advanced test scenarios and examples
- **Root**: Test utilities, runners, and configuration

### 📁 `/dev/` - Development Files
- **experiments/**: Experimental features, demos, prototypes
- **android-setup/**: Android development environment setup
- **temp/**: Temporary utilities, one-off scripts

### 📁 `/scripts/` - Build & Deployment
- Cross-platform service management
- Installation and setup scripts
- Deployment automation
- Build tools

### 📁 `/docs/` - Documentation
- Architecture documents
- Setup guides
- API documentation
- Development notes

### ❌ Never Put in Root
- Test files (`test_*.py`)
- Experimental code
- Temporary utilities
- Debug scripts
- Setup/installation scripts (use `/scripts/`)

## Development Workflow

### Adding New Features
1. **Prototype** in `/dev/experiments/`
2. **Test** with files in `/dev/test-files/`
3. **Integrate** into `/src/` when ready
4. **Document** in `/docs/`

### Testing
1. **Unit tests** → `/tests/unit/`
2. **Integration tests** → `/tests/integration/`
3. **Test examples** → `/tests/examples/`
4. **Test utilities** → `/tests/` (root)
5. Use descriptive names: `test_feature_name.py`
6. Run tests with: `python tests/run_tests.py`

### Scripts
1. Development scripts → `/dev/`
2. Build/deployment scripts → `/scripts/`
3. Keep root clean with only essential service scripts

## Current Cleanup Status

✅ **Organized `/tests/` structure**:
- **Unit tests**: Individual component testing
- **Integration tests**: Complete workflow testing  
- **Examples**: Advanced scenarios and demos
- **Utilities**: Test runners and validation tools

✅ **Moved to `/dev/experiments/`**:
- `create_*.py` files
- `demo_*.py` files
- `simple_*.py` files
- `phone_call_fix.py`

✅ **Moved to `/dev/android-setup/`**:
- `setup-android-dev.*`
- `setup-env-android.*`
- `build-android.*`

✅ **Moved to `/dev/temp/`**:
- `tts_subprocess.py`
- `init_user_system.py`
- `tts_test.*`
- `test_audio.wav`
- `users.db`

✅ **Moved to `/scripts/`**:
- `install-*.ps1`
- `setup-*.ps1`
- `test-*.ps1`

✅ **Removed redundant `/dev/test-files/`**: All merged into proper `/tests/` structure

## Future Guidelines

### For New Development
```bash
# Create experimental feature
touch dev/experiments/new_feature_prototype.py

# Create unit tests
touch tests/unit/test_new_feature.py

# Create integration tests  
touch tests/integration/test_new_feature_integration.py

# When ready, move to main codebase
mv dev/experiments/new_feature_prototype.py src/features/new_feature.py
```

### For Android Development
```bash
# All Android setup in dedicated directory
cd dev/android-setup/
./setup-android-dev.sh --check-only
./build-android.sh
```

This organization keeps the root directory clean and makes the project much more maintainable! 🧹✨
