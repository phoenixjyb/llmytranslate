#!/usr/bin/env python3
"""
Test configuration loading to debug the issue.
"""

import os
import sys
sys.path.append('src')

try:
    from src.core.config import get_settings
    print("Attempting to load settings...")
    settings = get_settings()
    print("✅ Settings loaded successfully!")
    print(f"API Host: {settings.api.host}")
    print(f"API Port: {settings.api.port}")
    print(f"Ollama Host: {settings.ollama.ollama_host}")
    print(f"Model Name: {settings.ollama.model_name}")
except Exception as e:
    print(f"❌ Error loading settings: {e}")
    import traceback
    traceback.print_exc()
