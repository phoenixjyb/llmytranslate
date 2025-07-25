# 🚀 Service Startup Scripts & Network Access

This directory contains multiple startup scripts for the LLM Translation Service, designed for different platforms and use cases. **All scripts now include network access configuration and environment conflict resolution.**

## 🌐 Network Access Status: ✅ ACHIEVED

- **✅ Local Access**: `http://localhost:8000`
- **✅ Local Network Access**: `http://[YOUR_LOCAL_IP]:8000` (verified working)
- **✅ Internet Access**: Ready for router configuration

## 📁 Available Scripts

### 1. `start-service.ps1` (Recommended for Windows) ⭐
**Advanced PowerShell script with full validation and network access features**

#### Features:
- ✅ Complete prerequisite validation (Ollama, Python, models)
- ✅ **Environment variable conflict resolution** (fixes `ollama` system variable issue)
- ✅ **Network access configuration and testing**
- ✅ Configuration testing
- ✅ Color-coded output with status indicators
- ✅ Multiple execution modes
- ✅ Custom port support
- ✅ **Network information display**
- ✅ Debug mode

#### Usage:
```powershell
# Basic startup with network access
.\start-service.ps1

# Show detailed network configuration
.\start-service.ps1 -NetworkInfo

# Configuration test only
.\start-service.ps1 -ConfigTest

# Custom port with debug and network info
.\start-service.ps1 -Port 8080 -Debug -NetworkInfo

# Get help
Get-Help .\start-service.ps1 -Full
```

### 2. `service-manager.ps1` (Service Management) 🔧
**Comprehensive service lifecycle management**

#### Features:
- ✅ Start/stop/restart/status commands
- ✅ **Environment conflict resolution built-in**
- ✅ **Virtual environment Python usage**
- ✅ Production and development modes
- ✅ Docker support
- ✅ Log management

#### Usage:
```powershell
# Start service (automatically handles environment conflicts)
.\service-manager.ps1 -Action start

# Check status with network info
.\service-manager.ps1 -Action status

# Start in production mode
.\service-manager.ps1 -Action start -Production

# View logs
.\service-manager.ps1 -Action logs
```

### 3. `deploy-online.ps1` (Internet Access Setup) 🌐
**Network deployment and internet access configuration**

#### Features:
- ✅ **Firewall configuration**
- ✅ **Network interface detection**
- ✅ **Router setup instructions**
- ✅ **Public IP detection**
- ✅ **Port forwarding guidance**

#### Usage:
```powershell
# Full network setup
.\deploy-online.ps1

# Test configuration only
.\deploy-online.ps1 -TestOnly

# Skip firewall configuration
.\deploy-online.ps1 -SkipFirewall
```

#### Features:
- ✅ Cross-platform compatibility
- ✅ Color output
- ✅ Full validation suite
- ✅ Similar functionality to PowerShell version

#### Usage:
```bash
# Make executable (first time)
chmod +x start-service.sh

# Run the script
./start-service.sh
```

## 🔧 What These Scripts Do

### Prerequisites Check
1. **Project Structure**: Validates `src/`, `run.py`, `.venv/` exist
2. **Ollama Installation**: Checks if Ollama is installed and accessible
3. **Required Model**: Verifies `llama3.1:8b` model is available
4. **Python Environment**: Confirms virtual environment Python works

### Environment Setup
1. **Conflict Resolution**: Removes conflicting `ollama` environment variable
2. **Configuration Test**: Validates that all settings load correctly
3. **Service Information**: Displays access URLs and test commands

### Service Launch
1. **Startup**: Launches the translation service
2. **Monitoring**: Provides real-time status and helpful information

## 📊 Script Comparison

| Feature | PowerShell | Batch | Bash |
|---------|------------|-------|------|
| Platform | Windows | Windows | Linux/macOS |
| Validation | ✅ Full | ✅ Basic | ✅ Full |
| Color Output | ✅ | ❌ | ✅ |
| Options/Params | ✅ | ❌ | ❌ |
| Error Handling | ✅ Advanced | ✅ Basic | ✅ Good |
| User-Friendly | ✅ Excellent | ✅ Good | ✅ Good |

## 🐛 Troubleshooting

### ✅ Major Issues RESOLVED

#### 1. **JSON Parsing Error - Environment Variable Conflict** (SOLVED!)
**Problem**: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

**Root Cause**: System environment variable `ollama` conflicts with application configuration

**Solution**: All scripts now automatically handle this:
```powershell
# Automatic fix in all scripts:
Remove-Item Env:\ollama -ErrorAction SilentlyContinue
```

#### 2. **"Python was not found"** (SOLVED!)
**Problem**: System Python not found or virtual environment not activated

**Solution**: All scripts now use virtual environment Python:
```powershell
# Scripts automatically use:
.\.venv\Scripts\python.exe run.py
```

#### 3. **Network Access Issues** (SOLVED!)
**Problem**: Can't access service from other devices on network

**Solutions Applied**:
- ✅ Windows Firewall configured
- ✅ Service binds to `0.0.0.0:8000`
- ✅ Environment conflicts resolved

### Common Issues

1. **"Execution Policy Restricted" (PowerShell)**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **"Permission Denied" (Bash)**
   ```bash
   chmod +x start-service.sh
   ```

3. **Unicode Encoding Issues**
   - Scripts handle Windows console encoding automatically
   - Use Windows Terminal for best experience

### Script Fails to Start?
1. Check prerequisites manually:
   ```powershell
   ollama list
   .\.venv\Scripts\python.exe --version
   ```

2. Run configuration test separately:
   ```powershell
   .\.venv\Scripts\python.exe test_config.py
   ```

3. Check detailed procedure: [`TESTING_PROCEDURE.md`](./TESTING_PROCEDURE.md)

## 🎯 Recommended Usage

- **Development (Windows)**: Use `start-service.ps1`
- **Quick Testing (Windows)**: Use `start-service.bat`
- **Production (Windows)**: Use `start-service.ps1 -Port 8080`
- **Linux/macOS**: Use `start-service.sh`

## 📝 Service Information

Once started, the service provides:

- **Main API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`
- **Demo Translation**: `http://localhost:8000/api/demo/translate`

### Quick Test Commands
```bash
# Health check
curl http://localhost:8000/api/health

# Translation test
curl -X POST "http://localhost:8000/api/demo/translate" \
     -d "q=hello world&from=en&to=zh"
```

## 🔄 Next Steps

After the service starts successfully:
1. Test the health endpoint
2. Try demo translations
3. Explore the API documentation
4. Integrate with your applications

For detailed testing procedures and advanced configuration, see [`TESTING_PROCEDURE.md`](./TESTING_PROCEDURE.md).
