# macOS vs Windows Setup - OS Differences Summary

## Key Differences Identified and Resolved

### 1. **Proxy Configuration (CRITICAL)**
- **Issue**: macOS had proxy settings that blocked Python HTTP requests to localhost
- **Windows**: Usually no proxy for localhost
- **macOS**: Had proxy environment variables:
  ```bash
  http_proxy=http://127.0.0.1:7890
  https_proxy=http://127.0.0.1:7890
  all_proxy=socks5://127.0.0.1:7891
  ```
- **Solution**: Updated test scripts to bypass proxy for localhost:
  ```python
  proxies = {'http': '', 'https': ''}
  ```

### 2. **Port Standardization**
- **Changed from**: 8888 (macOS default) 
- **Changed to**: 9000 (matching Windows setup)
- **Files updated**:
  - `.env`
  - `.env.local` 
  - `docker-compose.yml`
  - `Dockerfile`
  - `validate.py`
  - `test_service_simple.py`

### 3. **Virtual Environment Usage**
- **Windows style**: Direct absolute path execution
- **macOS solution**: Use `.venv/bin/python` instead of activating
- **Benefit**: Consistent across both platforms, no activation needed

### 4. **Python Execution Method**
- **Old**: `source .venv/bin/activate && python script.py`
- **New**: `.venv/bin/python script.py`
- **Advantages**:
  - More reliable
  - Works consistently on Windows/macOS/Linux
  - No shell activation requirements

## Current Working Configuration

### Service Startup (macOS)
```bash
cd /Users/yanbo/Projects/llmYTranslate
.venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 9000 --reload
```

### Testing (macOS)
```bash
.venv/bin/python test_service_simple.py
```

### Service Endpoints
- Health: `http://127.0.0.1:9000/api/health`
- Demo Translation: `http://127.0.0.1:9000/api/demo/translate`
- Service Discovery: `http://127.0.0.1:9000/api/discovery/info`

## Service Status
✅ **Service**: Running on port 9000
✅ **Translation**: Working (Ollama integration)
✅ **Service Discovery**: Working
✅ **Health Checks**: Working
⚠️ **Ollama Status**: Shows as "unhealthy" but translations work
⚠️ **Cache Status**: Sometimes shows as "unhealthy" but not critical

## Environment Variables (Consistent)
```bash
API__HOST=127.0.0.1
API__PORT=9000
DEPLOYMENT__MODE=local
AUTH__DISABLE_SIGNATURE_VALIDATION=true
OLLAMA__MODEL_NAME=llava:latest
```

## Next Steps
1. ✅ Service working on port 9000 (matching Windows)
2. ✅ Proxy issues resolved  
3. ✅ Virtual environment working with absolute paths
4. ✅ All tests passing with proxy bypass
5. 🔄 Optional: Investigate Ollama health check sensitivity
