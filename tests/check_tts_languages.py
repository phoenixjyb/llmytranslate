#!/usr/bin/env python3
"""
Quick test to show TTS language support
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.services.tts_service import tts_service

def show_language_support():
    """Show supported TTS languages."""
    print("🎤 TTS Language Support Configuration:")
    print("=" * 50)
    
    for lang_code, config in tts_service.model_configs.items():
        print(f"📍 {lang_code.upper()}: {config['description']}")
        print(f"   Model: {config['model_name']}")
        print()
    
    print("💡 Usage Examples:")
    print("English: POST /api/tts/synthesize -F 'text=Hello world' -F 'language=en'")
    print("Chinese: POST /api/tts/synthesize -F 'text=你好世界' -F 'language=zh'")
    print("Auto:    POST /api/tts/synthesize -F 'text=Hello 你好' -F 'language=multilingual'")

if __name__ == "__main__":
    show_language_support()
