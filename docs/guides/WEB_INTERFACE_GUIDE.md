# Web Interface Guide

The LLM Translation Service includes a modern, responsive web interface for easy translation with auto-detection and real-time results.

## 🌐 Accessing the Web Interface

### Local Access
When running the service locally, access the web interface at:
```
http://localhost:8000/web/
```

### Remote Access

#### Via VS Code Port Forwarding (Recommended for SSH)
1. Open VS Code with remote SSH connection
2. Open the "Ports" tab (usually next to Terminal)
3. Click the "+" button to forward a port
4. Enter `8000` and press Enter
5. Click on the forwarded URL to access the web interface

#### Via ngrok Tunnel
```bash
# Start the service
.\start-service.ps1

# Start ngrok (in another terminal)
ngrok http 8000

# Access via the ngrok URL
# Example: https://abc123.ngrok-free.app/web/
```

## 🎯 Features

### Auto-Detection and Configuration
- **Server URL Detection**: Automatically detects if you're accessing via localhost, ngrok, or port forwarding
- **Language Detection**: Auto-detects source language when set to "Auto-detect"
- **Health Monitoring**: Real-time server status indicator in the header

### Translation Interface
- **Source Text Input**: Large textarea with character counter (up to 5000 characters)
- **Language Selection**: Dropdown menus for source and target languages
- **Language Swap**: Quick button to swap source and target languages
- **Auto-Detection**: Option to automatically detect source language

### Results and Interaction
- **Real-time Results**: Translation appears immediately after processing
- **Copy to Clipboard**: One-click copy button for translation results
- **Translation Metadata**: Shows detected languages, processing time, and character count
- **Error Handling**: User-friendly error messages for connection or translation issues

### Settings Panel
- **Server URL Configuration**: Manually set or auto-detect server URL
- **Auto-detect Button**: Automatically finds ngrok tunnel URLs
- **API Key Field**: Optional API key configuration (for authenticated endpoints)

## 📱 User Interface

### Layout
```
┌─────────────────────────────────────────┐
│           🌐 LLM Translation Service    │
│           ✅ Server healthy • llama3.1  │
├─────────────────────────────────────────┤
│ ⚙️ Server Settings ▼                   │
│   Server URL: http://localhost:8000     │
│   🔍 Auto-detect                       │
├─────────────────────────────────────────┤
│ Text to Translate:                      │
│ ┌─────────────────────────────────────┐ │
│ │ Hello world! How are you today?     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                              31/5000    │
├─────────────────────────────────────────┤
│ From: 🌍 Auto-detect  ⇄  To: 🇨🇳 Chinese │
├─────────────────────────────────────────┤
│ 🔄 Translate  🗑️ Clear  🏥 Check Server │
├─────────────────────────────────────────┤
│ 📝 Translation:              📋 Copy   │
│ 你好！今天怎么样？                        │
│ ─────────────────────────────────────── │
│ From: 🌍 Auto-detect  To: 🇨🇳 Chinese   │
│ Time: 2637ms  Characters: 31            │
└─────────────────────────────────────────┘
```

### Color Coding
- **Green**: Successful translations and healthy server status
- **Red**: Errors and connection failures
- **Yellow**: Warnings and loading states
- **Blue**: Interactive elements and links

## 🚀 Usage Instructions

### Basic Translation
1. **Enter Text**: Type or paste text in the source textarea
2. **Select Languages**: Choose source and target languages (or use auto-detect)
3. **Translate**: Click the "🔄 Translate" button
4. **Copy Result**: Use the "📋 Copy" button to copy the translation

### Advanced Features
- **Keyboard Shortcuts**: Press Ctrl+Enter in the textarea to translate
- **Language Swap**: Click the "⇄" button to swap source and target languages
- **Settings**: Click "⚙️ Server Settings" to configure server URL or API key
- **Health Check**: Use "🏥 Check Server" to verify connectivity

### Auto-Detection
The web interface automatically detects:
- **Server URL**: Uses current domain when accessed remotely
- **Source Language**: When "Auto-detect" is selected
- **ngrok URLs**: Can auto-detect active ngrok tunnels

## 🔧 Technical Details

### Browser Compatibility
- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Mobile Browsers**: Responsive design works on mobile devices
- **JavaScript Required**: The interface requires JavaScript to function

### Network Requirements
- **CORS**: Configured to allow cross-origin requests
- **Headers**: Automatically adds ngrok-skip-browser-warning for ngrok tunnels
- **Health Checks**: Performs connectivity tests before translation requests

### Error Handling
- **Connection Errors**: Shows user-friendly messages for network issues
- **Translation Errors**: Displays specific error messages from the API
- **Validation**: Client-side validation for empty text and invalid configurations

## 🛠️ Troubleshooting

### Common Issues

#### "Cannot connect to server"
1. Verify the service is running (`.\start-service.ps1`)
2. Check the server URL in settings
3. Test with "🏥 Check Server" button

#### "No translation result received"
1. Check browser console for detailed errors (F12)
2. Verify the text is not empty
3. Try different source/target language combinations

#### Web interface doesn't load
1. Ensure you're accessing the correct URL (`/web/` path)
2. Check if the service is running on the expected port
3. Try accessing the health endpoint directly (`/api/health`)

### Remote Access Issues
1. **Port Forwarding**: Ensure port 8000 is properly forwarded
2. **ngrok**: Check that ngrok is running and pointing to port 8000
3. **Firewall**: Verify firewall settings allow connections on port 8000

### Browser Developer Tools
Press F12 to open developer tools and check:
- **Console**: For JavaScript errors and debug information
- **Network**: To see API requests and responses
- **Application**: To check local storage and settings

## 📚 Related Documentation

- [README.md](../../README.md) - Main project documentation
- [API Usage Guide](../api/API_USAGE.md) - API endpoint documentation
- [Remote Access Guide](REMOTE_ACCESS_GUIDE.md) - Remote deployment setup
- [Project Structure](../PROJECT_STRUCTURE.md) - Codebase organization
