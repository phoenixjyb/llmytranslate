# LLM Translation Service - Testing & Running Procedure

## ✅ Prerequisites Verification

### 1. Check Ollama Installation
```powershell
ollama --version
ollama list  # Should show llama3.1:8b model
```

### 2. Check Python Installation
```powershell
py --version  # Should be Python 3.11+ (we tested with 3.13.5)
```

### 3. Verify Project Structure
```powershell
ls  # Should see .venv/, src/, requirements.txt, run.py
```

## 🚀 Running the Translation Service

### Method 1: Using Activated Virtual Environment (Recommended for Development)

1. **Open PowerShell and navigate to project directory**
   ```powershell
   cd c:\Users\yanbo\wspace\llmytranslate
   ```

2. **Activate the virtual environment**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   You should see `(.venv)` prefix in your prompt.

3. **Remove conflicting environment variable** (Critical Step!)
   ```powershell
   Remove-Item Env:\ollama -ErrorAction SilentlyContinue
   ```

4. **Test configuration loading**
   ```powershell
   python test_config.py
   ```
   Should output: ✅ Settings loaded successfully!

5. **Run the translation service**
   ```powershell
   python run.py
   ```

### Method 2: Direct Python Execution (Recommended for Production/Scripts)

1. **Navigate to project directory**
   ```powershell
   cd c:\Users\yanbo\wspace\llmytranslate
   ```

2. **Remove conflicting environment variable**
   ```powershell
   Remove-Item Env:\ollama -ErrorAction SilentlyContinue
   ```

3. **Run using full Python path**
   ```powershell
   .\.venv\Scripts\python.exe test_config.py
   .\.venv\Scripts\python.exe run.py
   ```

## 🧪 Testing the Service

### 1. Health Check
Once the service is running (default: http://localhost:8000), test:

```powershell
# In a new terminal
curl http://localhost:8000/api/health
```

### 2. Basic Translation Test
```powershell
# Test English to Chinese
curl -X POST "http://localhost:8000/api/demo/translate" -d "q=hello world&from=en&to=zh"

# Test Chinese to English  
curl -X POST "http://localhost:8000/api/demo/translate" -d "q=你好世界&from=zh&to=en"
```

### 3. API Documentation
Visit: http://localhost:8000/docs (when DEBUG=true)

## 🔧 Configuration

### Minimal Working Configuration (.env)
```properties
# Simple working configuration for Windows
ENVIRONMENT=development
DEBUG=true

# Disable complex configs for now - use defaults
```

### Key Configuration Points
- **Ollama Host**: Default `http://localhost:11434`
- **Model**: Default `llama3.1:8b`
- **API Port**: Default `8000`
- **Debug Mode**: Enabled for development

## ⚠️ Important Notes

### Environment Variable Conflict
The system `ollama` environment variable (set by Ollama installer) conflicts with our configuration. Always run:
```powershell
Remove-Item Env:\ollama -ErrorAction SilentlyContinue
```

### Virtual Environment Persistence
- Method 1 (activated env) works for interactive development
- Method 2 (direct path) works for background processes and scripts
- Background processes lose virtual environment context in PowerShell

### Dependency Inheritance
When using `.\.venv\Scripts\python.exe` directly:
- ✅ **Virtual Environment**: 29 packages (includes FastAPI, Pydantic, Uvicorn, etc.)
- ⚠️ **System Python**: Only 17 packages (basic Python installation)
- **Direct calls** (`.\.venv\Scripts\python.exe`) always use virtual environment dependencies
- **This ensures** all required packages are available regardless of activation state

**Key Virtual Environment Packages:**
```
fastapi           0.116.1
pydantic          2.11.7
pydantic-settings 2.10.1
uvicorn           0.35.0
httpx             0.28.1
redis             6.2.0
```

**Why Direct Path Method Works:**
- Virtual environment Python (`\.venv\Scripts\python.exe`) has its own `site-packages` directory
- Contains all project dependencies installed via `pip install -r requirements.txt`
- Independent of system Python and its packages
- Guarantees consistent environment for the application

### Service Verification Steps
1. ✅ Configuration loads without errors
2. ✅ Ollama model is available (`llama3.1:8b`)
3. ✅ Service starts on port 8000
4. ✅ Health endpoint responds
5. ✅ Translation endpoints work

## 📝 Quick Start Commands

```powershell
# Complete setup and test in one go
cd c:\Users\yanbo\wspace\llmytranslate
.\.venv\Scripts\Activate.ps1
Remove-Item Env:\ollama -ErrorAction SilentlyContinue
python test_config.py
python run.py
```

## 🐛 Troubleshooting

### Common Issues
1. **"Python was not found"** → Use `.\.venv\Scripts\python.exe` directly
2. **"error parsing value for field ollama"** → Remove the `ollama` environment variable
3. **"Connection refused to Ollama"** → Ensure Ollama is running and accessible
4. **Import errors** → Ensure virtual environment is activated or use full path

### Verification Commands
- `ollama list` - Check available models
- `python test_config.py` - Test configuration loading
- `Get-ChildItem Env: | Where-Object {$_.Name -like "*ollama*"}` - Check env vars
