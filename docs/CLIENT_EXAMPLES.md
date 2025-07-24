# Client Access Examples for LLM Translation Server

## 🌐 Accessing Your Translation Server from Different Platforms

Once your Windows PC is set up as a server, here are examples of how different clients (Mac, PC, mobile, web) can access your translation service.

## 📝 Basic Information

### Server Endpoints:
- **Health Check**: `GET /api/health`
- **Translation**: `POST /api/translate`
- **API Documentation**: `GET /docs`

### Server URL Examples:
- **Local Network**: `http://192.168.1.100:8080`
- **Internet Access**: `http://YOUR_PUBLIC_IP:8080`
- **With Domain**: `http://yourdomain.ddns.net:8080`

## 🐍 Python Clients

### Simple Python Client
```python
import requests
import json

class TranslationClient:
    def __init__(self, server_url, api_key=None):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        
    def translate(self, text, target_language, source_language="auto"):
        """Translate text using the server."""
        payload = {
            "text": text,
            "target_language": target_language,
            "source_language": source_language
        }
        
        if self.api_key:
            payload["api_key"] = self.api_key
            
        try:
            response = requests.post(
                f"{self.server_url}/api/translate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def health_check(self):
        """Check if server is healthy."""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

# Usage Example
if __name__ == "__main__":
    # Replace with your server's address
    client = TranslationClient("http://192.168.1.100:8080", "your-api-key")
    
    # Health check
    health = client.health_check()
    print(f"Server health: {health}")
    
    # Translation
    result = client.translate("Hello, world!", "Spanish")
    print(f"Translation result: {result}")
```

### Advanced Python Client with Error Handling
```python
import requests
import time
from typing import Dict, List, Optional

class AdvancedTranslationClient:
    def __init__(self, server_url: str, api_key: Optional[str] = None, 
                 max_retries: int = 3, timeout: int = 30):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with retry logic."""
        url = f"{self.server_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                response.raise_for_status()
                return {"success": True, "data": response.json()}
                
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    return {"success": False, "error": "Request timeout"}
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def translate_batch(self, texts: List[str], target_language: str, 
                       source_language: str = "auto") -> List[Dict]:
        """Translate multiple texts."""
        results = []
        for text in texts:
            result = self.translate(text, target_language, source_language)
            results.append(result)
            time.sleep(0.1)  # Rate limiting
        return results
    
    def translate(self, text: str, target_language: str, 
                 source_language: str = "auto") -> Dict:
        """Translate single text."""
        payload = {
            "text": text,
            "target_language": target_language,
            "source_language": source_language
        }
        
        if self.api_key:
            payload["api_key"] = self.api_key
            
        return self._make_request("POST", "/api/translate", json=payload)

# Usage Example
client = AdvancedTranslationClient(
    "http://YOUR_SERVER_IP:8080", 
    "your-api-key"
)

texts = ["Hello", "Goodbye", "Thank you"]
results = client.translate_batch(texts, "French")
for i, result in enumerate(results):
    if result["success"]:
        print(f"'{texts[i]}' → '{result['data']['translated_text']}'")
    else:
        print(f"Error translating '{texts[i]}': {result['error']}")
```

## 🖥️ Windows PowerShell Client

### PowerShell Script
```powershell
# Windows PowerShell Translation Client

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$Text,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetLanguage,
    
    [string]$SourceLanguage = "auto",
    [string]$ApiKey = ""
)

function Invoke-Translation {
    param($Url, $Text, $Target, $Source, $Key)
    
    $body = @{
        text = $Text
        target_language = $Target
        source_language = $Source
    }
    
    if ($Key) {
        $body.api_key = $Key
    }
    
    $jsonBody = $body | ConvertTo-Json -Depth 2
    
    try {
        $response = Invoke-RestMethod -Uri "$Url/api/translate" -Method Post -Body $jsonBody -ContentType "application/json" -TimeoutSec 30
        return $response
    }
    catch {
        Write-Error "Translation failed: $($_.Exception.Message)"
        return $null
    }
}

# Health check first
try {
    $health = Invoke-RestMethod -Uri "$ServerUrl/api/health" -Method Get -TimeoutSec 5
    Write-Host "✅ Server is healthy: $($health.status)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Server health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Perform translation
Write-Host "🔄 Translating '$Text' to $TargetLanguage..." -ForegroundColor Yellow

$result = Invoke-Translation -Url $ServerUrl -Text $Text -Target $TargetLanguage -Source $SourceLanguage -Key $ApiKey

if ($result) {
    Write-Host "✅ Translation successful!" -ForegroundColor Green
    Write-Host "Original: $($result.original_text)" -ForegroundColor White
    Write-Host "Translated: $($result.translated_text)" -ForegroundColor Cyan
    Write-Host "Language: $($result.detected_language) → $($result.target_language)" -ForegroundColor Gray
}

# Usage: .\translate.ps1 -ServerUrl "http://192.168.1.100:8080" -Text "Hello world" -TargetLanguage "Spanish" -ApiKey "your-key"
```

