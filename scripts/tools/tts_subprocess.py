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
import re
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_text_for_tts(text: str) -> str:
    """Clean text by removing emojis, special characters, and formatting for better TTS."""
    if not text:
        return ""
    
    # Remove emojis (Unicode emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+", 
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove special markdown and formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # `code` -> code
    text = re.sub(r'~~(.*?)~~', r'\1', text)      # ~~strike~~ -> strike
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove excessive punctuation (keep single instances)
    text = re.sub(r'[!]{2,}', '!', text)  # Multiple ! -> single !
    text = re.sub(r'[?]{2,}', '?', text)  # Multiple ? -> single ?
    text = re.sub(r'[.]{3,}', '...', text)  # Multiple . -> ellipsis
    
    # Remove special symbols but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\'-]', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    logger.info(f"Text cleaned for TTS: '{text[:100]}...' ({len(text)} chars)")
    return text

def load_request(request_file_path: str) -> dict:
    """Load request data from JSON file."""
    try:
        with open(request_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load request file: {e}")
        raise

def synthesize_with_coqui(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using Coqui TTS with British accent for English."""
    try:
        # Import TTS here to avoid import errors in main environment
        from TTS.api import TTS
        import torch
        
        # Clean text for better TTS output
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            raise ValueError("No valid text remaining after cleaning")
        
        logger.info(f"Starting TTS synthesis: {len(clean_text)} characters")
        logger.info(f"Language: {language}, Voice: {voice}, Speed: {speed}")
        
        # Initialize TTS model based on language with British accent preference
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
            # For English, try to use a multi-speaker model if available
            # Note: LJSpeech is American, so we'll use it but Edge TTS is preferred for British
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            logger.info("Using American English model - Edge TTS preferred for British accent")
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Initialize TTS model
        tts = TTS(model_name=model_name).to(device)
        
        # Generate speech with cleaned text
        logger.info("Generating speech...")
        tts.tts_to_file(text=clean_text, file_path=output_path)
        
        logger.info(f"✅ Speech synthesis completed: {output_path}")
        
    except ImportError as e:
        logger.error("Coqui TTS not installed. Falling back to simple TTS.")
        raise Exception(f"TTS libraries not available: {e}")
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def synthesize_with_edge_tts(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using Edge TTS as fallback with British accent for English."""
    try:
        import edge_tts
        import asyncio
        
        # Clean text for better TTS output
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            raise ValueError("No valid text remaining after cleaning")
        
        logger.info("Using Edge TTS fallback")
        
        # Map language codes to Edge TTS voices with British accent for English
        voice_map = {
            'en': 'en-GB-LibbyNeural',      # British English female - natural sounding
            'en-gb': 'en-GB-LibbyNeural',   # British English female
            'en-uk': 'en-GB-RyanNeural',    # British English male
            'en-us': 'en-US-AriaNeural',    # American English if specifically requested
            'es': 'es-ES-ElviraNeural', 
            'fr': 'fr-FR-DeniseNeural',
            'de': 'de-DE-KatjaNeural',
            'zh': 'zh-CN-XiaoxiaoNeural',
            'cn': 'zh-CN-XiaoxiaoNeural'
        }
        
        # For British accent preference, use LibbyNeural (female) or RyanNeural (male)
        if voice == 'british' or voice == 'male':
            voice_name = 'en-GB-RyanNeural'  # British male
        else:
            voice_name = voice_map.get(language, 'en-GB-LibbyNeural')  # British female default
        
        logger.info(f"Using Edge TTS voice: {voice_name} for British accent")
        
        # Add SSML for speed control if needed
        if speed != 1.0:
            speed_percent = f"{int(speed * 100)}%"
            ssml_text = f'<speak><prosody rate="{speed_percent}">{clean_text}</prosody></speak>'
        else:
            ssml_text = clean_text
        
        async def async_tts():
            communicate = edge_tts.Communicate(ssml_text, voice_name)
            await communicate.save(output_path)
        
        # Run async function
        asyncio.run(async_tts())
        
        logger.info(f"✅ Edge TTS synthesis completed with British accent: {output_path}")
        
    except ImportError as e:
        logger.error("Edge TTS not installed either.")
        raise Exception(f"No TTS libraries available: {e}")
    except Exception as e:
        logger.error(f"Edge TTS synthesis failed: {e}")
        raise

def synthesize_with_system_tts(text: str, language: str, voice: str, speed: float, output_path: str):
    """Synthesize speech using system TTS (Windows SAPI) as final fallback with British preference."""
    try:
        import pyttsx3
        
        # Clean text for better TTS output
        clean_text = clean_text_for_tts(text)
        if not clean_text:
            raise ValueError("No valid text remaining after cleaning")
        
        logger.info("Using system TTS fallback")
        
        # Initialize pyttsx3
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', int(200 * speed))  # Speed
        
        # Get voices and prefer British/UK voices for English
        voices = engine.getProperty('voices')
        if voices:
            british_voice = None
            english_voice = None
            
            for voice_obj in voices:
                voice_id_lower = voice_obj.id.lower()
                voice_name_lower = getattr(voice_obj, 'name', '').lower()
                
                # Prefer British/UK voices
                if any(uk_term in voice_id_lower or uk_term in voice_name_lower 
                      for uk_term in ['uk', 'british', 'britain', 'gb']):
                    british_voice = voice_obj.id
                    break
                # Fallback to any English voice
                elif any(en_term in voice_id_lower or en_term in voice_name_lower 
                        for en_term in ['english', 'en-', 'en_']):
                    english_voice = voice_obj.id
            
            # Set voice preference: British > English > Default
            if british_voice:
                engine.setProperty('voice', british_voice)
                logger.info("Using British voice for system TTS")
            elif english_voice:
                engine.setProperty('voice', english_voice)
                logger.info("Using English voice for system TTS")
        
        # Save to file with cleaned text
        engine.save_to_file(clean_text, output_path)
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
        logger.info(f"Original text length: {len(text)} characters")
        
        # Log a preview of text cleaning (for debugging)
        cleaned_preview = clean_text_for_tts(text)
        if len(cleaned_preview) != len(text):
            logger.info(f"Text cleaned: {len(text)} -> {len(cleaned_preview)} characters")
            logger.info(f"Cleaned preview: '{cleaned_preview[:100]}...'")
        
        # Try TTS methods in order of preference for British accent
        if language == 'en' or language.startswith('en'):
            # For English, prioritize Edge TTS for better British accent support
            synthesis_methods = [
                ("Edge TTS (British)", synthesize_with_edge_tts),
                ("Coqui TTS", synthesize_with_coqui),
                ("System TTS (British)", synthesize_with_system_tts)
            ]
        else:
            # For other languages, keep Coqui TTS first
            synthesis_methods = [
                ("Coqui TTS", synthesize_with_coqui),
                ("Edge TTS (British)", synthesize_with_edge_tts),
                ("System TTS (British)", synthesize_with_system_tts)
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
        
        logger.info("🎉 TTS subprocess completed successfully with British accent")
        
    except Exception as e:
        logger.error(f"TTS subprocess failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
