#!/usr/bin/env python3
"""
TTS Subprocess Handler for Python 3.12 Environment
Handles TTS operations in a separate Python 3.12 environment
"""

import sys
import json
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any

def setup_logging():
    """Setup basic logging for the subprocess."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - TTS-Subprocess - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
    logger.info("✅ Coqui TTS loaded successfully in subprocess")
except ImportError as e:
    TTS_AVAILABLE = False
    logger.error(f"❌ Failed to import TTS: {e}")
    sys.exit(1)

class TTSSubprocessHandler:
    """Handles TTS operations in the Python 3.12 subprocess."""
    
    def __init__(self):
        self.models = {}
        self.supported_models = {
            "en": {
                "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
                "description": "English TTS - LJSpeech Tacotron2"
            },
            "zh": {
                "model_name": "tts_models/zh-CN/baker/tacotron2-DDC",
                "description": "Chinese TTS - Baker Tacotron2"
            },
            "multilingual": {
                "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
                "description": "Multilingual XTTS v2"
            }
        }
    
    def load_model(self, language: str) -> bool:
        """Load TTS model for specified language."""
        try:
            if language in self.models:
                return True
            
            model_config = self.supported_models.get(language)
            if not model_config:
                logger.warning(f"No model configuration for language: {language}")
                return False
            
            logger.info(f"🔄 Loading TTS model: {model_config['model_name']}")
            self.models[language] = TTS(model_name=model_config['model_name'])
            logger.info(f"✅ Model loaded for {language}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load model for {language}: {e}")
            return False
    
    def synthesize_speech(self, request_data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """Synthesize speech and save to output path."""
        try:
            text = request_data.get("text", "")
            language = request_data.get("language", "en")
            voice = request_data.get("voice", "default")
            speed = request_data.get("speed", 1.0)
            
            # Map language codes
            if language.lower().startswith("zh"):
                lang_key = "zh"
            elif language.lower().startswith("en"):
                lang_key = "en"
            else:
                lang_key = "en"  # Default to English
            
            # Load model if needed
            if not self.load_model(lang_key):
                return {
                    "success": False,
                    "error": f"Failed to load model for language: {language}"
                }
            
            model = self.models[lang_key]
            
            # Generate speech
            logger.info(f"🎤 Synthesizing: {text[:50]}...")
            model.tts_to_file(
                text=text,
                file_path=output_path,
                speed=speed
            )
            
            # Verify output file was created
            if not Path(output_path).exists():
                return {
                    "success": False,
                    "error": "Audio file was not generated"
                }
            
            file_size = Path(output_path).stat().st_size
            logger.info(f"✅ Speech generated: {file_size} bytes")
            
            return {
                "success": True,
                "output_path": output_path,
                "file_size": file_size,
                "language": language,
                "model_used": lang_key
            }
            
        except Exception as e:
            logger.error(f"❌ Speech synthesis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def list_models(self) -> Dict[str, Any]:
        """List available models and their status."""
        try:
            models_info = {}
            
            for lang, config in self.supported_models.items():
                models_info[lang] = {
                    "model_name": config["model_name"],
                    "description": config["description"],
                    "loaded": lang in self.models,
                    "available": True  # Assume available since TTS imported successfully
                }
            
            return {
                "available": True,
                "languages": models_info,
                "total_languages": len(models_info),
                "loaded_models": list(self.models.keys()),
                "python_version": sys.version
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to list models: {e}")
            return {
                "available": False,
                "error": str(e),
                "python_version": sys.version
            }

def main():
    """Main function to handle subprocess communication."""
    if len(sys.argv) != 3:
        logger.error("Usage: tts_subprocess.py <request_file> <output_file>")
        sys.exit(1)
    
    request_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # Read request data with proper UTF-8 handling
        with open(request_file, 'r', encoding='utf-8-sig') as f:
            request_data = json.load(f)
        
        action = request_data.get("action", "")
        logger.info(f"🔄 Processing action: {action}")
        
        handler = TTSSubprocessHandler()
        
        if action == "synthesize":
            result = handler.synthesize_speech(request_data, output_file)
            if not result["success"]:
                logger.error(f"Synthesis failed: {result.get('error')}")
                sys.exit(1)
        
        elif action == "list_models":
            result = handler.list_models()
            # For list_models, we output JSON to stdout instead of file
            print(json.dumps(result, indent=2))
            sys.exit(0)
        
        else:
            logger.error(f"Unknown action: {action}")
            sys.exit(1)
        
        logger.info("✅ TTS subprocess completed successfully")
        
    except Exception as e:
        logger.error(f"❌ TTS subprocess failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
