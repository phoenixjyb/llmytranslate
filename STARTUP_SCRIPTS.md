# 🚀 Service Startup Scripts

This directory contains multiple startup scripts for the LLM Translation Service, designed for different platforms and use cases.

## 📁 Available Scripts

### 1. `start-service.ps1` (Recommended for Windows)
**Advanced PowerShell script with full validation and options**

#### Features:
- ✅ Complete prerequisite validation (Ollama, Python, models)
- ✅ Environment variable conflict resolution
- ✅ Configuration testing
- ✅ Color-coded output with status indicators
- ✅ Multiple execution modes
- ✅ Custom port support
- ✅ Debug mode

#### Usage:
```powershell
# Basic startup
.\start-service.ps1

# Configuration test only
.\start-service.ps1 -ConfigTest

# Custom port with debug
.\start-service.ps1 -Port 8080 -Debug

# Get help
Get-Help .\start-service.ps1 -Full
```

### 2. `start-service.bat` (Simple Windows Batch)
**Simple batch file for basic Windows users**

#### Features:
- ✅ Basic validation
- ✅ Environment conflict resolution
- ✅ Simple error handling
- ✅ Easy to understand and modify

#### Usage:
```cmd
start-service.bat
```

### 3. `start-service.sh` (Linux/macOS)
**Bash script for Unix-like systems**

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
