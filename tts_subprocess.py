#!/usr/bin/env python3
"""
TTS Subprocess Script for Dual Environment Setup
Runs in Python 3.12 environment with Coqui TTS dependencies.
Called by main service running in Python 3.13 environment.
"""

import sys
import json
import logging
import traceback
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_request(request_file_path: str) -> dict:
    """Load request data from JSON file."""
    try:
        with open(request_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load request file: {e}")
        raise

def synthesize_with_coqui(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using Coqui TTS."""
    try:
        # Import TTS here to avoid import errors in main environment
        from TTS.api import TTS
        import torch
        
        logger.info(f"Starting TTS synthesis: {len(text)} characters")
        logger.info(f"Language: {language}, Voice: {voice}, Speed: {speed}")
        
        # Initialize TTS model based on language
        if language.startswith('zh') or language == 'cn':
            # Chinese TTS
            model_name = "tts_models/zh-CN/baker/tacotron2-DDC-GST"
        elif language == 'es':
            # Spanish TTS
            model_name = "tts_models/es/mai/tacotron2-DDC"
        elif language == 'fr':
            # French TTS
            model_name = "tts_models/fr/mai/tacotron2-DDC"
        elif language == 'de':
            # German TTS
            model_name = "tts_models/de/thorsten/tacotron2-DDC"
        else:
            # Default to English
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Initialize TTS model
        tts = TTS(model_name=model_name).to(device)
        
        # Generate speech
        logger.info("Generating speech...")
        tts.tts_to_file(text=text, file_path=output_path)
        
        logger.info(f"✅ Speech synthesis completed: {output_path}")
        
    except ImportError as e:
        logger.error("Coqui TTS not installed. Falling back to simple TTS.")
        raise Exception(f"TTS libraries not available: {e}")
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def synthesize_with_edge_tts(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using Edge TTS as fallback."""
    try:
        import edge_tts
        import asyncio
        
        logger.info("Using Edge TTS fallback")
        
        # Map language codes to Edge TTS voices
        voice_map = {
            'en': 'en-US-AriaNeural',
            'es': 'es-ES-ElviraNeural', 
            'fr': 'fr-FR-DeniseNeural',
            'de': 'de-DE-KatjaNeural',
            'zh': 'zh-CN-XiaoxiaoNeural',
            'cn': 'zh-CN-XiaoxiaoNeural'
        }
        
        voice_name = voice_map.get(language, 'en-US-AriaNeural')
        
        async def async_tts():
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(output_path)
        
        # Run async function
        asyncio.run(async_tts())
        
        logger.info(f"✅ Edge TTS synthesis completed: {output_path}")
        
    except ImportError as e:
        logger.error("Edge TTS not installed either.")
        raise Exception(f"No TTS libraries available: {e}")
    except Exception as e:
        logger.error(f"Edge TTS synthesis failed: {e}")
        raise

def synthesize_with_system_tts(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using system TTS (Windows SAPI) as final fallback."""
    try:
        import pyttsx3
        
        logger.info("Using system TTS fallback")
        
        # Initialize pyttsx3
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', int(200 * speed))  # Speed
        
        # Get voices and set language-appropriate voice
        voices = engine.getProperty('voices')
        if voices:
            for voice_obj in voices:
                if language in voice_obj.id.lower() or 'english' in voice_obj.id.lower():
                    engine.setProperty('voice', voice_obj.id)
                    break
        
        # Save to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        logger.info(f"✅ System TTS synthesis completed: {output_path}")
        
    except ImportError as e:
        logger.error("pyttsx3 not installed.")
        raise Exception(f"System TTS not available: {e}")
    except Exception as e:
        logger.error(f"System TTS synthesis failed: {e}")
        raise

def main():
    """Main function for TTS subprocess."""
    if len(sys.argv) != 3:
        logger.error("Usage: python tts_subprocess.py <request_file> <output_file>")
        sys.exit(1)
    
    request_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    
    try:
        # Load request
        request_data = load_request(request_file_path)
        
        action = request_data.get('action', 'synthesize')
        text = request_data.get('text', '')
        language = request_data.get('language', 'en')
        voice = request_data.get('voice', 'default')
        speed = request_data.get('speed', 1.0)
        
        if not text:
            raise ValueError("No text provided for synthesis")
        
        logger.info(f"Processing TTS request: action={action}, lang={language}")
        
        # Try TTS methods in order of preference
        synthesis_methods = [
            ("Coqui TTS", synthesize_with_coqui),
            ("Edge TTS", synthesize_with_edge_tts),
            ("System TTS", synthesize_with_system_tts)
        ]
        
        last_error = None
        for method_name, method_func in synthesis_methods:
            try:
                logger.info(f"Attempting {method_name}...")
                method_func(text, language, voice, speed, output_file_path)
                logger.info(f"✅ Successfully used {method_name}")
                break
            except Exception as e:
                logger.warning(f"❌ {method_name} failed: {e}")
                last_error = e
                continue
        else:
            # All methods failed
            raise Exception(f"All TTS methods failed. Last error: {last_error}")
        
        # Verify output file was created
        if not Path(output_file_path).exists():
            raise Exception("Output audio file was not created")
        
        logger.info("🎉 TTS subprocess completed successfully")
        
    except Exception as e:
        logger.error(f"TTS subprocess failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
