#!/bin/bash

# Verify Gemma 2:270M Model Update
echo "🔍 Verifying Gemma 2:270M Model Update"
echo "======================================"

echo ""
echo "📱 Android App Configuration:"
grep -n "gemma2:270m" android/app/src/main/java/com/llmytranslate/android/services/TermuxOllamaClient.kt || echo "❌ Android not updated"

echo ""
echo "🖥️  Backend Services Configuration:"
echo "  • optimized_llm_service.py:"
grep -n "gemma2:270m" src/services/optimized_llm_service.py | head -3

echo "  • streaming_tts_websocket.py:"
grep -n "gemma2:270m" src/services/streaming_tts_websocket.py || echo "❌ Not found"

echo "  • android_streaming_tts.py:"
grep -n "gemma2:270m" src/services/android_streaming_tts.py || echo "❌ Not found"

echo ""
echo "📱 Mobile-Specific Services:"
echo "  • mobile/optimized_llm_service.py:"
grep -n "gemma2:270m" mobile/src/services/optimized_llm_service.py | head -2

echo "  • mobile/android.py API:"
grep -n "gemma2:270m" mobile/src/api/routes/android.py || echo "❌ Not found"

echo ""
echo "📚 Documentation Updates:"
echo "  • README.md:"
grep -n "gemma2:270m" README.md | head -2

echo "  • Model update doc:"
ls -la GEMMA270M_MODEL_UPDATE.md 2>/dev/null || echo "❌ Documentation missing"

echo ""
echo "🔧 Utility Scripts:"
echo "  • Migration script:"
ls -la switch_to_gemma270m.sh 2>/dev/null || echo "❌ Script missing"

echo "  • Test scripts updated:"
grep -n "gemma2:270m" android_gpu_reality_check.py | head -1
grep -n "gemma2:270m" test_gpu_acceleration.py | head -1

echo ""
echo "🎯 Expected Performance Improvements:"
echo "  • Model size: 1.6GB → 270MB (85% reduction)"
echo "  • Response time: 3-8s → <1s (5x faster)" 
echo "  • Memory usage: ~2GB → ~400MB (80% reduction)"
echo "  • Storage savings: 1.33GB per installation"

echo ""
echo "✅ Verification Complete!"
echo "📋 Next Steps:"
echo "  1. Run: ./switch_to_gemma270m.sh"
echo "  2. Test: ollama run gemma2:270m 'Hello'"
echo "  3. Verify: time ollama run gemma2:270m 'Quick test'"
