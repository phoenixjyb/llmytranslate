# Cross-Platform Service Management

## 📋 Overview

The LLMyTranslate service now has **complete cross-platform compatibility** with identical functionality on Windows, macOS, and Linux.

## 🚀 Service Management Scripts

### Start Service

#### Windows (PowerShell):
```powershell
# Basic start
.\start-service.ps1

# Production mode
.\start-service.ps1 -Production

# With debugging
.\start-service.ps1 -Debug

# With ngrok tunnel
.\start-service.ps1 -WithNgrok

# Force start (resolve conflicts)
.\start-service.ps1 -Force
```

#### Mac/Linux (Bash):
```bash
# Basic start
./start-service.sh

# Production mode
./start-service.sh --production

# With debugging
./start-service.sh --debug

# With ngrok tunnel
./start-service.sh --with-ngrok

# Force start (resolve conflicts)
./start-service.sh --force
```

### Stop Service

#### Windows (PowerShell):
```powershell
# Stop both service and ngrok
.\stop-service.ps1

# Force stop
.\stop-service.ps1 -Force

# Stop only ngrok
.\stop-service.ps1 -NgrokOnly

# Stop only translation service
.\stop-service.ps1 -ServiceOnly

# Verbose output
.\stop-service.ps1 -Verbose
```

#### Mac/Linux (Bash):
```bash
# Stop both service and ngrok
./stop-service.sh

# Force stop
./stop-service.sh --force

# Stop only ngrok
./stop-service.sh --ngrok-only

# Stop only translation service
./stop-service.sh --service-only

# Verbose output
./stop-service.sh --verbose
```

## 🔧 Phase 4 Features (Cross-Platform)

Both PowerShell and Bash scripts include:

### Service Health Monitoring
- **Main Service**: HTTP health checks on port 8000
- **Component Verification**: Individual component status
  - 🧠 **Optimized LLM**: `/api/llm/health`
  - 📊 **Performance Monitor**: `/api/performance/status`
  - ✅ **Quality Monitor**: `/api/quality/status`
  - 🔗 **Connection Pool**: `/api/connections/status`

### Environment Conflict Resolution
- **Automatic Detection**: Identifies conflicting environment variables
- **Temporary Removal**: Safely removes conflicts during startup
- **Restoration**: Can restore variables after service stops

### Smart Process Management
- **Port-based Detection**: Finds processes using port 8000
- **Pattern Matching**: Identifies Python processes running the service
- **Graceful Shutdown**: Attempts clean shutdown before force-killing
- **Verification**: Confirms service is actually stopped

## 📊 Status Monitoring

### Windows:
```powershell
# Quick status check
.\scripts\service-status.ps1

# Continuous monitoring
.\scripts\service-status.ps1 -Continuous

# Detailed view
.\scripts\service-status.ps1 -Detailed
```

### Mac/Linux:
```bash
# Quick status check
./scripts/service-status.sh

# Continuous monitoring
./scripts/service-status.sh --continuous

# Detailed view
./scripts/service-status.sh --detailed
```

## 🌐 Access Information (Both Platforms)

Once started, services are accessible at:

### Local Access:
- `http://localhost:8000` - Main service
- `http://127.0.0.1:8000` - Alternative local access

### Network Access:
- `http://<LOCAL_IP>:8000` - From other devices on network
- Scripts automatically detect and display local IP addresses

### API Documentation:
- `http://localhost:8000/docs` - Interactive API docs
- `http://localhost:8000/api/health` - Health check endpoint

### Phase 4 Endpoints:
- `http://localhost:8000/api/llm/health` - LLM component
- `http://localhost:8000/api/performance/status` - Performance metrics
- `http://localhost:8000/api/quality/status` - Quality monitoring
- `http://localhost:8000/api/connections/status` - Connection pool

## 🔄 Android Development Integration

### Windows Development:
```powershell
# Start LLMyTranslate service
.\start-service.ps1

# Build and install Android app
.\build-android.ps1 build -Install -Clean

# Monitor service for Android connections
.\scripts\service-status.ps1 -Continuous
```

### Mac Development:
```bash
# Start LLMyTranslate service
./start-service.sh

# Build and install Android app
chmod +x ./build-android.sh
./build-android.sh build --install --clean

# Monitor service for Android connections
./scripts/service-status.sh --continuous
```

## 🛠️ Development Workflow

### 1. Environment Setup (Both Platforms)
```bash
# Activate virtual environment
# Windows: .\.venv\Scripts\activate
# Mac/Linux: source ./.venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Service Development (Both Platforms)
```bash
# Start in development mode with debugging
# Windows: .\start-service.ps1 -Debug
# Mac/Linux: ./start-service.sh --debug

# Make code changes...

# Stop service
# Windows: .\stop-service.ps1
# Mac/Linux: ./stop-service.sh

# Restart with changes
# (Scripts handle automatic reload in debug mode)
```

### 3. Android Testing (Both Platforms)
```bash
# Start service
# Windows: .\start-service.ps1
# Mac/Linux: ./start-service.sh

# Check Android app connection
# Open Android app and verify WebSocket connection to http://<IP>:8000

# Monitor in real-time
# Windows: .\scripts\service-status.ps1 -Continuous
# Mac/Linux: ./scripts/service-status.sh --continuous
```

## 🔒 Security Considerations

### Network Access:
- **Local Development**: Service binds to all interfaces (0.0.0.0:8000)
- **Production**: Consider firewall rules for external access
- **Android**: Ensure phone and development machine are on same network

### Environment Variables:
- **Conflict Resolution**: Scripts temporarily remove conflicting variables
- **Sensitive Data**: Store API keys and secrets in `.env` file
- **Production**: Use environment-specific configuration

## 📝 Troubleshooting

### Common Issues (Both Platforms):

#### Port Already in Use:
```bash
# Check what's using port 8000
# Windows: netstat -ano | findstr :8000
# Mac/Linux: lsof -i :8000

# Force stop any existing service
# Windows: .\stop-service.ps1 -Force
# Mac/Linux: ./stop-service.sh --force
```

#### Python Environment Issues:
```bash
# Verify Python installation
python --version

# Check virtual environment
# Windows: .\.venv\Scripts\python.exe --version
# Mac/Linux: ./.venv/bin/python --version

# Reinstall dependencies if needed
pip install -r requirements.txt --force-reinstall
```

#### Android Connection Issues:
```bash
# Check if service is accessible from network
curl http://<DEV_MACHINE_IP>:8000/api/health

# Verify Android app server URL in settings
# Should be: ws://<DEV_MACHINE_IP>:8000/api/android/stream
```

## 🎯 Next Steps

1. **Phase 2 Android**: Implement voice features in Android app
2. **Production Deployment**: Set up production environment
3. **Load Testing**: Test service under Android app load
4. **Monitoring**: Implement advanced monitoring and alerting

---

**All scripts are now synchronized between PowerShell (.ps1) and Bash (.sh) with identical functionality across Windows, macOS, and Linux platforms.**
