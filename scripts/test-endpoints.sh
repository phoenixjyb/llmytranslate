#!/bin/bash
# Quick test script for LLM Translation Service
# Usage: ./test_endpoints.sh

BASE_URL="http://localhost:8000"

echo "🚀 Testing LLM Translation Service"
echo "=================================="

echo ""
echo "1. 🔍 Health Check:"
curl -s "$BASE_URL/api/health" | jq '.' 2>/dev/null || curl -s "$BASE_URL/api/health"

echo ""
echo ""
echo "2. 📋 Service Info:"
curl -s "$BASE_URL/" | jq '.' 2>/dev/null || curl -s "$BASE_URL/"

echo ""
echo ""
echo "3. 🌍 Demo Translation (Hello world):"
curl -s -X POST "$BASE_URL/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh" | jq '.' 2>/dev/null || \
curl -s -X POST "$BASE_URL/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"

echo ""
echo ""
echo "4. 🌍 Demo Translation (How are you?):"
curl -s -X POST "$BASE_URL/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=How are you?&from=en&to=zh" | jq '.' 2>/dev/null || \
curl -s -X POST "$BASE_URL/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=How are you?&from=en&to=zh"

echo ""
echo ""
echo "✅ Test completed!"
