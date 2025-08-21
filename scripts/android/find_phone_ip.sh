#!/bin/bash
# Quick test for Android streaming TTS with phone IP

echo "🔧 Testing Android Streaming TTS with Phone IP Configuration"
echo "============================================================"

# Example IPs to test (replace with your actual phone IP)
POSSIBLE_IPS=(
    "192.168.1.100"
    "192.168.0.100" 
    "10.0.0.100"
    "172.16.0.100"
)

echo "💡 Common phone IP addresses to try:"
for ip in "${POSSIBLE_IPS[@]}"; do
    echo "   $ip"
done

echo ""
echo "🔍 To find your phone's actual IP:"
echo "   On your Android in Termux, run: hostname -I"
echo "   Or: ip route get 8.8.8.8 | head -1 | awk '{print \$7}'"
echo ""

echo "🚀 Once you have the IP, run this to test streaming TTS:"
echo "   export OLLAMA_HOST=http://YOUR_PHONE_IP:11434"
echo "   python test_android_streaming_flow.py"
echo ""

echo "📱 Make sure on your phone in Termux:"
echo "   1. Ollama is running: ollama serve"
echo "   2. Model is loaded: ollama run gemma2:2b"
echo "   3. Accessible from network (not just localhost)"