## 🍎 macOS Client Examples

### macOS Terminal (curl)
```bash
#!/bin/bash
# macOS/Linux Translation Script

SERVER_URL="http://YOUR_SERVER_IP:8080"
API_KEY="your-api-key"

# Function to translate text
translate() {
    local text="$1"
    local target="$2"
    local source="${3:-auto}"
    
    echo "🔄 Translating '$text' to $target..."
    
    curl -s -X POST "$SERVER_URL/api/translate" \
         -H "Content-Type: application/json" \
         -d "{
           \"text\": \"$text\",
           \"target_language\": \"$target\",
           \"source_language\": \"$source\",
           \"api_key\": \"$API_KEY\"
         }" | jq -r '.translated_text // .error'
}

# Health check
echo "Checking server health..."
health=$(curl -s "$SERVER_URL/api/health" | jq -r '.status // "error"')
if [ "$health" = "healthy" ]; then
    echo "✅ Server is healthy"
else
    echo "❌ Server is not healthy: $health"
    exit 1
fi

# Usage examples
translate "Hello, world!" "Spanish"
translate "Good morning" "French"
translate "Thank you" "German"
```

### Swift iOS/macOS App
```swift
import Foundation

class TranslationService {
    private let serverURL: String
    private let apiKey: String?
    
    init(serverURL: String, apiKey: String? = nil) {
        self.serverURL = serverURL
        self.apiKey = apiKey
    }
    
    func translate(text: String, targetLanguage: String, 
                  sourceLanguage: String = "auto",
                  completion: @escaping (Result<TranslationResponse, Error>) -> Void) {
        
        guard let url = URL(string: "\(serverURL)/api/translate") else {
            completion(.failure(TranslationError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody = TranslationRequest(
            text: text,
            targetLanguage: targetLanguage,
            sourceLanguage: sourceLanguage,
            apiKey: apiKey
        )
        
        do {
            request.httpBody = try JSONEncoder().encode(requestBody)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(TranslationError.noData))
                return
            }
            
            do {
                let translationResponse = try JSONDecoder().decode(TranslationResponse.self, from: data)
                completion(.success(translationResponse))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

struct TranslationRequest: Codable {
    let text: String
    let targetLanguage: String
    let sourceLanguage: String
    let apiKey: String?
    
    private enum CodingKeys: String, CodingKey {
        case text
        case targetLanguage = "target_language"
        case sourceLanguage = "source_language"
        case apiKey = "api_key"
    }
}

struct TranslationResponse: Codable {
    let translatedText: String
    let originalText: String
    let targetLanguage: String
    let detectedLanguage: String?
    
    private enum CodingKeys: String, CodingKey {
        case translatedText = "translated_text"
        case originalText = "original_text"
        case targetLanguage = "target_language"
        case detectedLanguage = "detected_language"
    }
}

enum TranslationError: Error {
    case invalidURL
    case noData
}

// Usage
let service = TranslationService(
    serverURL: "http://192.168.1.100:8080",
    apiKey: "your-api-key"
)

service.translate(text: "Hello", targetLanguage: "Spanish") { result in
    switch result {
    case .success(let translation):
        print("Translated: \(translation.translatedText)")
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

## 🌐 Web Browser / JavaScript Clients

### HTML + JavaScript Web Client
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Translation Client</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        input, select, textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .result { background: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .error { background: #ffe8e8; color: #d63384; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 LLM Translation Service</h1>
        
        <div>
            <label>Server URL:</label>
            <input type="text" id="serverUrl" value="http://192.168.1.100:8080" placeholder="http://your-server:8080">
        </div>
        
        <div>
            <label>API Key (optional):</label>
            <input type="password" id="apiKey" placeholder="your-api-key">
        </div>
        
        <div>
            <label>Text to Translate:</label>
            <textarea id="textInput" rows="4" placeholder="Enter text to translate...">Hello, how are you today?</textarea>
        </div>
        
        <div>
            <label>Target Language:</label>
            <select id="targetLanguage">
                <option value="Spanish">Spanish</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Italian">Italian</option>
                <option value="Portuguese">Portuguese</option>
                <option value="Chinese">Chinese</option>
                <option value="Japanese">Japanese</option>
                <option value="Korean">Korean</option>
                <option value="Russian">Russian</option>
                <option value="Arabic">Arabic</option>
            </select>
        </div>
        
        <button onclick="checkHealth()">🔍 Check Server Health</button>
        <button onclick="translateText()">🔄 Translate</button>
        
        <div id="result"></div>
    </div>

    <script>
        async function checkHealth() {
            const serverUrl = document.getElementById('serverUrl').value;
            const resultDiv = document.getElementById('result');
            
            try {
                const response = await fetch(`${serverUrl}/api/health`);
                const data = await response.json();
                
                if (data.status === 'healthy') {
                    resultDiv.innerHTML = '<div class="result">✅ Server is healthy and ready!</div>';
                } else {
                    resultDiv.innerHTML = '<div class="result error">⚠️ Server reported: ' + data.status + '</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<div class="result error">❌ Cannot connect to server: ' + error.message + '</div>';
            }
        }
        
        async function translateText() {
            const serverUrl = document.getElementById('serverUrl').value;
            const apiKey = document.getElementById('apiKey').value;
            const text = document.getElementById('textInput').value;
            const targetLanguage = document.getElementById('targetLanguage').value;
            const resultDiv = document.getElementById('result');
            
            if (!text.trim()) {
                resultDiv.innerHTML = '<div class="result error">Please enter text to translate</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="result">🔄 Translating...</div>';
            
            const requestBody = {
                text: text,
                target_language: targetLanguage,
                source_language: "auto"
            };
            
            if (apiKey) {
                requestBody.api_key = apiKey;
            }
            
            try {
                const response = await fetch(`${serverUrl}/api/translate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });
                
                const data = await response.json();
                
                if (response.ok && data.translated_text) {
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>✅ Translation Successful!</h3>
                            <p><strong>Original:</strong> ${data.original_text}</p>
                            <p><strong>Translated:</strong> ${data.translated_text}</p>
                            <p><strong>Language:</strong> ${data.detected_language || 'auto'} → ${data.target_language}</p>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = '<div class="result error">❌ Translation failed: ' + (data.error || 'Unknown error') + '</div>';
                }
            } catch (error) {
                resultDiv.innerHTML = '<div class="result error">❌ Network error: ' + error.message + '</div>';
            }
        }
        
        // Check health on page load
        window.onload = function() {
            checkHealth();
        };
    </script>
