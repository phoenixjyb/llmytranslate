# 🚇 Quick Ngrok Setup Guide (Windows Store Version)

## Prerequisites
✅ You already have ngrok 3.24 installed via Windows Store

## Step 1: Get Auth Token
1. Go to: https://dashboard.ngrok.com/signup
2. Sign up (free account)
3. Get auth token from: https://dashboard.ngrok.com/get-started/your-authtoken

## Step 2: Configure Ngrok
```powershell
# Replace YOUR_AUTH_TOKEN with your actual token
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

## Step 3: Start Tunnel
```powershell
# Start ngrok tunnel
ngrok http 8000
```

## Step 4: Test Your Service
```bash
# Replace ngrok-url with the URL from ngrok output
curl https://your-ngrok-url.ngrok.io/api/health
curl -X POST "https://your-ngrok-url.ngrok.io/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"
```

## Alternative: Use the Automated Script
```powershell
.\scripts\setup_ngrok.ps1 YOUR_AUTH_TOKEN
```

Your translation service will be accessible worldwide via the ngrok URL!
