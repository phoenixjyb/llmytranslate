# Graceful Shutdown Scripts

This directory contains comprehensive shutdown scripts to safely stop all LLM Translation Service components, including ngrok and Tailscale services.

## Available Scripts

### 🔵 Windows PowerShell Script (`shutdown.ps1`)
**Recommended for Windows users**
- Full-featured with color output and detailed logging
- Graceful API shutdowns before process termination
- Comprehensive error handling and verification

### 🟡 Windows Batch Script (`shutdown.bat`)
**Alternative for Windows compatibility**
- Simple batch file for basic Windows environments
- No external dependencies required
- Compatible with older Windows systems

### 🟢 Unix/Linux/macOS Script (`shutdown.sh`)
**For Unix-based systems**
- Full bash script with color output
- Uses standard Unix tools (lsof, netstat, pgrep)
- Cross-platform compatibility

## Quick Usage

### Windows (PowerShell - Recommended)
```powershell
# Stop all services
.\shutdown.ps1

# Keep Tailscale running
.\shutdown.ps1 -KeepTailscale

# Keep ngrok running  
.\shutdown.ps1 -KeepNgrok

# Force stop all processes
.\shutdown.ps1 -Force

# Silent operation
.\shutdown.ps1 -Quiet

# Combine options
.\shutdown.ps1 -KeepTailscale -KeepNgrok -Quiet
```

### Windows (Batch)
```cmd
REM Stop all services
shutdown.bat

REM Keep Tailscale running
shutdown.bat --keep-tailscale

REM Keep ngrok running
shutdown.bat --keep-ngrok

REM Force stop all processes
shutdown.bat --force

REM Silent operation
shutdown.bat --quiet
```

### Unix/Linux/macOS
```bash
# Make executable (first time only)
chmod +x shutdown.sh

# Stop all services
./shutdown.sh

# Keep Tailscale running
./shutdown.sh --keep-tailscale

# Keep ngrok running
./shutdown.sh --keep-ngrok

# Force stop all processes
./shutdown.sh --force

# Silent operation
./shutdown.sh --quiet
```

## What Gets Stopped

### 🔄 Translation Services (Always stopped)
- **FastAPI/Uvicorn** processes running the translation server
- **Python** processes related to the translation service
- **Port 8000** - Main translation API endpoint

### 🤖 Ollama Services (Always stopped)
- **Ollama** processes and services
- **Port 11434** - Ollama API endpoint

### 🌐 ngrok Services (Optional - controlled by `--keep-ngrok`)
- **ngrok** processes and tunnels
- **Port 4040** - ngrok dashboard
- Attempts graceful tunnel shutdown via API before process termination

### 🔗 Tailscale Services (Optional - controlled by `--keep-tailscale`)
- **Tailscale** client processes
- **tailscaled** daemon processes
- Attempts graceful logout before process termination

## Shutdown Process

Each script follows this systematic approach:

### 1. 🎯 Graceful API Shutdowns
- Translation service: `POST /api/admin/shutdown`
- ngrok tunnels: Individual tunnel deletion via API
- Tailscale: Logout command via CLI

### 2. 🔄 Process Termination
- Gentle termination attempts first
- Force termination if graceful fails
- Process identification by name and port usage

### 3. ✅ Verification Steps
- Check for remaining processes
- Verify port availability
- Report any issues or warnings

### 4. 📊 Summary Report
- Status of each service type
- Port availability confirmation
- Success/warning messages

## Options Reference

| Option | PowerShell | Batch | Unix | Description |
|--------|------------|-------|------|-------------|
| Keep Tailscale | `-KeepTailscale` | `--keep-tailscale` | `--keep-tailscale` | Don't stop Tailscale services |
| Keep ngrok | `-KeepNgrok` | `--keep-ngrok` | `--keep-ngrok` | Don't stop ngrok services |
| Force Stop | `-Force` | `--force` | `--force` | Force kill remaining processes |
| Silent Mode | `-Quiet` | `--quiet` | `--quiet` | Minimal output |
| Help | `Get-Help .\shutdown.ps1` | `shutdown.bat /?` | `./shutdown.sh --help` | Show usage information |

## Troubleshooting

### 🚨 Script Won't Run (PowerShell)
```powershell
# Check execution policy
Get-ExecutionPolicy

# Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 🚨 Processes Still Running
- Use the `-Force` or `--force` option to force-kill stubborn processes
- Check if processes are running under different user accounts
- Some system services may require administrator privileges

### 🚨 Port Still in Use
- Wait a few seconds for the OS to release the port
- Check for other applications using the same ports
- Restart the terminal/command prompt if needed

### 🚨 Permission Denied
- Run as Administrator (Windows) or with sudo (Unix) if needed
- Check file permissions for script execution
- Ensure you have rights to terminate the processes

## Integration with Development Workflow

### 🔄 Quick Development Cycle
```powershell
# Stop services for development
.\shutdown.ps1 -KeepTailscale

# Make your changes...

# Restart services
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 🌐 Production Shutdown
```powershell
# Complete production shutdown
.\shutdown.ps1 -Quiet

# Or keep network connectivity
.\shutdown.ps1 -KeepTailscale -KeepNgrok -Quiet
```

### 🧪 Testing Isolation
```powershell
# Stop everything for clean testing
.\shutdown.ps1 -Force

# Verify clean state
netstat -ano | findstr ":8000\|:11434\|:4040"
```

## Advanced Usage

### 🔧 Custom Service Management
You can modify the scripts to add additional services by:

1. **Adding process patterns** to the process detection logic
2. **Adding port checks** to the verification section  
3. **Adding graceful shutdown APIs** if your services support them

### 📝 Logging and Monitoring
The scripts provide detailed output that can be redirected:

```powershell
# Log shutdown process
.\shutdown.ps1 -Quiet > shutdown.log 2>&1

# Monitor in real-time
.\shutdown.ps1 | Tee-Object -FilePath shutdown.log
```

### 🔄 Automation Integration
These scripts can be integrated into:
- **CI/CD pipelines** for clean environment preparation
- **System startup/shutdown** procedures
- **Development environment** reset scripts
- **Docker container** shutdown hooks

## Safety Features

- ✅ **Graceful shutdowns** attempted before force termination
- ✅ **Verification steps** to confirm successful shutdown
- ✅ **Option to preserve** specific services (Tailscale, ngrok)
- ✅ **Detailed logging** of all operations
- ✅ **Error handling** for common failure scenarios
- ✅ **Cross-platform** compatibility

---

**💡 Tip**: Bookmark this file and keep these scripts handy for quick service management during development and deployment!