</body>
</html>
```

### Node.js Client
```javascript
// Node.js Translation Client
const axios = require('axios');

class TranslationClient {
    constructor(serverUrl, apiKey = null) {
        this.serverUrl = serverUrl.replace(/\/$/, ''); // Remove trailing slash
        this.apiKey = apiKey;
        this.client = axios.create({
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async healthCheck() {
        try {
            const response = await this.client.get(`${this.serverUrl}/api/health`);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async translate(text, targetLanguage, sourceLanguage = 'auto') {
        const payload = {
            text,
            target_language: targetLanguage,
            source_language: sourceLanguage
        };
        
        if (this.apiKey) {
            payload.api_key = this.apiKey;
        }
        
        try {
            const response = await this.client.post(`${this.serverUrl}/api/translate`, payload);
            return { success: true, data: response.data };
        } catch (error) {
            return { 
                success: false, 
                error: error.response?.data?.error || error.message 
            };
        }
    }
    
    async translateBatch(texts, targetLanguage, sourceLanguage = 'auto') {
        const results = [];
        for (const text of texts) {
            const result = await this.translate(text, targetLanguage, sourceLanguage);
            results.push(result);
            // Add small delay to respect rate limits
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        return results;
    }
}

// Usage Example
async function main() {
    const client = new TranslationClient('http://192.168.1.100:8080', 'your-api-key');
    
    // Health check
    console.log('Checking server health...');
    const health = await client.healthCheck();
    if (health.success) {
        console.log('✅ Server is healthy:', health.data.status);
    } else {
        console.log('❌ Health check failed:', health.error);
        return;
    }
    
    // Single translation
    console.log('\nTranslating single text...');
    const result = await client.translate('Hello, world!', 'Spanish');
    if (result.success) {
        console.log('✅ Translation:', result.data.translated_text);
    } else {
        console.log('❌ Translation failed:', result.error);
    }
    
    // Batch translation
    console.log('\nTranslating multiple texts...');
    const texts = ['Hello', 'Goodbye', 'Thank you', 'Please', 'Excuse me'];
    const batchResults = await client.translateBatch(texts, 'French');
    
    batchResults.forEach((result, index) => {
        if (result.success) {
            console.log(`✅ "${texts[index]}" → "${result.data.translated_text}"`);
        } else {
            console.log(`❌ "${texts[index]}" failed: ${result.error}`);
        }
    });
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = TranslationClient;
```

## 📱 Mobile App Examples

### React Native Client
```javascript
// React Native Translation Component
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, Alert, ScrollView } from 'react-native';

const TranslationScreen = () => {
    const [serverUrl, setServerUrl] = useState('http://192.168.1.100:8080');
    const [apiKey, setApiKey] = useState('');
    const [inputText, setInputText] = useState('');
    const [targetLanguage, setTargetLanguage] = useState('Spanish');
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [serverHealth, setServerHealth] = useState(null);
    
    useEffect(() => {
        checkServerHealth();
    }, [serverUrl]);
    
    const checkServerHealth = async () => {
        try {
            const response = await fetch(`${serverUrl}/api/health`);
            const data = await response.json();
            setServerHealth(data.status === 'healthy');
        } catch (error) {
            setServerHealth(false);
        }
    };
    
    const translateText = async () => {
        if (!inputText.trim()) {
            Alert.alert('Error', 'Please enter text to translate');
            return;
        }
        
        setIsLoading(true);
        setResult(null);
        
        const requestBody = {
            text: inputText,
            target_language: targetLanguage,
            source_language: 'auto'
        };
        
        if (apiKey) {
            requestBody.api_key = apiKey;
        }
        
        try {
            const response = await fetch(`${serverUrl}/api/translate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (response.ok && data.translated_text) {
                setResult(data);
            } else {
                Alert.alert('Translation Error', data.error || 'Unknown error');
            }
        } catch (error) {
            Alert.alert('Network Error', error.message);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <ScrollView style={{ flex: 1, padding: 20 }}>
            <Text style={{ fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 }}>
                🌐 Translation Service
            </Text>
            
            {/* Server Status */}
            <View style={{ padding: 10, backgroundColor: serverHealth ? '#e8f5e8' : '#ffe8e8', borderRadius: 5, marginBottom: 15 }}>
                <Text style={{ textAlign: 'center', color: serverHealth ? '#155724' : '#721c24' }}>
                    {serverHealth ? '✅ Server Online' : '❌ Server Offline'}
                </Text>
            </View>
            
            {/* Server URL */}
            <Text>Server URL:</Text>
            <TextInput
                style={{ borderWidth: 1, borderColor: '#ddd', padding: 10, marginBottom: 15, borderRadius: 5 }}
                value={serverUrl}
                onChangeText={setServerUrl}
                placeholder="http://your-server:8080"
            />
            
            {/* API Key */}
            <Text>API Key (optional):</Text>
            <TextInput
                style={{ borderWidth: 1, borderColor: '#ddd', padding: 10, marginBottom: 15, borderRadius: 5 }}
                value={apiKey}
                onChangeText={setApiKey}
                placeholder="your-api-key"
                secureTextEntry
            />
            
            {/* Input Text */}
            <Text>Text to Translate:</Text>
            <TextInput
                style={{ borderWidth: 1, borderColor: '#ddd', padding: 10, marginBottom: 15, borderRadius: 5, height: 100 }}
                value={inputText}
                onChangeText={setInputText}
                placeholder="Enter text to translate..."
                multiline
            />
            
            {/* Target Language */}
            <Text>Target Language: {targetLanguage}</Text>
            <View style={{ marginBottom: 15 }}>
                {/* Add language picker component here */}
            </View>
            
            {/* Buttons */}
            <Button 
                title={isLoading ? "Translating..." : "🔄 Translate"}
                onPress={translateText}
                disabled={isLoading || !serverHealth}
            />
            
            <View style={{ marginTop: 10 }}>
                <Button title="🔍 Check Server" onPress={checkServerHealth} />
            </View>
            
            {/* Results */}
            {result && (
                <View style={{ marginTop: 20, padding: 15, backgroundColor: '#e8f5e8', borderRadius: 5 }}>
                    <Text style={{ fontWeight: 'bold', marginBottom: 10 }}>✅ Translation Result:</Text>
                    <Text style={{ marginBottom: 5 }}>
                        <Text style={{ fontWeight: 'bold' }}>Original: </Text>
                        {result.original_text}
                    </Text>
                    <Text style={{ marginBottom: 5 }}>
                        <Text style={{ fontWeight: 'bold' }}>Translated: </Text>
                        {result.translated_text}
                    </Text>
                    <Text>
                        <Text style={{ fontWeight: 'bold' }}>Language: </Text>
                        {result.detected_language || 'auto'} → {result.target_language}
                    </Text>
                </View>
            )}
        </ScrollView>
    );
};

export default TranslationScreen;
```

## 🔧 Testing Your Server

### Quick Test Script (Multi-Platform)
```bash
#!/bin/bash
# Universal test script for any platform with curl

SERVER="http://YOUR_SERVER_IP:8080"
API_KEY="your-api-key"

echo "🧪 Testing LLM Translation Server: $SERVER"
echo "=========================================="

# Test 1: Health Check
echo "1. Health Check..."
HEALTH=$(curl -s "$SERVER/api/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH" = "healthy" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH"
    exit 1
fi

# Test 2: Simple Translation
echo "2. Simple Translation..."
RESULT=$(curl -s -X POST "$SERVER/api/translate" \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"Hello\",\"target_language\":\"Spanish\",\"api_key\":\"$API_KEY\"}")

if echo "$RESULT" | grep -q "translated_text"; then
    TRANSLATED=$(echo "$RESULT" | grep -o '"translated_text":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Translation successful: Hello → $TRANSLATED"
else
    echo "❌ Translation failed: $RESULT"
fi

# Test 3: Load Test (10 requests)
echo "3. Load Test (10 requests)..."
SUCCESS=0
for i in {1..10}; do
    RESPONSE=$(curl -s -w "%{http_code}" -X POST "$SERVER/api/translate" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"Test $i\",\"target_language\":\"French\",\"api_key\":\"$API_KEY\"}")
    
    HTTP_CODE="${RESPONSE: -3}"
    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESS++))
    fi
    sleep 0.1
done

echo "✅ Load test: $SUCCESS/10 requests successful"

# Test 4: Rate Limiting
echo "4. Rate Limiting Test..."
echo "Sending 35 rapid requests to test rate limiting..."
RATE_LIMITED=0
for i in {1..35}; do
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null -X POST "$SERVER/api/translate" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"Rate test\",\"target_language\":\"German\",\"api_key\":\"$API_KEY\"}")
    
    if [ "$HTTP_CODE" = "429" ]; then
        ((RATE_LIMITED++))
    fi
done

if [ $RATE_LIMITED -gt 0 ]; then
    echo "✅ Rate limiting working: $RATE_LIMITED requests blocked"
else
    echo "⚠️ Rate limiting might not be configured"
fi

echo ""
echo "🎉 Server testing complete!"
echo "Your translation server is ready for production use!"
```

---

## 📞 Support & Troubleshooting

### Common Client Issues:

1. **Connection Refused**: Server not running or firewall blocking
2. **Timeout**: Server overloaded or network issues  
3. **401/403 Errors**: API key issues or access restrictions
4. **429 Errors**: Rate limiting triggered (normal behavior)
5. **500 Errors**: Server-side issues, check server logs

### Getting Help:
- Check server logs: `logs/production.log`
- Test health endpoint: `/api/health`
- View API documentation: `/docs`
- Verify network connectivity

**🌟 Your Windows PC is now a powerful translation server accessible from any device, anywhere!**
