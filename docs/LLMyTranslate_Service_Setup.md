# LLMyTranslate Service Setup Instructions

## 🚀 Setting Up LLMyTranslate Service for Remote Access

### 📍 **Where to Run This Setup**
Run these commands on the **machine where LLMyTranslate service will run** (not in systemDesign folder).

---

## 🔒 **Option 1: Tailscale Setup (Recommended)**

### **Step 1: Install Tailscale**
```bash
# macOS
brew install tailscale

# Linux
curl -fsSL https://tailscale.com/install.sh | sh

# Or download from: https://tailscale.com/download
```

### **Step 2: Connect to Tailscale Network**
```bash
# Start Tailscale (will open browser for authentication)
sudo tailscale up

# Get your Tailscale IP address
tailscale ip -4
# Example output: 100.64.0.1
```

### **Step 3: Start LLMyTranslate Service**
```bash
# Install and start your LLMyTranslate service
pip install llmytranslate  # or however you install it
python -m llmytranslate --port 8080 --host 0.0.0.0

# Or if you have a different start command:
# llmytranslate-server --port 8080 --bind 0.0.0.0
```

### **Step 4: Test Local Access**
```bash
# Test from the same machine
curl http://localhost:8080/api/health

# Test via Tailscale IP
curl http://100.64.0.1:8080/api/health  # Use your actual IP
```

### **Step 5: Note Your Service Details**
- **Tailscale IP**: (from `tailscale ip -4`)
- **Port**: 8080 (or your chosen port)
- **Service URL**: `http://YOUR_TAILSCALE_IP:8080`

---

## 🌍 **Option 2: ngrok Setup (Alternative)**

### **Step 1: Install ngrok**
```bash
# macOS
brew install ngrok

# Linux
snap install ngrok

# Or download from: https://ngrok.com/download
```

### **Step 2: Get Auth Token**
1. Sign up at [ngrok.com](https://ngrok.com)
2. Get your auth token from the dashboard
3. Configure it:
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### **Step 3: Start LLMyTranslate Service**
```bash
# Start your service on localhost
python -m llmytranslate --port 8080
```

### **Step 4: Create ngrok Tunnel**
```bash
# In a separate terminal, create public tunnel
ngrok http 8080

# Note the public URL from output, e.g.:
# https://abc123.ngrok.io -> http://localhost:8080
```

### **Step 5: Note Your Service Details**
- **Public URL**: (from ngrok output, e.g., `https://abc123.ngrok.io`)
- **Warning**: URL changes each time you restart ngrok

---

## 🔧 **Firewall Configuration**

If using Tailscale, ensure your firewall allows the service port:

```bash
# Linux (ufw)
sudo ufw allow 8080/tcp

# macOS (if firewall is enabled)
# System Preferences > Security & Privacy > Firewall > Firewall Options
# Add your LLMyTranslate application
```

---

## 🧪 **Verification Steps**

### **Test Service Locally**
```bash
curl http://localhost:8080/api/health
```

### **Test Service via Tailscale**
```bash
# From the same machine
curl http://YOUR_TAILSCALE_IP:8080/api/health

# From another device (with Tailscale installed)
curl http://YOUR_TAILSCALE_IP:8080/api/health
```

### **Test Translation**
```bash
# Simple translation test
curl -X POST "http://YOUR_TAILSCALE_IP:8080/api/trans/vip/translate" \
  -d "q=hello world" \
  -d "from=en" \
  -d "to=zh" \
  -d "appid=demo_app_id" \
  -d "salt=12345" \
  -d "sign=dummy_sign"
```

---

## 🎯 **What to Share with systemDesign Project**

After setup, provide these details to configure the systemDesign client:

### **For Tailscale:**
- **Service URL**: `http://YOUR_TAILSCALE_IP:8080`
- **App ID**: Your LLMyTranslate app ID
- **App Secret**: Your LLMyTranslate app secret

### **For ngrok:**
- **Service URL**: `https://abc123.ngrok.io` (your ngrok URL)
- **App ID**: Your LLMyTranslate app ID  
- **App Secret**: Your LLMyTranslate app secret

---

## 🛠️ **Troubleshooting**

### **Service Not Accessible**
1. Check if service is running: `ps aux | grep llmytranslate`
2. Check port binding: `netstat -tulpn | grep 8080`
3. Check firewall: `sudo ufw status`

### **Tailscale Issues**
1. Check connection: `tailscale status`
2. Restart if needed: `sudo tailscale down && sudo tailscale up`

### **ngrok Issues**
1. Check if tunnel is active: `curl http://localhost:4040/api/tunnels`
2. Verify auth token: `ngrok config check`

---

## ✅ **Ready for Client Configuration**

Once your LLMyTranslate service is accessible remotely, go to your systemDesign project and run:

```bash
./tools/scripts/configure_remote_service.sh
```

This will configure the systemDesign project to use your remote LLMyTranslate service!
